from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Defect, Product, Comment
from .permissions import IsProductOwnerOrDeveloperForDefect
from .serializers import DefectSerializer, ProductSerializer,CommentSerializer
from rest_framework.decorators import action
from rest_framework.decorators import action
from .state_machine import is_transition_allowed, ROLE_OWNER, ROLE_DEVELOPER  
from rest_framework.response import Response
from rest_framework import status
from django_filters import rest_framework as filters

# ====================== Defect API ======================
class DefectViewSet(viewsets.ModelViewSet):
    serializer_class = DefectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends=(filters.DjangoFilterBackend,)
    filterset_fields=['status','priority','tester_id','severity','assigned_to','title']
    search_fields=['title','description']
    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name='Product Owner').exists():
            return Defect.objects.filter(product__owner=user)
        
        elif user.groups.filter(name='Developer').exists():
            return Defect.objects.filter(product__developers=user)
        
        else:
            return Defect.objects.filter(
                Q(tester_email=user.email) | Q(tester_id=str(user.id))
            )


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        new_comment_text = request.data.get('new_comment')
        new_status = request.data.get('status')
        old_status = instance.status

        if new_status == 'duplicate':
            if request.user != instance.product.owner:
                return Response(
                    {'error': 'Only product owner can mark a defect as duplicate.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if old_status != 'new':
                return Response(
                    {'error': 'Only defects with status "new" can be marked as duplicate.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            target_id = request.data.get('target_defect_id')
            if not target_id:
                return Response(
                    {'error': 'target_defect_id is required when status is "duplicate".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                target_defect = Defect.objects.get(id=target_id)
            except Defect.DoesNotExist:
                return Response(
                    {'error': f'Defect with id {target_id} does not exist.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if target_defect.product != instance.product:
                return Response(
                    {'error': 'Target defect must belong to the same product.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            source_emails = set(e.strip() for e in instance.tester_email.split(',') if e.strip())
            target_emails = set(e.strip() for e in target_defect.tester_email.split(',') if e.strip())
            merged_emails = target_emails.union(source_emails)
            target_defect.tester_email = ', '.join(merged_emails)
            target_defect.save()

            instance.duplicate_of = target_defect
            instance.status = 'duplicate'
            instance.save()

            if new_comment_text:
                Comment.objects.create(
                    defect=instance,
                    author=request.user,
                    text=new_comment_text
                )

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if new_status is not None and new_status != old_status:
            user = request.user
            role = self.get_user_role_for_defect(user, instance)
            if not role:
                return Response(
                    {'error': 'You are not authorized to change the status of this defect.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not is_transition_allowed(old_status, new_status, role):
                return Response(
                    {'error': f'Transition from {old_status} to {new_status} is not allowed for {role}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if new_comment_text:
            user = request.user
            role = self.get_user_role_for_defect(user, instance)
            if not role:
                return Response(
                    {'error': 'Only product owner or developer can add comments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        response = super().update(request, *args, **kwargs)

        instance.refresh_from_db()

        if new_status == 'assigned' and old_status != 'assigned':
            user = request.user
            role = self.get_user_role_for_defect(user, instance)
            if role == 'developer':  
                instance.refresh_from_db()
                instance.assigned_to = user
                instance.save(update_fields=['assigned_to'])
                response.data = self.get_serializer(instance).data

        if new_comment_text:
            Comment.objects.create(
                defect=instance,
                author=request.user,
                text=new_comment_text
            )
            instance.refresh_from_db()
            serializer = self.get_serializer(instance)
            response.data = serializer.data

        return response
    
        


    @action(detail=True, methods=['get'], url_path='candidate-targets')
    def candidate_targets(self, request, pk=None):
        defect = self.get_object()
        candidates = Defect.objects.filter(product=defect.product).exclude(status='new').values('id', 'title')
        return Response(candidates)


    @action(detail=True, methods=['get'], url_path='allowed-statuses')
    def allowed_statuses(self, request, pk=None):
        defect = self.get_object()
        user = request.user
        if user == defect.product.owner:
            role = ROLE_OWNER
        elif user in defect.product.developers.all():
            role = ROLE_DEVELOPER
        else:
            role = None
        if not role:
            return Response({'allowed_statuses': []})  
        allowed = get_allowed_transitions(defect.status, role)
        status_choices = dict(Defect.STATUS_CHOICES)
        allowed_with_labels = [{'value': s, 'label': status_choices.get(s, s)} for s in allowed]
        return Response({'allowed_statuses': allowed_with_labels})


        
    def perform_create(self, serializer):
        tester_id_value = str(self.request.user.id)
        serializer.save(tester_id=tester_id_value, tester_email=self.request.user.email)
        product = serializer.validated_data.get('product')
        if product:
            version = product.version
        else:
            version = ''  
        serializer.save(
            tester_id=str(self.request.user.id),
            tester_email=self.request.user.email,
            status='new',
            severity=None,
            priority=None,
            version=version   
        )

    @staticmethod
    def get_user_role_for_defect(user, defect):
        if user == defect.product.owner:
            return 'owner'
        elif user in defect.product.developers.all():
            return 'developer'
        return None
    
    def perform_create(self, serializer):
        serializer.save(
            tester_id=str(self.request.user.id),  
            status='new',
            severity="low",  
            priority="low"
        )

    def create(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Tester').exists():
            return Response(
                {'error': 'Only testers can submit defect reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    

    


# ====================== Product API ======================
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Product Owner').exists():
            return Product.objects.filter(owner=user)
        return Product.objects.none()

    def perform_create(self, serializer):
        product = serializer.save(owner=self.request.user)
        developers_ids = self.request.data.get('developers', [])
        if developers_ids:
            product.developers.set(developers_ids)
    
    def perform_update(self, serializer):
        product = serializer.save()
        developers_ids = self.request.data.get('developers', None)
        if developers_ids is not None:
            product.developers.set(developers_ids)
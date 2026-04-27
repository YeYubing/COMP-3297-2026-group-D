# defects/views.py
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Defect, Product
from .serializers import DefectSerializer, ProductSerializer

class DefectViewSet(viewsets.ModelViewSet):
    serializer_class = DefectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.groups.filter(name='Product Owner').exists():
            return Defect.objects.filter(product__owner=user).order_by('id')
        
        elif user.groups.filter(name='Developer').exists():
            return Defect.objects.filter(product__developers=user).order_by('id')
        
        else:
            return Defect.objects.filter(
                Q(tester_email=user.email) | Q(tester_id=str(user.id))
            ).order_by('id')
    
    def perform_create(self, serializer):
        # Automatically set the tester information from the authenticated user
        serializer.save(
            tester_id=str(self.request.user.id),
            tester_email=self.request.user.email,
            status='new'
        )            
            self.developer_user = User.objects.create_user(
                username='developer1',
                email='developer1@example.com',
                password='testpass123'
            )
            self.developer_user.groups.add(self.developer_group)
            
            self.owner_user = User.objects.create_user(
                username='owner1',
                email='owner1@example.com',
                password='testpass123'
            )
            self.owner_user.groups.add(self.owner_group)

            # Create test product
            self.product = Product.objects.create(
                product_id='PROD002',
                version='2.0.0',
                owner=self.owner_user,
                description='Test Product'
            )
            self.product.developers.set([])
            self.product.developers.add(self.developer_user)
            
            # Create test defect
            self.defect = Defect.objects.create(
                product=self.product,
                title='Test Defect',
                description='This is a test defect',
                steps_to_reproduce='1. Do this\n2. Do that',
                tester_id=str(self.tester_user.id),
                tester_email=self.tester_user.email,
                status='new'
            )


class DefectAPITests(BaseAPITestCase):
    
    def test_defect_create_successful(self):
        # Authenticate using APIClient's method
        self.client.force_authenticate(user=self.tester_user)
        
        data = {
            'product': self.product.id,
            'title': 'New Test Defect',
            'description': 'A newly created defect',
            'steps_to_reproduce': 'Step 1\nStep 2'
        }
        
        # Make the request - the tenant header is automatically included
        response = self.client.post('/api/defects/', data, format='json')

        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Defect')
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['tester_id'], str(self.tester_user.id))


from rest_framework import serializers
from .models import Defect, Product, Comment, User

# ====================== Product Serializer ======================
class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    developers = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'product_id',
            'version',
            'owner',
            'description',
            'developers',
            'created_at'
        ]
        read_only_fields = ['id', 'date_reported', 'date_fixed', 'tester_id']

# ====================== CommentSerializer  ======================
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)  
    class Meta:
        model = Comment
        fields = ['id', 'author', 'text', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

class DefectSerializer(serializers.ModelSerializer):
    assigned_to = serializers.StringRelatedField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)          
    new_comment = serializers.CharField(write_only=True, required=False, allow_blank=True) 
    target_defect_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    tester_email = serializers.EmailField(label="Tester email", required=False, allow_blank=True)

    class Meta:
        model = Defect
        fields = [
            'id', 'product', 'version', 'title', 'description', 'steps_to_reproduce',
            'tester_id', 'tester_email', 'severity', 'priority', 'status','target_defect_id',
            'assigned_to', 'date_reported', 'date_fixed', 'comments', 'new_comment'
        ]
        read_only_fields = ['id', 'date_reported', 'date_fixed', 'tester_id', 'version']
    
    def create(self, validated_data):
        validated_data.pop('new_comment', None)
        validated_data.pop('target_defect_id', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('new_comment', None)
        validated_data.pop('target_defect_id', None)
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        user = self.context['request'].user
        method = self.context['request'].method  

        # ==================== Tester  ====================
        if user.groups.filter(name='Tester').exists():
            if method == 'POST':
                fields_to_hide = ['version', 'status', 'severity', 'priority', 'date_fixed', 'assigned_to']
                for field in fields_to_hide:
                    fields.pop(field, None)

        # ==================== Developer and Product Owner  ====================
        else:
            if method == 'PUT' and 'status' in fields:
                if user.groups.filter(name='Developer').exists():
                    fields['status'].choices = [
                        ('open', 'Open'),
                        ('assigned', 'Assigned'),
                        ('cannot reproduce', 'Cannot reproduce'),
                        ('fixed', 'Fixed')
                    ]

                elif user.groups.filter(name='Product Owner').exists():
                    fields['status'].choices = [
                        ('new', 'New'),
                        ('open', 'Open'),
                        ('rejected', 'Rejected'),
                        ('reopened', 'Reopened'),
                        ('resolved', 'Resolved'),
                        ('duplicate', 'Duplicate')
                    ]

        return fields

    read_only_fields = [
        'severity',
        'priority',
        'date_reported',
        'date_fixed'
    ]

class TesterDefectSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True, default='new')
    class Meta:
        model = Defect
        fields = ['id', 'product', 'title', 'description', 'steps_to_reproduce', 'tester_email', 'tester_id', 'status', 'date_reported']
        read_only_fields = ['id', 'status', 'date_reported', 'tester_id']

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta
from defects.models import Defect, Product, Comment, DefectHistory


class test_api(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        
        # Create groups
        self.tester_group, _ = Group.objects.get_or_create(name='Tester')
        self.developer_group, _ = Group.objects.get_or_create(name='Developer')
        self.owner_group, _ = Group.objects.get_or_create(name='Product Owner')
        
        # Create test users
        self.tester_user = User.objects.create_user(
            username='tester1',
            email='tester1@example.com',
            password='testpass123'
        )
        self.tester_user.groups.add(self.tester_group)
        
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
            product_id='PROD001',
            version='1.0.0',
            owner=self.owner_user,
            description='Test Product',
            expiry_date=datetime.now().date() + timedelta(days=365)
        )
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
        self.client.force_authenticate(user=self.tester_user)
        
        data = {
            'product': self.product.id,
            'title': 'New Test Defect',
            'description': 'A newly created defect',
            'steps_to_reproduce': 'Step 1\nStep 2'
        }
        
        response = self.client.post('/api/defects/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Defect')
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['tester_id'], str(self.tester_user.id))
    
    def test_defect_list_successful(self):
        self.client.force_authenticate(user=self.tester_user)
        
        response = self.client.get('/api/defects/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_defect_retrieve_successful(self):
        self.client.force_authenticate(user=self.tester_user)
        
        response = self.client.get(f'/api/defects/{self.defect.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.defect.id)
        self.assertEqual(response.data['title'], self.defect.title)
    
    def test_defect_update_successful(self):
        self.client.force_authenticate(user=self.owner_user)
        
        data = {
            'title': 'Updated Defect Title',
            'description': 'Updated description',
            'status': 'open'
        }
        
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Defect Title')
        self.assertEqual(response.data['status'], 'open')
    
    def test_defect_delete_successful(self):
        defect_to_delete = Defect.objects.create(
            product=self.product,
            title='To Be Deleted',
            description='This will be deleted',
            tester_id=str(self.tester_user.id),
            tester_email=self.tester_user.email,
            status='new'
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.delete(f'/api/defects/{defect_to_delete.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Defect.objects.filter(id=defect_to_delete.id).exists())
    
    def test_defect_candidate_targets_action_successful(self):
        """Test successful retrieval of candidate targets for duplicate marking."""
        target_defect = Defect.objects.create(
            product=self.product,
            title='Target Defect',
            description='This is a target',
            tester_id=str(self.tester_user.id),
            tester_email=self.tester_user.email,
            status='open'
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(f'/api/defects/{self.defect.id}/candidate-targets/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_defect_allowed_statuses_action_successful(self):
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(f'/api/defects/{self.defect.id}/allowed-statuses/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('allowed_statuses', response.data)
        self.assertIsInstance(response.data['allowed_statuses'], list)
    
    def test_defect_developer_metrics_action_successful(self):

        DefectHistory.objects.create(
            defect=self.defect,
            old_status='open',
            new_status='fixed',
            changed_by=self.owner_user,
            assigned_to=self.developer_user
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(f'/api/defects/metrics/{self.developer_user.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('developer_id', response.data)
        self.assertIn('rating', response.data)
        self.assertEqual(response.data['developer_id'], self.developer_user.id)


class ProductAPITests(BaseAPITestCase):
    
    def test_product_create_successful(self):
        self.client.force_authenticate(user=self.owner_user)
        
        data = {
            'product_id': 'PROD002',
            'version': '2.0.0',
            'description': 'New Test Product',
            'expiry_date': (datetime.now() + timedelta(days=365)).date()
        }
        
        response = self.client.post('/api/products/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product_id'], 'PROD002')
        self.assertEqual(response.data['owner'], self.owner_user.username)
        self.assertEqual(response.data['version'], '2.0.0')
    
    def test_product_list_successful(self):
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/products/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_product_retrieve_successful(self):
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get(f'/api/products/{self.product.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.id)
        self.assertEqual(response.data['product_id'], 'PROD001')
    
    def test_product_update_successful(self):
        """Test successful update of a product."""
        self.client.force_authenticate(user=self.owner_user)
        
        data = {
            'description': 'Updated Product Description'
        }
        
        response = self.client.patch(f'/api/products/{self.product.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated Product Description')
    
    def test_product_delete_successful(self):
        """Test successful deletion of a product."""
        # Create another product for deletion test
        product_to_delete = Product.objects.create(
            product_id='PROD003',
            version='3.0.0',
            owner=self.owner_user,
            description='To Be Deleted'
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.delete(f'/api/products/{product_to_delete.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=product_to_delete.id).exists())
    
    def test_product_update_with_developers_successful(self):
        """Test successful update of product with developer assignment."""
        self.client.force_authenticate(user=self.owner_user)
        
        # Create another developer
        developer2 = User.objects.create_user(
            username='developer2',
            email='developer2@example.com',
            password='testpass123'
        )
        developer2.groups.add(self.developer_group)
        
        data = {
            'developers': [self.developer_user.id, developer2.id]
        }
        
        response = self.client.patch(f'/api/products/{self.product.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['developers']), 2)


class defect_comment_tests(BaseAPITestCase):
    
    def test_defect_add_comment_through_update_successful(self):
        """Test successful addition of a comment to a defect via update."""
        self.client.force_authenticate(user=self.owner_user)
        
        # First, update status to 'open'
        self.defect.status = 'open'
        self.defect.save()
        
        data = {
            'new_comment': 'This is a test comment'
        }
        
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['comments']), 0)
        self.assertEqual(response.data['comments'][0]['text'], 'This is a test comment')


class defect_filtering_tests(BaseAPITestCase):
    
    def test_defect_filter_by_status_successful(self):
        # Create defect with different status
        defect2 = Defect.objects.create(
            product=self.product,
            title='Open Defect',
            description='An open defect',
            tester_id=str(self.tester_user.id),
            tester_email=self.tester_user.email,
            status='open'
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/defects/?status=open', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        for defect in response.data['results']:
            self.assertEqual(defect['status'], 'open')
    
    def test_defect_filter_by_priority_successful(self):
        # Update defect with priority
        self.defect.priority = 'high'
        self.defect.save()
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/defects/?priority=high', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_defect_filter_by_severity_successful(self):
        self.defect.severity = 'critical'
        self.defect.save()
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/defects/?severity=critical', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

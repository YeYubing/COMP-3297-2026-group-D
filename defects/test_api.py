from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from defects.models import Defect, Product, Comment, DefectHistory
from django.utils import timezone


class APITestSetup(TestCase):
    """Base test class with common setup for all API tests."""
    
    def setUp(self):
        """Set up test users, groups, and products."""
        self.client = APIClient()
        
        # Create user groups
        self.tester_group, _ = Group.objects.get_or_create(name='Tester')
        self.owner_group, _ = Group.objects.get_or_create(name='Product Owner')
        self.developer_group, _ = Group.objects.get_or_create(name='Developer')
        
        # Create users
        self.tester = User.objects.create_user(username='tester1', password='testpass123', email='tester@example.com')
        self.tester.groups.add(self.tester_group)
        
        self.owner = User.objects.create_user(username='owner1', password='testpass123', email='owner@example.com')
        self.owner.groups.add(self.owner_group)
        
        self.developer = User.objects.create_user(username='dev1', password='testpass123', email='dev@example.com')
        self.developer.groups.add(self.developer_group)
        
        self.another_developer = User.objects.create_user(username='dev2', password='testpass123', email='dev2@example.com')
        self.another_developer.groups.add(self.developer_group)
        
        # Create a product
        self.product = Product.objects.create(
            product_id='PROD001',
            version='1.0.0',
            owner=self.owner,
            description='Test Product'
        )
        self.product.developers.add(self.developer)
        
        # Create another product for testing developer assignment
        self.product2 = Product.objects.create(
            product_id='PROD002',
            version='1.0.0',
            owner=self.owner,
            description='Test Product 2'
        )
        self.product2.developers.add(self.another_developer)


# ====================== DEFECT ENDPOINT TESTS ======================

class DefectListCreateTest(APITestSetup):
    """Test Defect List and Create endpoints."""
    
    def test_defect_list_unauthenticated(self):
        """Test that unauthenticated users cannot list defects."""
        response = self.client.get('/api/defects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_defect_list_authenticated_tester(self):
        """Test that authenticated tester can list their own defects."""
        self.client.force_authenticate(user=self.tester)
        Defect.objects.create(
            product=self.product,
            title='Test Defect',
            description='Description',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email
        )
        response = self.client.get('/api/defects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_defect_list_authenticated_owner(self):
        """Test that authenticated owner can list defects for their products."""
        self.client.force_authenticate(user=self.owner)
        Defect.objects.create(
            product=self.product,
            title='Test Defect',
            description='Description',
            tester_id='123',
            tester_email='test@example.com'
        )
        response = self.client.get('/api/defects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_defect_list_authenticated_developer(self):
        """Test that authenticated developer can list defects for their products."""
        self.client.force_authenticate(user=self.developer)
        Defect.objects.create(
            product=self.product,
            title='Test Defect',
            description='Description',
            tester_id='123',
            tester_email='test@example.com'
        )
        response = self.client.get('/api/defects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_create_defect_as_tester_success(self):
        """Test that tester can successfully create a defect."""
        self.client.force_authenticate(user=self.tester)
        data = {
            'product': self.product.id,
            'title': 'New Bug Found',
            'description': 'This is a bug description',
            'steps_to_reproduce': '1. Do this\n2. Do that',
            'tester_email': self.tester.email
        }
        response = self.client.post('/api/defects/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['title'], 'New Bug Found')
    
    def test_create_defect_as_developer_forbidden(self):
        """Test that developer cannot create defects."""
        self.client.force_authenticate(user=self.developer)
        data = {
            'product': self.product.id,
            'title': 'New Bug',
            'description': 'Bug description'
        }
        response = self.client.post('/api/defects/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only testers can submit', str(response.data))
    
    def test_create_defect_as_owner_forbidden(self):
        """Test that owner cannot create defects."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'product': self.product.id,
            'title': 'New Bug',
            'description': 'Bug description'
        }
        response = self.client.post('/api/defects/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only testers can submit', str(response.data))


class DefectRetrieveUpdateDeleteTest(APITestSetup):
    """Test Defect Retrieve, Update, Delete endpoints."""
    
    def setUp(self):
        super().setUp()
        self.defect = Defect.objects.create(
            product=self.product,
            title='Test Defect',
            description='Test Description',
            steps_to_reproduce='Steps here',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            severity='major',
            priority='high'
        )
    
    def test_retrieve_defect_as_tester(self):
        """Test that tester can retrieve their own defect."""
        self.client.force_authenticate(user=self.tester)
        response = self.client.get(f'/api/defects/{self.defect.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Defect')
    
    def test_retrieve_defect_as_owner(self):
        """Test that owner can retrieve defects for their products."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/defects/{self.defect.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Defect')
    
    def test_retrieve_defect_as_developer(self):
        """Test that developer can retrieve defects for their products."""
        self.client.force_authenticate(user=self.developer)
        response = self.client.get(f'/api/defects/{self.defect.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_defect_nonexistent(self):
        """Test that retrieving nonexistent defect returns 404."""
        self.client.force_authenticate(user=self.tester)
        response = self.client.get('/api/defects/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_defect_status_as_owner(self):
        """Test that owner can update defect status (new->open)."""
        self.client.force_authenticate(user=self.owner)
        data = {'status': 'open'}
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.defect.refresh_from_db()
        self.assertEqual(self.defect.status, 'open')
    
    def test_update_defect_status_as_developer(self):
        """Test that developer can update defect status (new->open->assigned)."""
        # First open the defect as owner
        self.defect.status = 'open'
        self.defect.save()
        
        self.client.force_authenticate(user=self.developer)
        data = {'status': 'assigned'}
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.defect.refresh_from_db()
        self.assertEqual(self.defect.status, 'assigned')
        self.assertEqual(self.defect.assigned_to, self.developer)
    
    def test_update_defect_with_comment(self):
        """Test that user can add comment while updating defect."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'status': 'open',
            'new_comment': 'This is a test comment'
        }
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.filter(defect=self.defect).count(), 1)
    
    def test_mark_defect_as_duplicate(self):
        """Test that owner can mark defect as duplicate."""
        target_defect = Defect.objects.create(
            product=self.product,
            title='Target Defect',
            description='Target Description',
            tester_id='123',
            tester_email='test@example.com'
        )
        target_defect.status = 'open'
        target_defect.save()
        
        self.client.force_authenticate(user=self.owner)
        data = {
            'status': 'duplicate',
            'target_defect_id': target_defect.id
        }
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.defect.refresh_from_db()
        self.assertEqual(self.defect.status, 'duplicate')
        self.assertEqual(self.defect.duplicate_of, target_defect)
    
    def test_mark_duplicate_invalid_target(self):
        """Test that marking duplicate fails with invalid target."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'status': 'duplicate',
            'target_defect_id': 99999
        }
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_mark_duplicate_self_reference_fails(self):
        """Test that marking a defect as duplicate of itself fails."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'status': 'duplicate',
            'target_defect_id': self.defect.id
        }
        response = self.client.patch(f'/api/defects/{self.defect.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be marked as a duplicate of itself', str(response.data))
    
    def test_delete_defect_as_owner(self):
        """Test that owner can delete a defect."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(f'/api/defects/{self.defect.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Defect.objects.filter(id=self.defect.id).exists())


class DefectCustomActionsTest(APITestSetup):
    """Test Defect custom actions (candidate-targets, allowed-statuses, metrics)."""
    
    def setUp(self):
        super().setUp()
        self.defect = Defect.objects.create(
            product=self.product,
            title='Test Defect',
            description='Test Description',
            tester_id='123',
            tester_email='test@example.com'
        )
    
    def test_candidate_targets_action(self):
        """Test candidate-targets custom action."""
        # Create a non-new defect as target
        target = Defect.objects.create(
            product=self.product,
            title='Target',
            description='Description',
            tester_id='123',
            tester_email='test@example.com',
            status='open'
        )
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/defects/{self.defect.id}/candidate-targets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_allowed_statuses_action_owner(self):
        """Test allowed-statuses action for owner."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/defects/{self.defect.id}/allowed-statuses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        allowed_values = [item['value'] for item in response.data['allowed_statuses']]
        self.assertIn('open', allowed_values)
    
    def test_allowed_statuses_action_developer(self):
        """Test allowed-statuses action for developer."""
        self.defect.status = 'open'
        self.defect.save()
        
        self.client.force_authenticate(user=self.developer)
        response = self.client.get(f'/api/defects/{self.defect.id}/allowed-statuses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        allowed_values = [item['value'] for item in response.data['allowed_statuses']]
        self.assertIn('assigned', allowed_values)
    
    def test_developer_metrics_action(self):
        """Test developer metrics custom action."""
        # Create some history for the developer
        self.defect.assigned_to = self.developer
        self.defect.save()
        DefectHistory.objects.create(
            defect=self.defect,
            old_status='open',
            new_status='fixed',
            changed_by=self.developer,
            assigned_to=self.developer
        )
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/defects/metrics/{self.developer.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rating', response.data)


# ====================== PRODUCT ENDPOINT TESTS ======================

class ProductListCreateTest(APITestSetup):
    """Test Product List and Create endpoints."""
    
    def test_product_list_unauthenticated(self):
        """Test that unauthenticated users cannot list products."""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_product_list_authenticated_owner(self):
        """Test that owner can list their own products."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_product_list_authenticated_developer(self):
        """Test that developer cannot list products (empty list)."""
        self.client.force_authenticate(user=self.developer)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_product_list_authenticated_tester(self):
        """Test that tester cannot list products (empty list)."""
        self.client.force_authenticate(user=self.tester)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_create_product_as_owner_success(self):
        """Test that owner can successfully create a product."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'product_id': 'PROD003',
            'version': '1.0.0',
            'description': 'New Test Product',
            'developers': [self.developer.id]
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product_id'], 'PROD003')
    
    def test_create_product_as_developer_forbidden(self):
        """Test that developer cannot create products."""
        self.client.force_authenticate(user=self.developer)
        data = {
            'product_id': 'PROD003',
            'version': '1.0.0',
            'description': 'New Product'
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only product owners can register', str(response.data))
    
    def test_create_product_as_tester_forbidden(self):
        """Test that tester cannot create products."""
        self.client.force_authenticate(user=self.tester)
        data = {
            'product_id': 'PROD003',
            'version': '1.0.0',
            'description': 'New Product'
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Only product owners can register', str(response.data))


class ProductRetrieveUpdateDeleteTest(APITestSetup):
    """Test Product Retrieve, Update, Delete endpoints."""
    
    def test_retrieve_product_as_owner(self):
        """Test that owner can retrieve their products."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], 'PROD001')
    
    def test_retrieve_product_as_other_owner_forbidden(self):
        """Test that owner cannot retrieve other owners' products."""
        other_owner = User.objects.create_user(username='owner2', password='testpass123')
        other_owner.groups.add(self.owner_group)
        
        self.client.force_authenticate(user=other_owner)
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_product_as_developer_forbidden(self):
        """Test that developer cannot retrieve products."""
        self.client.force_authenticate(user=self.developer)
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_nonexistent_product(self):
        """Test that retrieving nonexistent product returns 404."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_product_as_owner(self):
        """Test that owner can update their products."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'product_id': 'PROD001-UPDATED',
            'version': '2.0.0',
            'description': 'Updated Description'
        }
        response = self.client.patch(f'/api/products/{self.product.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.version, '2.0.0')
    
    def test_update_product_developers(self):
        """Test that owner can update product developers."""
        self.client.force_authenticate(user=self.owner)
        data = {
            'developers': [self.another_developer.id]
        }
        response = self.client.patch(f'/api/products/{self.product.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertIn(self.another_developer, self.product.developers.all())
    
    def test_delete_product_as_owner(self):
        """Test that owner can delete their products."""
        self.client.force_authenticate(user=self.owner)
        product_id = self.product.id
        response = self.client.delete(f'/api/products/{product_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=product_id).exists())


# ====================== FILTERING TESTS ======================

class DefectFilteringTest(APITestSetup):
    """Test Defect filtering functionality."""
    
    def setUp(self):
        super().setUp()
        # Create multiple defects with different statuses and priorities
        self.defect1 = Defect.objects.create(
            product=self.product,
            title='High Priority Bug',
            description='High priority issue',
            tester_id='123',
            tester_email='test@example.com',
            priority='high',
            severity='critical',
            status='open'
        )
        self.defect2 = Defect.objects.create(
            product=self.product,
            title='Low Priority Bug',
            description='Low priority issue',
            tester_id='123',
            tester_email='test@example.com',
            priority='low',
            severity='low',
            status='new'
        )
    
    def test_filter_by_status(self):
        """Test filtering defects by status."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/defects/?status=open')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        statuses = [d['status'] for d in response.data]
        self.assertTrue(all(s == 'open' for s in statuses))
    
    def test_filter_by_priority(self):
        """Test filtering defects by priority."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/defects/?priority=high')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
    
    def test_filter_by_severity(self):
        """Test filtering defects by severity."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/defects/?severity=critical')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

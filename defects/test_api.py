# tests/test_simple_api.py
"""
Simple API test suite for BetaTrax - tests each endpoint method exactly once.
Run with: python manage.py test tests.test_simple_api
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta

from defects.models import Defect, Product, DefectHistory


class SimpleAPITests(TestCase):
    """
    Tests each API endpoint method once - minimal but complete coverage.
    """
    
    def setUp(self):
        self.client = APIClient()
        
        # Create groups
        self.tester_group = Group.objects.create(name='Tester')
        self.developer_group = Group.objects.create(name='Developer')
        self.owner_group = Group.objects.create(name='Product Owner')
        
        # Create users
        self.tester = User.objects.create_user(
            username='tester', email='tester@test.com', password='pass'
        )
        self.tester.groups.add(self.tester_group)
        
        self.developer = User.objects.create_user(
            username='developer', email='dev@test.com', password='pass'
        )
        self.developer.groups.add(self.developer_group)
        
        self.owner = User.objects.create_user(
            username='owner', email='owner@test.com', password='pass'
        )
        self.owner.groups.add(self.owner_group)
        
        # Create product
        self.product = Product.objects.create(
            product_id='TEST-PROD',
            version='1.0',
            owner=self.owner,
            description='Test product',
            expiry_date=datetime.now().date() + timedelta(days=365)
        )
        self.product.developers.add(self.developer)
        
        # Create defect
        self.defect = Defect.objects.create(
            product=self.product,
            title='Original Defect',
            description='Original description',
            steps_to_reproduce='Steps here',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            status='new',
            severity='major',
            priority='medium'
        )
        
        # URLs
        self.defects_url = '/api/defects/'
        self.defect_detail_url = f'/api/defects/{self.defect.id}/'
        self.products_url = '/api/products/'
        self.product_detail_url = f'/api/products/{self.product.id}/'

    # ========== DEFECT ENDPOINTS ==========
    
    def test_01_defect_post_create(self):
        """POST /api/defects/ - Create a new defect (Tester)"""
        self.client.force_authenticate(user=self.tester)
        
        response = self.client.post(self.defects_url, {
            'product': self.product.id,
            'title': 'New Test Defect',
            'description': 'This is a test defect',
            'steps_to_reproduce': '1. Login\n2. Click button'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Defect')
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['tester_id'], str(self.tester.id))
        print("✓ POST /api/defects/")

    def test_02_defect_get_list(self):
        """GET /api/defects/ - List all defects"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.defects_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        print("✓ GET /api/defects/")

    def test_03_defect_get_detail(self):
        """GET /api/defects/{id}/ - Get single defect"""
        self.client.force_authenticate(user=self.tester)
        
        response = self.client.get(self.defect_detail_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.defect.id)
        self.assertEqual(response.data['title'], self.defect.title)
        print(f"✓ GET /api/defects/{self.defect.id}/")

    def test_04_defect_put_update(self):
        """PUT /api/defects/{id}/ - Full update"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.put(self.defect_detail_url, {
            'product': self.product.id,
            'title': 'Fully Updated Defect',
            'description': 'Completely new description',
            'steps_to_reproduce': 'New steps',
            'status': 'open',
            'severity': 'critical',
            'priority': 'high'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Fully Updated Defect')
        print("✓ PUT /api/defects/{id}/")

    def test_05_defect_patch_update(self):
        """PATCH /api/defects/{id}/ - Partial update"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.patch(self.defect_detail_url, {
            'title': 'Partially Updated Title',
            'priority': 'critical'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Partially Updated Title')
        self.assertEqual(response.data['priority'], 'critical')
        print("✓ PATCH /api/defects/{id}/")

    def test_06_defect_delete(self):
        """DELETE /api/defects/{id}/ - Delete defect"""
        # Create temporary defect for deletion
        temp_defect = Defect.objects.create(
            product=self.product,
            title='To Delete',
            description='Temp',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            status='new'
        )
        temp_url = f'/api/defects/{temp_defect.id}/'
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(temp_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Defect.objects.filter(id=temp_defect.id).exists())
        print("✓ DELETE /api/defects/{id}/")

    # ========== PRODUCT ENDPOINTS ==========

    def test_07_product_post_create(self):
        """POST /api/products/ - Create a new product (Product Owner only)"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.post(self.products_url, {
            'product_id': 'NEW-PROD',
            'version': '2.0',
            'description': 'Brand new product',
            'expiry_date': (datetime.now().date() + timedelta(days=180)).isoformat()
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product_id'], 'NEW-PROD')
        self.assertEqual(response.data['owner'], self.owner.username)
        print("✓ POST /api/products/")

    def test_08_product_get_list(self):
        """GET /api/products/ - List all products"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.products_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        print("✓ GET /api/products/")

    def test_09_product_get_detail(self):
        """GET /api/products/{id}/ - Get single product"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(self.product_detail_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.id)
        self.assertEqual(response.data['product_id'], self.product.product_id)
        print(f"✓ GET /api/products/{self.product.id}/")

    def test_10_product_put_update(self):
        """PUT /api/products/{id}/ - Full product update"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.put(self.product_detail_url, {
            'product_id': 'UPDATED-PROD',
            'version': '3.0',
            'description': 'Fully updated product',
            'expiry_date': (datetime.now().date() + timedelta(days=400)).isoformat(),
            'developers': [self.developer.id]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], 'UPDATED-PROD')
        self.assertEqual(response.data['version'], '3.0')
        print("✓ PUT /api/products/{id}/")

    def test_11_product_patch_update(self):
        """PATCH /api/products/{id}/ - Partial product update"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.patch(self.product_detail_url, {
            'description': 'Patched product description'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Patched product description')
        print("✓ PATCH /api/products/{id}/")

    def test_12_product_delete(self):
        """DELETE /api/products/{id}/ - Delete product"""
        # Create temporary product for deletion
        temp_product = Product.objects.create(
            product_id='TEMP-PROD',
            version='1.0',
            owner=self.owner,
            description='To be deleted'
        )
        temp_url = f'/api/products/{temp_product.id}/'
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(temp_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=temp_product.id).exists())
        print("✓ DELETE /api/products/{id}/")

    # ========== CUSTOM ACTIONS ==========

    def test_13_candidate_targets(self):
        """GET /api/defects/{id}/candidate-targets/ - Get possible duplicate targets"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(f'/api/defects/{self.defect.id}/candidate-targets/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        print("✓ GET /api/defects/{id}/candidate-targets/")

    def test_14_allowed_statuses(self):
        """GET /api/defects/{id}/allowed-statuses/ - Get allowed status transitions"""
        self.client.force_authenticate(user=self.owner)
        
        response = self.client.get(f'/api/defects/{self.defect.id}/allowed-statuses/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('allowed_statuses', response.data)
        print("✓ GET /api/defects/{id}/allowed-statuses/")

    def test_15_developer_metrics(self):
        """GET /api/defects/metrics/{user_id}/ - Get developer rating"""
        # Create history entries for developer
        for i in range(25):
            defect = Defect.objects.create(
                product=self.product,
                title=f'Defect {i}',
                description='Fixed',
                tester_id=str(self.tester.id),
                tester_email=self.tester.email,
                status='fixed'
            )
            DefectHistory.objects.create(
                defect=defect,
                old_status='assigned',
                new_status='fixed',
                changed_by=self.owner,
                assigned_to=self.developer
            )
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/defects/metrics/{self.developer.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['developer_id'], self.developer.id)
        self.assertIn('rating', response.data)
        print("✓ GET /api/defects/metrics/{user_id}/")

    def test_16_mark_as_duplicate(self):
        """PATCH /api/defects/{id}/ - Mark defect as duplicate"""
        # Create source and target defects
        target = Defect.objects.create(
            product=self.product,
            title='Target Defect',
            description='Target for duplicate',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            status='open'
        )
        source = Defect.objects.create(
            product=self.product,
            title='Source Defect',
            description='Will become duplicate',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            status='new'
        )
        source_url = f'/api/defects/{source.id}/'
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(source_url, {
            'status': 'duplicate',
            'target_defect_id': target.id
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'duplicate')
        
        # Verify duplicate relationship
        source.refresh_from_db()
        self.assertEqual(source.duplicate_of_id, target.id)
        print("✓ PATCH /api/defects/{id}/ (mark duplicate)")

    def test_17_add_comment_via_update(self):
        """PATCH /api/defects/{id}/ - Add comment while updating"""
        self.client.force_authenticate(user=self.owner)
        
        # Change status to open first (allowed transition)
        self.defect.status = 'open'
        self.defect.save()
        
        response = self.client.patch(self.defect_detail_url, {
            'status': 'rejected',
            'new_comment': 'This defect is rejected because it is invalid'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')
        self.assertGreater(len(response.data['comments']), 0)
        print("✓ PATCH /api/defects/{id}/ (with comment)")

    def test_18_status_transition_new_to_open(self):
        """PATCH /api/defects/{id}/ - Transition from new to open (Owner)"""
        # Create defect with 'new' status
        new_defect = Defect.objects.create(
            product=self.product,
            title='New Defect',
            description='For transition test',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            status='new'
        )
        new_url = f'/api/defects/{new_defect.id}/'
        
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(new_url, {'status': 'open'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'open')
        print("✓ PATCH /api/defects/{id}/ (status: new → open)")

    def test_19_status_transition_assigned_to_fixed(self):
        """PATCH /api/defects/{id}/ - Transition from assigned to fixed (Developer)"""
        # Create defect assigned to developer
        assigned_defect = Defect.objects.create(
            product=self.product,
            title='Assigned Defect',
            description='For fix test',
            tester_id=str(self.tester.id),
            tester_email=self.tester.email,
            status='assigned',
            assigned_to=self.developer
        )
        assigned_url = f'/api/defects/{assigned_defect.id}/'
        
        self.client.force_authenticate(user=self.developer)
        response = self.client.patch(assigned_url, {'status': 'fixed'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'fixed')
        self.assertIsNotNone(response.data['date_fixed'])
        print("✓ PATCH /api/defects/{id}/ (status: assigned → fixed)")

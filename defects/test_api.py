# defects/test_api.py
from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from defects.models import Defect, Product
from django_tenants.utils import tenant_context
from tenants.models import Client
from django.urls import reverse


class BaseAPITestCase(TestCase):
    
    def setUp(self):
        self.tenant, _ = Client.objects.get_or_create(
            schema_name='standard',
            defaults={'name': 'Standard Tenant'}
        )

        self.client = APIClient()
        
        # Set tenant header for all requests
        self.client.defaults['HTTP_X_TENANT'] = self.tenant.schema_name

        with tenant_context(self.tenant):
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
    
    def test_debug_urls(self):
        """Debug test to see what URLs are available"""
        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.tester_user)
            
            # Try to get the list endpoint
            response = self.client.get('/api/defects/')
            print(f"\nGET /api/defects/ - Status: {response.status_code}")
            
            if response.status_code == 404:
                # Try without the slash
                response = self.client.get('/api/defects')
                print(f"GET /api/defects - Status: {response.status_code}")
            
            print(f"Response content: {response.content}")
    
    def test_defect_create_successful(self):
        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.tester_user)
            
            data = {
                'product': self.product.id,
                'title': 'New Test Defect',
                'description': 'A newly created defect',
                'steps_to_reproduce': 'Step 1\nStep 2'
            }
            
            response = self.client.post('/api/defects/', data, format='json')
            
            print(f"\nPOST Status: {response.status_code}")
            print(f"POST Content: {response.content}")
            
            if response.status_code == 404:
                # Try alternative URL patterns
                alt_urls = ['/api/defects', '/defects/', '/defects']
                for url in alt_urls:
                    alt_response = self.client.post(url, data, format='json')
                    print(f"Trying {url} - Status: {alt_response.status_code}")
                    if alt_response.status_code == 201:
                        response = alt_response
                        break
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['title'], 'New Test Defect')
            self.assertEqual(response.data['status'], 'new')
            self.assertEqual(response.data['tester_id'], str(self.tester_user.id))

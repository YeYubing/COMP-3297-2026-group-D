from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from unittest.mock import patch, Mock

from .views import DefectViewSet


class dev_metrics_test(TestCase):
    
    def setUp(self):
      
        self.developer_group, _ = Group.objects.get_or_create(name='Developer')
        
        self.developer = User.objects.create_user(
            username='test_developer',
            password='testpass123',
            email='dev@test.com'
        )
      
        self.developer.groups.add(self.developer_group)
        
        self.view = DefectViewSet()
    
    def get_rating(self, fixed_count, reopened_count):
      
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.developer
    
        with patch('defects.views.DefectHistory.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.count.side_effect = [fixed_count, reopened_count]
        
            mock_filter.return_value = mock_queryset
        
            response = self.view.developer_metrics(request, user_id=self.developer.id)
            return response.data['rating']

  
    def test_insufficient_data(self):
      
        test_cases = [
            (0, 0),      # Lower boundary: no defects
            (10, 5),     # Middle value
            (19, 100),   # Upper boundary: exactly 19 fixed
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Insufficient data")

  
    def test_good(self):
      
        test_cases = [
            (20, 0),      # Lower boundary: minimum fixed, zero reopened
            (32, 0),      # Fixed exactly 32 with zero reopened
            (33, 1),      # Ratio slightly below 1/32 (0.0303)
            (100, 2),     # Typical case (0.02)
            (1000, 31),   # Upper boundary of ratio (0.031)
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Good")
    

    def test_fair(self):

        test_cases = [
            (32, 1),      # Lower boundary: exactly 1/32
            (64, 3),      # Middle value (0.046875)
            (20, 2),      # Ratio = 0.1
            (64, 7),      # Upper boundary: just below 1/8 (0.109375)
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Fair")
    
    
    def test_poor(self):

        test_cases = [
            (32, 4),      # Lower boundary: exactly 1/8
            (40, 6),      # Middle value (0.15)
            (20, 5),      # Ratio = 0.25
            (20, 20),     # Ratio = 1.0
            (30, 40),     # Ratio > 1.0
        ]
        
        for fixed, reopened in test_cases:
            with self.subTest(fixed = fixed, reopened = reopened):
                rating = self.get_rating(fixed, reopened)
                self.assertEqual(rating, "Poor")
    
def test_boundary_values(self):

    rating_below = self.get_rating(19, 0)
    self.assertEqual(rating_below, "Insufficient data")
    
    rating_at = self.get_rating(20, 0)
    self.assertEqual(rating_at, "Good")
    
    rating_above = self.get_rating(21, 0)
    self.assertEqual(rating_above, "Good")
    
    rating_below = self.get_rating(33, 1)
    self.assertEqual(rating_below, "Good")
    
    rating_at = self.get_rating(32, 1)
    self.assertEqual(rating_at, "Fair")
    
    rating_above = self.get_rating(31, 1)
    self.assertEqual(rating_above, "Fair")
    
    rating_below = self.get_rating(41, 5)
    self.assertEqual(rating_below, "Fair")
    
    rating_at = self.get_rating(32, 4)
    self.assertEqual(rating_at, "Poor")
    
    rating_above = self.get_rating(31, 4)
    self.assertEqual(rating_above, "Poor")

from django.test import TestCase
from django.urls import reverse
from timetrack.models import Timetrack  # Replace `Timetrack` with your model

class SearchAPITest(TestCase):
    def setUp(self):
        # Set up sample data for testing
        Timetrack.objects.create(name="Meeting", description="Team meeting at 10 AM")
        Timetrack.objects.create(name="Coding", description="Write search API")

    def test_search_timetrack(self):
        # Test the search API
        response = self.client.get(reverse('search-timetrack') + '?q=meeting')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

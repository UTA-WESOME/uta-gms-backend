from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    User,
    Project,
)


class TestViews(APITestCase):
    def setUp(self):
        self.client = APIClient()

        register_url = '/api/register'
        data = {
            'email': 'test@example.com',
            'password': 'testpassword',
            'name': 'test',
            'surname': 'test',
        }
        self.client.post(register_url, data, format='json')

        self.login_url = '/api/login'
        self.login_data = {
            'email': 'test@example.com',
            'password': 'testpassword',
        }
        self.client.post(self.login_url, self.login_data, format='json')

        user = User.objects.get(name='test')

        project = Project.objects.create(
            user=user,
            name='Project 1',
            description='Description for Project 1',
            shareable=True
        )

    def test_project_list_success(self):
        url = '/api/projects/'
        response = self.client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]['name'] == 'Project 1'
        assert response.data[0]['description'] == 'Description for Project 1'
        assert response.data[0]['shareable'] is True

    def test_project_detail_success(self):
        url = '/api/projects/1'
        response = self.client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Project 1'
        assert response.data['description'] == 'Description for Project 1'
        assert response.data['shareable'] is True

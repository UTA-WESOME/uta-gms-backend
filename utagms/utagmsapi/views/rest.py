from django.db.models import Max
from django_celery_results.models import TaskResult
from rest_framework import generics

from utagms.celery import app
from utagmsapi.utils.jwt import get_user_from_jwt
from ..models import Project
from ..permissions import IsLogged, IsOwnerOfProject
from ..serializers import CategorySerializer, ProjectSerializer


# Project
class ProjectList(generics.ListCreateAPIView):
    permission_classes = [IsLogged]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        token = self.request.COOKIES.get('access_token')
        user = get_user_from_jwt(token)
        queryset = Project.objects.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        user = get_user_from_jwt(self.request.COOKIES.get('access_token'))
        project = serializer.save(user=user)
        root_category_serializer = CategorySerializer(data={
            'name': 'General',
            'color': 'teal.500',
            'active': True,
            'hasse_diagram': {},
            'parent': None
        })
        if root_category_serializer.is_valid():
            root_category_serializer.save(project=project)


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    lookup_url_kwarg = 'project_pk'

    def perform_destroy(self, instance):
        # Cancel any currently running jobs
        for job in instance.jobs.filter(group=instance.jobs.aggregate(max_group=Max('group'))['max_group']):
            if not TaskResult.objects.filter(task_id=job.task).exists():
                app.control.revoke(job.task, terminate=True)
        super().perform_destroy(instance)

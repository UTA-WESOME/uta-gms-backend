import jwt
from django.db.models import Max
from django_celery_results.models import TaskResult
from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from utagmsapi.models import Project
from utagmsapi.utils.jwt import get_user_from_jwt


class IsLogged(permissions.BasePermission):

    def has_permission(self, request, view):
        token = request.COOKIES.get('access_token')

        if token is None:
            return False

        try:
            _ = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        return True


class IsOwnerOfProject(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get project
        project_pk = view.kwargs.get('project_pk')
        if project_pk is None:
            return False
        project = Project.objects.filter(id=project_pk).first()
        if project is None:
            return False

        # Checking if user is the owner of the project.
        # If they are it means that they can also get criterion or alternative from this project
        return project.user == user


class ProjectJobCompletion(permissions.BasePermission):
    message = {"message": "Project has running jobs!"}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        project_id = view.kwargs.get('project_pk')
        if project_id is None:
            return False  # No project_pk in URL

        project = Project.objects.filter(id=project_id).first()
        if project is None:
            return False  # Project does not exist

        for job in project.jobs.filter(group=project.jobs.aggregate(max_group=Max('group'))['max_group']):
            if not TaskResult.objects.filter(task_id=job.task).exists():
                return False
        return True

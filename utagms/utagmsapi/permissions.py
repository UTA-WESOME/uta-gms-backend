import jwt
from rest_framework import permissions

from utagmsapi.utils.jwt import get_user_from_jwt


class IsLogged(permissions.BasePermission):

    def has_permission(self, request, view):
        token = request.META.get('HTTP_AUTHORIZATION')

        try:
            _ = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        return True


class IsOwnerOfProject(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        token = request.META.get('HTTP_AUTHORIZATION')

        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        return obj.user == user

import jwt
from django.conf import settings
from rest_framework import permissions

from utagmsapi.models import User


class IsOwnerOfProject(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        token = request.META.get('HTTP_AUTHORIZATION')

        # sanity check
        if not token:
            return False

        # check to see if there is a word Bearer
        if token.split()[0] != "Bearer":
            return False

        # get jwt token
        token = token.split()[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        return obj.user == User.objects.filter(id=payload['id']).first()

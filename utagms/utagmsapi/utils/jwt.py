import jwt
from django.conf import settings

from utagmsapi.models import User


def get_user_from_jwt(token: str) -> User:
    """Returns a User identified by id stored in JWT"""

    # sanity check
    if not token:
        return None

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

    # retrieve User by id
    return User.objects.filter(id=payload['id']).first()

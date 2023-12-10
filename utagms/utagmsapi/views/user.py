import datetime

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from utagmsapi.utils.jwt import get_user_from_jwt
from ..models import User
from ..serializers import UserSerializer


class RegisterView(APIView):
    def post(self, request):
        # check if user with this email already exists
        if User.objects.filter(email=request.data.get('email')).exists():
            raise ValidationError("User already exists!")

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed("User not found!")

        if not check_password(password, user.password):
            raise AuthenticationFailed("Incorrect password!")

        # create a token
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
            'iat': datetime.datetime.now()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # create a refresh token
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.now()
        }
        refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        response = Response({'message': 'authenticated'})
        response.set_cookie(
            key='access_token',
            value=token,
            httponly=True,
            secure=False if settings.DEBUG else True,
            samesite='lax' if settings.DEBUG else 'none'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            max_age=datetime.timedelta(days=30),
            secure=False if settings.DEBUG else True,
            samesite='lax' if settings.DEBUG else 'none'
        )

        return response


class UserView(APIView):
    def get(self, request):
        token = request.COOKIES.get('access_token')

        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            raise AuthenticationFailed('Unauthenticated!')

        if user is None:
            raise AuthenticationFailed('Unauthenticated!')

        serializer = UserSerializer(user)

        return Response(serializer.data)


class RefreshView(APIView):
    def get(self, request):
        token = request.COOKIES.get('refresh_token')

        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            raise AuthenticationFailed('Unauthenticated!')

        if user is None:
            raise AuthenticationFailed('Unauthenticated!')

        # create a token
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
            'iat': datetime.datetime.now()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # create a refresh token
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.now()
        }
        refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # create the response with tokens in cookies
        response = Response({'message': 'authenticated'})
        response.set_cookie(
            key='access_token',
            value=token,
            httponly=True,
            secure=False if settings.DEBUG else True,
            samesite='lax' if settings.DEBUG else 'none'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            max_age=datetime.timedelta(days=30),
            secure=False if settings.DEBUG else True,
            samesite='lax' if settings.DEBUG else 'none'
        )
        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.data = {
            'message': 'success'
        }
        return response

import datetime

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import generics
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from utagmsapi.utils.jwt import get_user_from_jwt
from .models import (
    User,
    Project,
    Criterion,
    Alternative,
    Performance,
    CriterionFunction,
    HasseGraph
)
from .permissions import (
    IsOwnerOfProject,
    IsLogged,
    IsOwnerOfCriterion,
    IsOwnerOfAlternative,
    IsOwnerOfPerformance
)
from .serializers import (
    UserSerializer,
    ProjectSerializer,
    CriterionSerializer,
    AlternativeSerializer,
    PerformanceSerializer,
    CriterionFunctionSerializer,
    HasseGraphSerializer, PerformanceSerializerUpdate
)


# User
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

        response = Response({
            'message': 'authenticated'
        })
        response.set_cookie(key='access_token', value=token, httponly=True)
        response.set_cookie(key='refresh_token', value=refresh_token, httponly=True,
                            max_age=datetime.timedelta(days=30))

        return response


class UserView(APIView):
    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')

        # sanity check
        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        # check to see if there is a word Bearer
        if token.split()[0] != "Bearer":
            raise AuthenticationFailed('Wrong authentication method!')

        # get jwt token
        token = token.split()[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
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
        response = Response({
            'message': 'authenticated'
        })
        response.set_cookie(key='access_token', value=token, httponly=True)
        response.set_cookie(key='refresh_token', value=refresh_token, httponly=True,
                            max_age=datetime.timedelta(days=30))
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
        serializer.save(user=get_user_from_jwt(self.request.COOKIES.get('access_token')))


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    lookup_url_kwarg = 'project_pk'


# Criterion
class CriterionList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = CriterionSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_pk")
        criteria = Criterion.objects.filter(project=project_id)
        return criteria

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_pk")
        project = Project.objects.filter(id=project_id).first()
        serializer.save(project=project)


class CriterionDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfCriterion]
    serializer_class = CriterionSerializer
    queryset = Criterion.objects.all()
    lookup_url_kwarg = 'criterion_pk'


# Alternative
class AlternativeList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = AlternativeSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_pk")
        alternatives = Alternative.objects.filter(project=project_id)
        return alternatives

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_pk")
        project = Project.objects.filter(id=project_id).first()
        serializer.save(project=project)


class AlternativeDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfAlternative]
    serializer_class = AlternativeSerializer
    queryset = Alternative.objects.all()
    lookup_url_kwarg = 'alternative_pk'


# Performance
class PerformanceList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfAlternative]
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        alternative_id = self.kwargs.get("alternative_pk")
        performances = Performance.objects.filter(alternative=alternative_id)
        return performances

    def perform_create(self, serializer):

        # get alternative
        alternative_id = self.kwargs.get("alternative_pk")
        alternative = Alternative.objects.filter(id=alternative_id).first()

        # get criterion
        criterion = serializer.validated_data.get('criterion')

        # check if alternative and criterion are in the same project
        if criterion.project != alternative.project:
            raise ValidationError({"details": "alternative and criterion do not belong to the same project"})

        # check if there exists a performance with this alternative and criterion
        performance = Performance.objects.filter(alternative=alternative).filter(criterion=criterion).first()
        if performance:
            raise ValidationError({"details": "performance for this alternative and criterion already exists"})

        # save the performance
        serializer.save(alternative=alternative)


class PerformanceDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfPerformance]
    serializer_class = PerformanceSerializerUpdate
    queryset = Performance.objects.all()
    lookup_url_kwarg = 'performance_pk'


# CriterionFunction
class CriterionFunctionList(generics.ListCreateAPIView):
    queryset = CriterionFunction.objects.all()
    serializer_class = CriterionFunctionSerializer


class CriterionFunctionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CriterionFunction.objects.all()
    serializer_class = CriterionFunctionSerializer


# HasseGraph
class HasseGraphList(generics.ListCreateAPIView):
    queryset = HasseGraph.objects.all()
    serializer_class = HasseGraphSerializer


class HasseGraphDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = HasseGraph.objects.all()
    serializer_class = HasseGraphSerializer

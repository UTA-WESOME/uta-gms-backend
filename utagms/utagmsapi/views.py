import datetime

import jwt
import _io
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from utagmsengine.solver import Solver
from utagmsengine.parser import Parser

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
    HasseGraphSerializer,
    PerformanceSerializerUpdate
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


class ProjectUpdate(APIView):
    permission_classes = [IsOwnerOfProject]

    def patch(self, request, *args, **kwargs):
        data = request.data
        project_id = kwargs.get("project_pk")
        project = Project.objects.filter(id=project_id).first()

        criteria_data = data.get("criteria", [])
        alternatives_data = data.get("alternatives", [])

        # Criteria
        # if there are criteria that were not in the payload, we delete them
        criteria_ids_db = project.criteria.values_list('id', flat=True)
        criteria_ids_request = [criterion_data.get('id') for criterion_data in criteria_data]
        criteria_ids_to_delete = set(criteria_ids_db) - set(criteria_ids_request)
        project.criteria.filter(id__in=criteria_ids_to_delete).delete()

        # if there exists a criterion with provided ID in the project, we update it
        # if there does not exist a criterion with provided ID in the project, we insert it (with a new id)
        for criterion_data in criteria_data:
            criterion_id = criterion_data.get('id')

            try:
                criterion = project.criteria.get(id=criterion_id)
                criterion_serializer = CriterionSerializer(criterion, data=criterion_data)
            except Criterion.DoesNotExist:
                criterion_serializer = CriterionSerializer(data=criterion_data)

            if criterion_serializer.is_valid():
                criterion = criterion_serializer.save(project=project)

                # update criterion id in performances
                for alternative_data in alternatives_data:
                    performances_data = alternative_data.get('performances', [])
                    for performance_data in performances_data:
                        if performance_data.get('criterion', -1) == criterion_id:
                            performance_data['criterion'] = criterion.id

        # Alternatives
        # if there are alternatives that were not in the payload, we delete them
        alternatives_ids_db = project.alternatives.values_list('id', flat=True)
        alternatives_ids_request = [alternative_data.get('id') for alternative_data in alternatives_data]
        alternatives_ids_to_delete = set(alternatives_ids_db) - set(alternatives_ids_request)
        project.alternatives.filter(id__in=alternatives_ids_to_delete).delete()

        # if there exists an alternative with provided ID in the project, we update it
        # if there does not exist an alternative with provided ID in the project, we insert it (with a new id)
        for alternative_data in alternatives_data:
            alternative_id = alternative_data.get('id')

            try:
                alternative = project.alternatives.get(id=alternative_id)
                alternative_serializer = AlternativeSerializer(alternative, data=alternative_data)
            except Alternative.DoesNotExist:
                alternative_serializer = AlternativeSerializer(data=alternative_data)

            if alternative_serializer.is_valid():
                alternative = alternative_serializer.save(project=project)

                # Performances for this alternative
                performances_data = alternative_data.get('performances', [])
                for performance_data in performances_data:
                    performance_id = performance_data.get('id')

                    try:
                        performance = alternative.performances.get(id=performance_id)
                        performance_serializer = PerformanceSerializer(performance, data=performance_data)
                    except Performance.DoesNotExist:
                        performance_serializer = PerformanceSerializer(data=performance_data)

                    if performance_serializer.is_valid():
                        performance_serializer.save(alternative=alternative)
                    else:
                        print(f'{performance_serializer=}')

        return Response({"message": "Data updated successfully"})


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


# FileUpload
@csrf_exempt
def parse_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        parser = Parser()
        uploaded_file_text = _io.TextIOWrapper(uploaded_file, encoding='utf-8')

        alternatives_id_list = parser.get_alternatives_id_list_csv(uploaded_file_text)
        type_of_criterion = parser.get_criteria_csv(uploaded_file_text)
        performance_table_list = parser.get_performance_table_list_csv(uploaded_file_text)

        print(alternatives_id_list)
        print(type_of_criterion)
        print(performance_table_list)

        return JsonResponse({'message': 'File uploaded successfully'})

    return JsonResponse({'message': 'No file selected or invalid request'}, status=400)

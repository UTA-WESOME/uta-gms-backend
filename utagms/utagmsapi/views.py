import datetime

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import generics
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from utagmsengine.solver import Solver

from utagmsapi.utils.jwt import get_user_from_jwt
from .models import (
    User,
    Project,
    Criterion,
    Alternative,
    Performance,
    CriterionFunction,
    HasseGraph,
    PreferenceIntensity
)
from .permissions import (
    IsOwnerOfProject,
    IsLogged,
    IsOwnerOfCriterion,
    IsOwnerOfAlternative,
    IsOwnerOfPerformance,
    IsOwnerOfPreferenceIntensity
)
from .serializers import (
    UserSerializer,
    ProjectSerializer,
    CriterionSerializer,
    AlternativeSerializer,
    PerformanceSerializer,
    CriterionFunctionSerializer,
    HasseGraphSerializer,
    PerformanceSerializerUpdate,
    PreferenceIntensitySerializer
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
        pref_intensities_data = data.get("preference_intensities", [])

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

                # update criterion id in preference intensities
                for pref_intensity_data in pref_intensities_data:
                    if pref_intensity_data.get('criterion', -1) == criterion_id:
                        pref_intensity_data['criterion'] = criterion.id

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

                # update alternatives id in preference intensities
                for pref_intensity_data in pref_intensities_data:
                    for alternative_number in range(1, 5):
                        if pref_intensity_data.get(f'alternative_{alternative_number}', -1) == alternative_id:
                            pref_intensity_data[f'alternative_{alternative_number}'] = alternative.id

        # Preference intensities
        # if there are preference intensities that were not in the payload, we delete them
        pref_intensities_ids_db = project.preference_intensities.values_list('id', flat=True)
        pref_intensities_ids_request = [pref_intensity_data.get('id') for pref_intensity_data in pref_intensities_data]
        pref_intensities_ids_to_delete = set(pref_intensities_ids_db) - set(pref_intensities_ids_request)
        project.preference_intensities.filter(id__in=pref_intensities_ids_to_delete).delete()

        # if there exists a preference_intensity with provided ID in the project, we update it
        # if there does not exist a preference_intensity with provided ID in the project, we insert it (with a new id)
        for pref_intensity_data in pref_intensities_data:
            pref_intensity_id = pref_intensity_data.get('id')

            try:
                pref_intensity = project.preference_intensities.get(id=pref_intensity_id)
                pref_intensity_serializer = PreferenceIntensitySerializer(pref_intensity, data=pref_intensity_data)
            except PreferenceIntensity.DoesNotExist:
                pref_intensity_serializer = PreferenceIntensitySerializer(data=pref_intensity_data)

            if pref_intensity_serializer.is_valid():
                pref_intensity_serializer.save(project=project)

        return Response({"message": "Data updated successfully"})


class ProjectResults(APIView):
    permission_classes = [IsOwnerOfProject]

    def post(self, request, *args, **kwargs):
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()

        # get gain
        gain_list = Criterion.objects.filter(project=project).order_by('id').values_list('gain', flat=True)
        gain_list = [1 if gain else 0 for gain in gain_list]

        # get weights and normalize them
        weights_list = Criterion.objects.filter(project=project).order_by('id').values_list('weight', flat=True)
        weights_list = [weight / sum(weights_list) for weight in weights_list]

        # get alternatives
        alternatives = Alternative.objects.filter(project=project).order_by('id')
        alternatives_id_list = [str(_id) for _id in
                                Alternative.objects.filter(project=project).order_by('id').values_list('id', flat=True)]

        # get performances
        performances_table = []
        for alternative in alternatives:
            performances = Performance.objects\
                .filter(alternative=alternative)\
                .order_by('criterion_id')\
                .values_list('value', flat=True)
            performances_table.append(performances)

        # get preferences and indifferences
        # first, we get unique reference_ranking values and sort it
        ref_ranking_unique_values = set(Alternative.objects
                                        .filter(project=project)
                                        .values_list('reference_ranking', flat=True)
                                        )
        ref_ranking_unique_list_sorted = sorted(ref_ranking_unique_values)

        preferences_list = []
        indifferences_list = []
        # now we need to check every alternative and find other alternatives that are below this alternative in
        # reference_ranking
        for i_alternative_1, alternative_1 in enumerate(alternatives):

            # 0 in reference_ranking means that it was not placed in the reference ranking
            if alternative_1.reference_ranking == 0:
                continue

            ref_ranking_index = ref_ranking_unique_list_sorted.index(alternative_1.reference_ranking)
            if ref_ranking_index < len(ref_ranking_unique_list_sorted) - 1:
                for i_alternative_2, alternative_2 in enumerate(alternatives):

                    if i_alternative_1 == i_alternative_2:
                        continue

                    if alternative_2.reference_ranking == ref_ranking_unique_list_sorted[ref_ranking_index + 1]:
                        preferences_list.append([i_alternative_1, i_alternative_2])

                    if alternative_2.reference_ranking == ref_ranking_unique_list_sorted[ref_ranking_index]:
                        indifferences_list.append([i_alternative_1, i_alternative_2])

        solver = Solver()

        ranking = solver.get_ranking_dict(
            performances_table,
            alternatives_id_list,
            preferences_list,
            indifferences_list,
            weights_list,
            gain_list,
        )

        # updating alternatives with ranking values
        for i, (key, value) in enumerate(sorted(ranking.items(), key=lambda x: -x[1]), start=1):
            alternative = Alternative.objects.filter(id=int(key)).first()
            alternative.ranking = i
            alternative.save()

        alternatives = Alternative.objects.filter(project=project)
        serializer = AlternativeSerializer(alternatives, many=True)

        return Response(serializer.data)


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


# PreferenceIntensity
class PreferenceIntensityList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = PreferenceIntensitySerializer

    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        preference_intensities = PreferenceIntensity.objects.filter(project=project_id)
        return preference_intensities

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        serializer.save(project=project)


class PreferenceIntensityDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfPreferenceIntensity]
    serializer_class = PreferenceIntensitySerializer
    queryset = PreferenceIntensity.objects.all()
    lookup_url_kwarg = 'preference_intensity_pk'

import _io
import datetime
from builtins import Exception

import jwt
import utagmsengine.dataclasses as uged
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import transaction
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from utagmsengine.parser import Parser
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
    PreferenceIntensity,
    PairwiseComparison
)
from .permissions import (
    IsOwnerOfProject,
    IsLogged,
    IsOwnerOfCriterion,
    IsOwnerOfAlternative,
    IsOwnerOfPerformance,
    IsOwnerOfPreferenceIntensity,
    IsOwnerOfPairwiseComparison
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
    PreferenceIntensitySerializer,
    ProjectSerializerWhole,
    PairwiseComparisonSerializer
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


class ProjectBatch(APIView):
    permission_classes = [IsOwnerOfProject]

    def get(self, request, *args, **kwargs):
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)

    def patch(self, request, *args, **kwargs):
        data = request.data
        project_id = kwargs.get("project_pk")
        project = Project.objects.filter(id=project_id).first()

        # set project's comparisons mode
        pairwise_mode_data = data.get("pairwise_mode", False)
        project.pairwise_mode = pairwise_mode_data
        project.save()

        # get data from request
        criteria_data = data.get("criteria", [])
        alternatives_data = data.get("alternatives", [])
        pref_intensities_data = data.get("preference_intensities", [])
        pairwise_comparisons_data = data.get("pairwise_comparisons", [])

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
                        performance_serializer = PerformanceSerializerUpdate(performance, data=performance_data)
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

        # Pairwise Comparisons
        # if there are pairwise comparisons that were not in the payload, we delete them
        pairwise_comparisons_ids_db = project.pairwise_comparisons.values_list('id', flat=True)
        pairwise_comparisons_ids_request = [pc_data.get('id') for pc_data in pairwise_comparisons_data]
        pairwise_comparisons_idb_to_delete = set(pairwise_comparisons_ids_db) - set(pairwise_comparisons_ids_request)
        project.pairwise_comparisons.filter(id__in=pairwise_comparisons_idb_to_delete).delete()

        # if there exists a pairwise_comparison with provided ID in the project, we update it
        # if there does not exist a pairwise_comparison with provided ID in the project, we insert it (with a new id)
        for pairwise_comparison_data in pairwise_comparisons_data:
            pairwise_comparison_id = pairwise_comparison_data

            try:
                pairwise_comparison = project.pairwise_comparisons.get(id=pairwise_comparison_id)
                pairwise_comparison_serializer = PairwiseComparisonSerializer(pairwise_comparison,
                                                                              data=pairwise_comparison_data)
            except PairwiseComparison.DoesNotExist:
                pairwise_comparison_serializer = PairwiseComparisonSerializer(data=pairwise_comparison_data)

            if pairwise_comparison_serializer.is_valid():
                pairwise_comparison_serializer.save(project=project)

        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)


class ProjectResults(APIView):
    permission_classes = [IsOwnerOfProject]

    def post(self, request, *args, **kwargs):
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()

        # get sum of the criteria weights
        weights_sum = sum(Criterion.objects.filter(project=project).order_by('id').values_list('weight', flat=True))

        # get criteria
        criteria = [uged.Criterion(criterion_id=str(c.id), weight=c.weight / weights_sum, gain=c.gain)
                    for c in Criterion.objects.filter(project=project)]

        # get alternatives
        alternatives = Alternative.objects.filter(project=project)

        # get performance_table_list
        performances = {}
        for alternative in alternatives:
            performances[str(alternative.id)] = {
                str(criterion_id): value for criterion_id, value in
                Performance.objects.filter(alternative=alternative).values_list('criterion', 'value')
            }

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
        for alternative_1 in alternatives:

            # 0 in reference_ranking means that it was not placed in the reference ranking
            if alternative_1.reference_ranking == 0:
                continue

            # we have to get the index of the current alternative's reference ranking
            ref_ranking_index = ref_ranking_unique_list_sorted.index(alternative_1.reference_ranking)
            if ref_ranking_index < len(ref_ranking_unique_list_sorted) - 1:
                for alternative_2 in alternatives:

                    if alternative_1.id == alternative_2.id:
                        continue

                    if alternative_2.reference_ranking == ref_ranking_unique_list_sorted[ref_ranking_index + 1]:
                        preferences_list.append(uged.Preference(
                            superior=str(alternative_1.id), inferior=str(alternative_2.id)
                        ))

                    if alternative_2.reference_ranking == ref_ranking_unique_list_sorted[ref_ranking_index]:
                        indifferences_list.append(uged.Indifference(
                            equal1=str(alternative_1.id), equal2=str(alternative_2.id)
                        ))

        solver = Solver()
        ranking = solver.get_ranking_dict(
            performances,
            preferences_list,
            indifferences_list,
            criteria,
        )

        # updating alternatives with ranking values
        for i, (key, value) in enumerate(sorted(ranking.items(), key=lambda x: -x[1]), start=1):
            alternative = Alternative.objects.filter(id=int(key)).first()
            alternative.ranking = i
            alternative.save()

        hasse_graph = solver.get_hasse_diagram_dict(
            performances,
            preferences_list,
            indifferences_list,
            criteria
        )

        # change data to integer ids and to list
        hasse_graph = {int(key): [int(value) for value in values] for key, values in hasse_graph.items()}
        project.hasse_graph = hasse_graph
        project.save()

        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)


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
        alternative_id = self.kwargs.get('alternative_pk')
        alternative = Alternative.objects.filter(id=alternative_id).first()
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


class PairwiseComparisonList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = PairwiseComparisonSerializer

    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        pairwise_comparisons = PairwiseComparison.objects.filter(project=project_id)
        return pairwise_comparisons

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        serializer.save(project=project)


class PairwiseComparisonDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfPairwiseComparison]
    serializer_class = PairwiseComparisonSerializer
    queryset = PairwiseComparison.objects.all()
    lookup_url_kwarg = 'pairwise_comparison'


# FileUpload
class FileUpload(APIView):
    permission_classes = [IsOwnerOfProject]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if request.FILES.get('file'):
            uploaded_file = request.FILES['file']
            uploaded_file_text = _io.TextIOWrapper(uploaded_file, encoding='utf-8')
            project_id = kwargs.get('project_pk')
            project = Project.objects.filter(id=project_id).first()

            # deleting previous data
            curr_alternatives = Alternative.objects.filter(project=project)
            curr_criteria = Criterion.objects.filter(project=project)
            curr_alternatives.delete()
            curr_criteria.delete()

            try:
                parser = Parser()
                criterion_list = parser.get_criterion_list_csv(uploaded_file_text)
                uploaded_file_text.seek(0)
                performance_table_list = parser.get_performance_table_dict_csv(uploaded_file_text)
            except Exception as e:
                return Response({'message': 'Incorrect file: {}'.format(str(e))},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # criteria
            for criterion in criterion_list:
                criterion_data = {
                    'name': criterion.criterion_id,
                    'gain': criterion.gain,
                    'linear_segments': 0,
                }

                criterion_serializer = CriterionSerializer(data=criterion_data)
                if criterion_serializer.is_valid():
                    criterion_serializer.save(project=project)

            # alternatives
            for alternative in performance_table_list.keys():
                alternative_data = {
                    'name': alternative,
                    'reference_ranking': 0,
                    'ranking': 0,
                }

                alternative_serializer = AlternativeSerializer(data=alternative_data)
                if alternative_serializer.is_valid():
                    alternative_serializer.save(project=project)

            # performances
            criteria = Criterion.objects.all().filter(project=project)
            alternatives = Alternative.objects.all().filter(project=project)
            for alternative_name, alternative_data in performance_table_list.items():
                alternative = alternatives.get(name=alternative_name)
                for criterion_name, value in alternative_data.items():
                    criterion = criteria.get(name=criterion_name)
                    performance_data = {
                        'criterion': criterion.pk,
                        'value': value,
                        'ranking': 0,
                    }
                    performance_serializer = PerformanceSerializer(data=performance_data)
                    if performance_serializer.is_valid():
                        performance_serializer.save(alternative=alternative)

            return Response({'message': 'File uploaded successfully'})

        return Response({'message': 'No file selected or invalid request'}, status=status.HTTP_400_BAD_REQUEST)

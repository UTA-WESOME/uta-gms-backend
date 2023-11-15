import _io
import datetime
from builtins import Exception

import jwt
import utagmsengine.dataclasses as uged
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Count, Q
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
    FunctionPoint,
    PreferenceIntensity,
    PairwiseComparison,
    Category,
    CriterionCategory,
    Ranking
)
from .permissions import (
    IsOwnerOfProject,
    IsLogged,
    IsOwnerOfCriterion,
    IsOwnerOfAlternative,
    IsOwnerOfPerformance,
    IsOwnerOfPreferenceIntensity,
    IsOwnerOfPairwiseComparison,
    IsOwnerOfCategory,
    IsOwnerOfCriterionCategory,
    IsOwnerOfRanking
)
from .serializers import (
    UserSerializer,
    ProjectSerializer,
    CriterionSerializer,
    AlternativeSerializer,
    PerformanceSerializer,
    PerformanceSerializerUpdate,
    PreferenceIntensitySerializer,
    ProjectSerializerWhole,
    PairwiseComparisonSerializer,
    FunctionPointSerializer,
    CategorySerializer,
    CriterionCategorySerializer,
    RankingSerializer
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
        categories_data = data.get("categories", [])
        preference_intensities_data = data.get("preference_intensities", [])

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

                # update criterion id in preference_intensities
                for pref_intensity_data in preference_intensities_data:
                    if pref_intensity_data.get('criterion', -1) == criterion_id:
                        pref_intensity_data['criterion'] = criterion.id

                for category_data in categories_data:
                    # update criterion id in criterion_categories
                    criterion_categories_data = category_data.get('criterion_categories', [])
                    for criterion_category_data in criterion_categories_data:
                        if criterion_category_data.get('criterion', -1) == criterion_id:
                            criterion_category_data['criterion'] = criterion.id

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

                # Performances
                performances_data = alternative_data.get('performances', [])

                # it may happen that the user had an alternative with id=1, deleted it and added a new one with id=1
                # and the performances were not deleted in cascade, so we need to delete them manually because the new
                # ones do not have an id in the payload, and they would raise a ValidationError in the serializer
                performances_ids_db = alternative.performances.values_list('id', flat=True)
                performances_ids_request = [performance_data.get('id', -1) for performance_data in performances_data]
                performances_ids_to_delete = set(performances_ids_db) - set(performances_ids_request)
                alternative.performances.filter(id__in=performances_ids_to_delete).delete()

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
                for pref_intensity_data in preference_intensities_data:
                    for alternative_number in range(1, 5):
                        if pref_intensity_data.get(f'alternative_{alternative_number}', -1) == alternative_id:
                            pref_intensity_data[f'alternative_{alternative_number}'] = alternative.id

                for category_data in categories_data:
                    # update alternative id in pairwise comparisons
                    pairwise_comparisons_data = category_data.get('pairwise_comparisons', [])
                    for pairwise_comparison_data in pairwise_comparisons_data:
                        if pairwise_comparison_data.get('alternative_1', -1) == alternative_id:
                            pairwise_comparison_data['alternative_1'] = alternative.id
                        if pairwise_comparison_data.get('alternative_2', -1) == alternative_id:
                            pairwise_comparison_data['alternative_2'] = alternative.id

                    # update alternative id in ranking
                    rankings_data = category_data.get('rankings', [])
                    for ranking_data in rankings_data:
                        if ranking_data.get('alternative', -1) == alternative_id:
                            ranking_data['alternative'] = alternative.id

        # Categories
        # if there are categories that were not in the payload, we delete them
        categories_ids_db = project.categories.values_list('id', flat=True)
        categories_ids_request = [category_data.get('id') for category_data in categories_data]
        categories_ids_to_delete = set(categories_ids_db) - set(categories_ids_request)
        project.categories.filter(id__in=categories_ids_to_delete).delete()

        # if there exists a category with provided ID in the project, we update it
        # if there does not exist a category with provided ID in the project, we insert it (with a new id)
        for category_data in categories_data:
            category_id = category_data.get('id')

            try:
                category = project.categories.get(id=category_id)
                category_serializer = CategorySerializer(category, data=category_data)
            except Category.DoesNotExist:
                category_serializer = CategorySerializer(data=category_data)

            if category_serializer.is_valid():
                category = category_serializer.save(project=project)

                # CriterionCategories
                ccs_data = category_data.get('criterion_categories', [])

                ccs_ids_db = category.criterion_categories.values_list('id', flat=True)
                ccs_ids_request = [cc_data.get('id') for cc_data in ccs_data]
                ccs_ids_to_delete = set(ccs_ids_db) - set(ccs_ids_request)
                category.criterion_categories.filter(id__in=ccs_ids_to_delete).delete()

                for cc_data in ccs_data:
                    cc_id = cc_data.get('id')
                    try:
                        criterion_category = category.criterion_categories.get(id=cc_id)
                        cc_serializer = CriterionCategorySerializer(criterion_category, data=cc_data)
                    except CriterionCategory.DoesNotExist:
                        cc_serializer = CriterionCategorySerializer(data=cc_data)
                    if cc_serializer.is_valid():
                        cc_serializer.save(category=category)

                # Pairwise Comparisons
                pairwise_comparisons_data = category_data.get('pairwise_comparisons', [])
                pairwise_comparisons_ids_db = category.pairwise_comparisons.values_list('id', flat=True)
                pairwise_comparisons_ids_request = [pc_data.get('id') for pc_data in pairwise_comparisons_data]
                pairwise_comparisons_ids_to_delete = (
                        set(pairwise_comparisons_ids_db) - set(pairwise_comparisons_ids_request)
                )
                category.pairwise_comparisons.filter(id__in=pairwise_comparisons_ids_to_delete).delete()
                for pairwise_comparison_data in pairwise_comparisons_data:
                    pairwise_comparison_id = pairwise_comparison_data.get('id')
                    try:
                        pairwise_comparison = category.pairwise_comparisons.get(id=pairwise_comparison_id)
                        pairwise_comparison_serializer = PairwiseComparisonSerializer(pairwise_comparison,
                                                                                      data=pairwise_comparison_data)
                    except PairwiseComparison.DoesNotExist:
                        pairwise_comparison_serializer = PairwiseComparisonSerializer(data=pairwise_comparison_data)
                    if pairwise_comparison_serializer.is_valid():
                        pairwise_comparison_serializer.save(category=category)

                # Rankings
                rankings_data = category_data.get('rankings', [])
                rankings_ids_db = category.rankings.values_list('id', flat=True)
                rankings_ids_request = [ranking_data.get('id') for ranking_data in rankings_data]
                rankings_ids_to_delete = set(rankings_ids_db) - set(rankings_ids_request)
                category.rankings.filter(id__in=rankings_ids_to_delete).delete()
                for ranking_data in rankings_data:
                    ranking_id = ranking_data.get('id')
                    try:
                        ranking = category.rankings.get(id=ranking_id)
                        ranking_serializer = RankingSerializer(ranking, data=ranking_data)
                    except Ranking.DoesNotExist:
                        ranking_serializer = RankingSerializer(data=ranking_data)
                    if ranking_serializer.is_valid():
                        ranking_serializer.save(category=category)

                # update criterion id in preference_intensities
                for pref_intensity_data in preference_intensities_data:
                    if pref_intensity_data.get('category', -1) == category_id:
                        pref_intensity_data['category'] = category.id

        # reset the hasse_graphs
        for category in Category.objects.filter(project=project):
            category.hasse_graph = {}
            category.save()

        # Preference Intensities
        pref_intensities_ids_db = project.preference_intensities.values_list('id', flat=True)
        pref_intensities_ids_request = [pref_intensity_data.get('id')
                                        for pref_intensity_data in preference_intensities_data]
        pref_intensities_ids_to_delete = set(pref_intensities_ids_db) - set(pref_intensities_ids_request)
        project.preference_intensities.filter(id__in=pref_intensities_ids_to_delete).delete()

        for pref_intensity_data in preference_intensities_data:
            pref_intensity_id = pref_intensity_data.get('id')
            try:
                pref_intensity = project.preference_intensities.get(id=pref_intensity_id)
                pref_intensity_serializer = PreferenceIntensitySerializer(pref_intensity,
                                                                          data=pref_intensity_data)
            except PreferenceIntensity.DoesNotExist:
                pref_intensity_serializer = PreferenceIntensitySerializer(data=pref_intensity_data)
            if pref_intensity_serializer.is_valid():
                pref_intensity_serializer.save(project=project)

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
        criteria_uged = [
            uged.Criterion(criterion_id=str(c.id), number_of_linear_segments=c.linear_segments, gain=c.gain)
            for c in Criterion.objects.filter(project=project)
            .annotate(active_category_count=Count('criterion_categories__category',
                                                  filter=Q(criterion_categories__category__active=True)))
            .annotate(criterion_categories_count=Count('criterion_categories'))
            .filter(Q(active_category_count__gt=0) | Q(criterion_categories_count=0))
        ]

        # sanity check: we need at least one criterion
        if len(criteria_uged) == 0:
            return Response({"details": "There are no active criteria! Please make at least one category active."},
                            status=status.HTTP_400_BAD_REQUEST)

        # get alternatives
        alternatives = Alternative.objects.filter(project=project)

        # get performance_table_list
        # we need performances only from criteria that have at least one category marked as active or no categories
        performances = {}
        for alternative in alternatives:
            performances[str(alternative.id)] = {
                str(criterion_id): value for criterion_id, value in
                Performance.objects
                .filter(alternative=alternative)
                .annotate(active_category_count=Count('criterion__criterion_categories__category',
                                                      filter=Q(criterion__criterion_categories__category__active=True)))
                .annotate(criterion_categories_count=Count('criterion__criterion_categories'))
                .filter(Q(active_category_count__gt=0) | Q(criterion_categories_count=0))
                .values_list('criterion', 'value')
            }

        # get preferences and indifferences
        preferences_list = []
        indifferences_list = []
        # we need to check if the project uses reference ranking or pairwise comparisons
        if project.pairwise_mode:
            for pairwise_comparison in PairwiseComparison.objects.filter(project=project):
                if pairwise_comparison.type == PairwiseComparison.PREFERENCE:
                    preferences_list.append(uged.Preference(
                        superior=str(pairwise_comparison.alternative_1.id),
                        inferior=str(pairwise_comparison.alternative_2.id)
                    ))
                if pairwise_comparison.type == PairwiseComparison.INDIFFERENCE:
                    indifferences_list.append(uged.Indifference(
                        equal1=str(pairwise_comparison.alternative_1.id),
                        equal2=str(pairwise_comparison.alternative_2.id)
                    ))
        else:
            # first, we get unique reference_ranking values and sort it
            ref_ranking_unique_values = set(
                Alternative.objects
                .filter(project=project)
                .values_list('reference_ranking', flat=True)
            )
            ref_ranking_unique_list_sorted = sorted(ref_ranking_unique_values)
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

        # get best-worst positions
        best_worst_positions = []
        alternatives_count = Alternative.objects.filter(project=project).count()
        for alternative in Alternative.objects.filter(project=project):
            if alternative.best_position is not None and alternative.worst_position is not None:
                best_worst_positions.append(uged.Position(alternative_id=str(alternative.id),
                                                          worst_position=alternative.worst_position,
                                                          best_position=alternative.best_position))
            elif alternative.best_position is not None:
                best_worst_positions.append(uged.Position(alternative_id=str(alternative.id),
                                                          worst_position=alternatives_count,
                                                          best_position=alternative.best_position))
            elif alternative.worst_position is not None:
                best_worst_positions.append(uged.Position(alternative_id=str(alternative.id),
                                                          worst_position=alternative.worst_position,
                                                          best_position=1))

        # RANKING
        solver = Solver()
        ranking, functions, samples = solver.get_representative_value_function_dict(
            performances,
            preferences_list,
            indifferences_list,
            criteria_uged,
            best_worst_positions,
            '/sampler/polyrun-1.1.0-jar-with-dependencies.jar',
            '10'
        )

        print(samples)

        # updating alternatives with ranking values
        for i, (key, value) in enumerate(sorted(ranking.items(), key=lambda x: -x[1]), start=1):
            alternative = Alternative.objects.filter(id=int(key)).first()
            alternative.ranking = i
            alternative.ranking_value = value
            alternative.save()

        # updating criterion functions
        for criterion_id, function in functions.items():
            criterion = Criterion.objects.get(id=int(criterion_id))
            criterion_function_points = FunctionPoint.objects.filter(criterion=criterion)
            criterion_function_points.delete()

            for x, y in function:
                point = FunctionPointSerializer(data={
                    'ordinate': y,
                    'abscissa': x,
                })
                if point.is_valid():
                    point.save(criterion=criterion)

        # HASSE GRAPH
        hasse_graph = solver.get_hasse_diagram_dict(
            performances,
            preferences_list,
            indifferences_list,
            criteria_uged,
            best_worst_positions
        )

        # change data to integer ids and to list
        hasse_graph = {int(key): [int(value) for value in values] for key, values in hasse_graph.items()}
        project.hasse_graph = hasse_graph
        project.save()

        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)


# Category
class CategoryList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = CategorySerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_pk")
        categories = Category.objects.filter(project=project_id)
        return categories

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_pk")
        project = Project.objects.filter(id=project_id).first()
        serializer.save(project=project)


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfCategory]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    lookup_url_kwarg = 'category_pk'


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


# CriterionCategory
class CriterionCategoryList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfCategory]
    serializer_class = CriterionCategorySerializer

    def get_queryset(self):
        category_id = self.kwargs.get("category_pk")
        return CriterionCategory.objects.filter(category=category_id)

    def perform_create(self, serializer):
        category_id = self.kwargs.get("category_pk")
        serializer.save(category=Category.objects.filter(id=category_id).first())


class CriterionCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfCriterionCategory]
    serializer_class = CriterionCategorySerializer
    queryset = CriterionCategory.objects.all()
    lookup_url_kwarg = 'criterion_category_pk'


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


# PreferenceIntensity
class PreferenceIntensityList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfProject]
    serializer_class = PreferenceIntensitySerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_pk")
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
    permission_classes = [IsOwnerOfCategory]
    serializer_class = PairwiseComparisonSerializer

    def get_queryset(self):
        category_id = self.kwargs.get("category_pk")
        pairwise_comparisons = PairwiseComparison.objects.filter(category=category_id)
        return pairwise_comparisons

    def perform_create(self, serializer):
        category_id = self.kwargs.get("category_pk")
        category = Category.objects.filter(id=category_id).first()
        serializer.save(category=category)


class PairwiseComparisonDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfPairwiseComparison]
    serializer_class = PairwiseComparisonSerializer
    queryset = PairwiseComparison.objects.all()
    lookup_url_kwarg = 'pairwise_comparison_pk'


class RankingList(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOfCategory]
    serializer_class = RankingSerializer

    def get_queryset(self):
        category_id = self.kwargs.get("category_pk")
        rankings = Ranking.objects.filter(category=category_id)
        return rankings

    def perform_create(self, serializer):
        category_id = self.kwargs.get("category_pk")
        category = Category.objects.filter(id=category_id).first()
        serializer.save(category=category)


class RankingDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfRanking]
    serializer_class = RankingSerializer
    queryset = Ranking.objects.all()
    lookup_url_kwarg = "ranking_pk"


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

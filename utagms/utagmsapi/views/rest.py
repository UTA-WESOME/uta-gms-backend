from rest_framework import generics

from utagmsapi.utils.jwt import get_user_from_jwt
from ..models import (
    Alternative,
    Category,
    Criterion,
    CriterionCategory,
    PairwiseComparison,
    Performance,
    PreferenceIntensity,
    Project,
    Ranking
)
from ..permissions import (
    IsLogged,
    IsOwnerOfAlternative,
    IsOwnerOfCategory,
    IsOwnerOfCriterion,
    IsOwnerOfCriterionCategory,
    IsOwnerOfPairwiseComparison,
    IsOwnerOfPerformance,
    IsOwnerOfPreferenceIntensity,
    IsOwnerOfProject,
    IsOwnerOfRanking
)
from ..serializers import (
    AlternativeSerializer,
    CategorySerializer,
    CriterionCategorySerializer,
    CriterionSerializer,
    PairwiseComparisonSerializer,
    PerformanceSerializer,
    PerformanceSerializerUpdate,
    PreferenceIntensitySerializer,
    ProjectSerializer,
    RankingSerializer
)


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

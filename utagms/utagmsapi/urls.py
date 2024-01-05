from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from utagmsapi.views.batch import CategoryResults, ProjectBatch
from utagmsapi.views.files import CsvExport, FileUpload, XmlExport
from utagmsapi.views.rest import (
    AlternativeDetail,
    AlternativeList,
    CategoryDetail,
    CategoryList,
    CriterionCategoryDetail,
    CriterionCategoryList,
    CriterionDetail,
    CriterionList,
    PairwiseComparisonDetail,
    PairwiseComparisonList,
    PerformanceDetail,
    PerformanceList,
    PreferenceIntensityDetail,
    PreferenceIntensityList,
    ProjectDetail,
    ProjectList,
    RankingDetail,
    RankingList
)
from utagmsapi.views.user import LoginView, LogoutView, RefreshView, RegisterView, UserView

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('user', UserView.as_view()),
    path('logout', LogoutView.as_view()),
    path('refresh', RefreshView.as_view()),

    path('projects/', ProjectList.as_view()),
    path('projects/<int:project_pk>', ProjectDetail.as_view()),
    path('projects/<int:project_pk>/batch/', ProjectBatch.as_view()),

    path('projects/<int:project_pk>/categories/', CategoryList.as_view()),
    path('categories/<int:category_pk>', CategoryDetail.as_view()),
    path('categories/<int:category_pk>/results/', CategoryResults.as_view()),

    path('projects/<int:project_pk>/criteria/', CriterionList.as_view()),
    path('criteria/<int:criterion_pk>', CriterionDetail.as_view()),

    path('categories/<int:category_pk>/criterion_categories/', CriterionCategoryList.as_view()),
    path('criterion_categories/<int:criterion_category_pk>', CriterionCategoryDetail.as_view()),

    path('projects/<int:project_pk>/alternatives/', AlternativeList.as_view()),
    path('alternatives/<int:alternative_pk>', AlternativeDetail.as_view()),

    path('alternatives/<int:alternative_pk>/performances/', PerformanceList.as_view()),
    path('performances/<int:performance_pk>', PerformanceDetail.as_view()),

    path('projects/<int:project_pk>/preference_intensities/', PreferenceIntensityList.as_view()),
    path('preference_intensities/<int:preference_intensity_pk>', PreferenceIntensityDetail.as_view()),

    path('categories/<int:category_pk>/pairwise_comparisons/', PairwiseComparisonList.as_view()),
    path('pairwise_comparisons/<int:pairwise_comparison_pk>', PairwiseComparisonDetail.as_view()),

    path('categories/<int:category_pk>/rankings/', RankingList.as_view()),
    path('rankings/<int:ranking_pk>', RankingDetail.as_view()),

    path('projects/<int:project_pk>/upload/', FileUpload.as_view()),
    path('projects/<int:project_pk>/export_csv/', CsvExport.as_view()),
    path('projects/<int:project_pk>/export_xml/', XmlExport.as_view()),

    # YOUR PATTERNS
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

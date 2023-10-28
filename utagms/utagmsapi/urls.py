from django.urls import path

from .views import (
    ProjectList,
    ProjectDetail,
    CriterionList,
    CriterionDetail,
    AlternativeList,
    AlternativeDetail,
    PerformanceList,
    PerformanceDetail,
    RegisterView,
    LoginView,
    UserView,
    LogoutView,
    RefreshView,
    ProjectBatch,
    ProjectResults,
    PreferenceIntensityList,
    PreferenceIntensityDetail,
    FileUpload, PairwiseComparisonList, PairwiseComparisonDetail
)

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('user', UserView.as_view()),
    path('logout', LogoutView.as_view()),
    path('refresh', RefreshView.as_view()),

    path('projects/', ProjectList.as_view()),
    path('projects/<int:project_pk>', ProjectDetail.as_view()),
    path('projects/<int:project_pk>/batch', ProjectBatch.as_view()),
    path('projects/<int:project_pk>/results', ProjectResults.as_view()),

    path('projects/<int:project_pk>/criteria/', CriterionList.as_view()),
    path('criteria/<int:criterion_pk>', CriterionDetail.as_view()),

    path('projects/<int:project_pk>/alternatives/', AlternativeList.as_view()),
    path('alternatives/<int:alternative_pk>', AlternativeDetail.as_view()),

    path('alternatives/<int:alternative_pk>/performances/', PerformanceList.as_view()),
    path('performances/<int:performance_pk>', PerformanceDetail.as_view()),

    path('projects/<int:project_pk>/preference_intensities/', PreferenceIntensityList.as_view()),
    path('preference_intensities/<int:preference_intensity_pk>', PreferenceIntensityDetail.as_view()),

    path('projects/<int:project_pk>/pairwise_comparisons/', PairwiseComparisonList.as_view()),
    path('pairwise_comparisons/<int:pairwise_comparison_pk>', PairwiseComparisonDetail.as_view()),

    path('projects/<int:project_pk>/upload/', FileUpload.as_view()),
]

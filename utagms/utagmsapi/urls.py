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
    CriterionFunctionList,
    CriterionFunctionDetail,
    HasseGraphList,
    HasseGraphDetail,
    RegisterView,
    LoginView,
    UserView,
    LogoutView,
    RefreshView,
    ProjectBatch,
    ProjectResults,
    PreferenceIntensityList,
    PreferenceIntensityDetail,
    parse_file
)

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('user', UserView.as_view()),
    path('logout', LogoutView.as_view()),
    path('refresh', RefreshView.as_view()),

    path('projects/', ProjectList.as_view()),
    path('projects/<int:project_pk>', ProjectDetail.as_view()),

    path('projects/<int:project_pk>/criteria/', CriterionList.as_view()),
    path('criteria/<int:criterion_pk>', CriterionDetail.as_view()),

    path('projects/<int:project_pk>/alternatives/', AlternativeList.as_view()),
    path('alternatives/<int:alternative_pk>', AlternativeDetail.as_view()),

    path('alternatives/<int:alternative_pk>/performances/', PerformanceList.as_view()),
    path('performances/<int:performance_pk>', PerformanceDetail.as_view()),

    path('criteria_functions/', CriterionFunctionList.as_view()),
    path('criteria_functions/', CriterionFunctionDetail.as_view()),
    path('hassegraphs/', HasseGraphList.as_view()),
    path('hassegraphs/', HasseGraphDetail.as_view()),

    path('<int:project_pk>/upload/', parse_file),
]

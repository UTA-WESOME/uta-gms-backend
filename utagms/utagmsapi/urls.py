from django.urls import path

from .views import (
    UserList,
    UserDetail,
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
    HasseGraphDetail
)

urlpatterns = [
    path('users/', UserList.as_view()),
    path('users/', UserDetail.as_view()),
    path('projects/', ProjectList.as_view()),
    path('projects/', ProjectDetail.as_view()),
    path('criteria/', CriterionList.as_view()),
    path('criteria/', CriterionDetail.as_view()),
    path('alternatives/', AlternativeList.as_view()),
    path('alternatives/', AlternativeDetail.as_view()),
    path('performances/', PerformanceList.as_view()),
    path('performances/', PerformanceDetail.as_view()),
    path('criteria_functions/', CriterionFunctionList.as_view()),
    path('criteria_functions/', CriterionFunctionDetail.as_view()),
    path('hassegraphs/', HasseGraphList.as_view()),
    path('hassegraphs/', HasseGraphDetail.as_view()),
]

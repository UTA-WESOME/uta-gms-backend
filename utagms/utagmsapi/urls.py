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
    HasseGraphDetail, RegisterView, LoginView, UserView, LogoutView
)

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('user', UserView.as_view()),
    path('logout', LogoutView.as_view()),
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

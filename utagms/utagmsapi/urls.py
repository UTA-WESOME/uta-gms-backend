from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from utagmsapi.views.batch import JobCancellation, ProjectBatch, ProjectJobs, ProjectResults
from utagmsapi.views.files import CsvExport, FileUpload, XmlExport
from utagmsapi.views.rest import ProjectDetail, ProjectList
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
    path('projects/<int:project_pk>/results/', ProjectResults.as_view()),
    path('projects/<int:project_pk>/jobs/', ProjectJobs.as_view()),
    path('jobs/<int:job_pk>/cancel/', JobCancellation.as_view()),

    path('projects/<int:project_pk>/upload/', FileUpload.as_view()),
    path('projects/<int:project_pk>/export_csv/', CsvExport.as_view()),
    path('projects/<int:project_pk>/export_xml/', XmlExport.as_view()),

    # YOUR PATTERNS
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

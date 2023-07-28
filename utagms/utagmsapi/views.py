from rest_framework import generics

from .models import (
    User,
    Project,
    Criterion,
    Alternative,
    Performance,
    CriterionFunction,
    HasseGraph
)

from .serializers import (
    UserSerializer,
    ProjectSerializer,
    CriterionSerializer,
    AlternativeSerializer,
    PerformanceSerializer,
    CriterionFunctionSerializer,
    HasseGraphSerializer
)


# User
class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Project
class ProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


# Criterion
class CriterionList(generics.ListCreateAPIView):
    queryset = Criterion.objects.all()
    serializer_class = CriterionSerializer


class CriterionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Criterion.objects.all()
    serializer_class = CriterionSerializer


# Alternative
class AlternativeList(generics.ListCreateAPIView):
    queryset = Alternative.objects.all()
    serializer_class = AlternativeSerializer


class AlternativeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alternative.objects.all()
    serializer_class = AlternativeSerializer


# Performance
class PerformanceList(generics.ListCreateAPIView):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer


class PerformanceDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer


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

import jwt
from rest_framework import permissions

from utagmsapi.models import (
    Project,
    Criterion,
    Alternative,
    Performance,
    PreferenceIntensity,
    PairwiseComparison,
    Category,
    CriterionCategory
)

from utagmsapi.utils.jwt import get_user_from_jwt


class IsLogged(permissions.BasePermission):

    def has_permission(self, request, view):
        token = request.COOKIES.get('access_token')

        if token is None:
            return False

        try:
            _ = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        return True


class IsOwnerOfProject(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get project
        project_pk = view.kwargs.get('project_pk')
        if project_pk is None:
            return False
        project = Project.objects.filter(id=project_pk).first()
        if project is None:
            return False

        # Checking if user is the owner of the project.
        # If they are it means that they can also get criterion or alternative from this project
        return project.user == user


class IsOwnerOfCategory(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get category
        category_pk = view.kwargs.get('category_pk')
        if category_pk is None:
            return False
        category = Category.objects.filter(id=category_pk).first()

        # check if criterion's project user is the same as the one making the request
        return category.project.user == user


class IsOwnerOfCriterion(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get criterion
        criterion_pk = view.kwargs.get('criterion_pk')
        if criterion_pk is None:
            return False
        criterion = Criterion.objects.filter(id=criterion_pk).first()

        # check if criterion's project user is the same as the one making the request
        return criterion.project.user == user


class IsOwnerOfCriterionCategory(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get criterion_category
        criterion_category_pk = view.kwargs.get('criterion_category_pk')
        if criterion_category_pk is None:
            return False
        criterion_category = CriterionCategory.objects.filter(id=criterion_category_pk).first()

        # check if performance belongs to the user
        return criterion_category.criterion.project.user == user


class IsOwnerOfAlternative(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get alternative
        alternative_pk = view.kwargs.get('alternative_pk')
        if alternative_pk is None:
            return False
        alternative = Alternative.objects.filter(id=alternative_pk).first()

        # check if alternative's project user is the same as the one making the request
        return alternative.project.user == user


class IsOwnerOfPerformance(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get performance
        performance_pk = view.kwargs.get('performance_pk')
        if performance_pk is None:
            return False
        performance = Performance.objects.filter(id=performance_pk).first()

        # check if performance belongs to the user
        return performance.alternative.project.user == user


class IsOwnerOfPreferenceIntensity(permissions.BasePermission):

    def has_permission(self, request, view):

        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get preference intensity
        preference_intensity_pk = view.kwargs.get('preference_intensity_pk')
        if preference_intensity_pk is None:
            return False
        preference_intensity = PreferenceIntensity.objects.filter(id=preference_intensity_pk).first()

        return preference_intensity.project.user == user


class IsOwnerOfPairwiseComparison(permissions.BasePermission):

    def has_permission(self, request, view):
        # get user
        token = request.COOKIES.get('access_token')
        if token is None:
            return False
        try:
            user = get_user_from_jwt(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
            return False

        # get pairwise comparison
        pairwise_comparison_pk = view.kwargs.get('pairwise_comparison_pk')
        if pairwise_comparison_pk is None:
            return False
        pairwise_comparison = PairwiseComparison.objects.filter(id=pairwise_comparison_pk).first()

        return pairwise_comparison.project.user == user

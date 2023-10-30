from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, MethodNotAllowed

from utagmsapi import models
from utagmsapi.models import (
    Performance,
    Criterion,
    Alternative,
    PreferenceIntensity,
    PairwiseComparison,
    CriterionFunctionPoint,
    CriterionCategory
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = "__all__"
        extra_kwargs = {
            'password': {'write_only': True}  # won't be returned
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.password = make_password(password)
        instance.save()
        return instance


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        exclude = ['user']
        optional_fields = ['description', 'hasse_graph']


class ProjectSerializerWhole(serializers.ModelSerializer):
    criteria = serializers.SerializerMethodField()
    alternatives = serializers.SerializerMethodField()
    preference_intensities = serializers.SerializerMethodField()
    pairwise_comparisons = serializers.SerializerMethodField()

    def get_criteria(self, obj):
        criteria = Criterion.objects.filter(project=obj)
        return CriterionSerializerWithFunctions(criteria, many=True).data

    def get_alternatives(self, obj):
        alternatives = Alternative.objects.filter(project=obj)
        return AlternativeSerializerWithPerformances(alternatives, many=True).data

    def get_preference_intensities(self, obj):
        preference_intensities = PreferenceIntensity.objects.filter(project=obj)
        return PreferenceIntensitySerializer(preference_intensities, many=True).data

    def get_pairwise_comparisons(self, obj):
        pairwise_comparisons = PairwiseComparison.objects.filter(project=obj)
        return PairwiseComparisonSerializer(pairwise_comparisons, many=True).data

    class Meta:
        model = models.Project
        fields = '__all__'

    def create(self, validated_data):
        raise MethodNotAllowed("Create operation not allowed")

    def update(self, instance, validated_data):
        raise MethodNotAllowed("Update operation not allowed")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        exclude = ['project']


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Criterion
        exclude = ['project']


class CriterionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CriterionCategory
        exclude = ['criterion']

    def save(self, **kwargs):
        criterion = kwargs.get('criterion')
        if criterion:

            category = self.validated_data.get('category')
            if criterion.project != category.project:
                raise ValidationError({"details": "criterion and category do not belong to the same project"})

            criterion_category = CriterionCategory.objects.filter(criterion=criterion).filter(category=category).first()
            if criterion_category:
                raise ValidationError({"details": "criterion_category already exists"})

        super().save(criterion=criterion)


class CriterionSerializerWithFunctions(serializers.ModelSerializer):
    criterion_function_points = serializers.SerializerMethodField()
    criterion_categories = serializers.SerializerMethodField()

    def get_criterion_function_points(self, obj):
        criterion_function_points = CriterionFunctionPoint.objects.filter(criterion=obj)
        return CriterionFunctionPointSerializer(criterion_function_points, many=True).data

    def get_criterion_categories(self, obj):
        criterion_categories = CriterionCategory.objects.filter(criterion=obj)
        return CriterionCategorySerializer(criterion_categories, many=True).data

    class Meta:
        model = models.Criterion
        fields = '__all__'


class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alternative
        exclude = ['project']


class AlternativeSerializerWithPerformances(serializers.ModelSerializer):
    performances = serializers.SerializerMethodField()

    def get_performances(self, obj):
        performances = Performance.objects.filter(alternative=obj)
        return PerformanceSerializer(performances, many=True).data

    class Meta:
        model = models.Alternative
        fields = '__all__'


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Performance
        exclude = ['alternative']

    def save(self, **kwargs):

        alternative = kwargs.get('alternative')
        if alternative:

            # get criterion
            criterion = self.validated_data.get('criterion')

            # check if alternative and criterion are in the same project
            if criterion.project != alternative.project:
                raise ValidationError({"details": "alternative and criterion do not belong to the same project"})

            # check if there exists a performance with this alternative and criterion
            performance = Performance.objects.filter(alternative=alternative).filter(criterion=criterion).first()
            if performance:
                raise ValidationError({"details": "performance for this alternative and criterion already exists"})

        super().save(alternative=alternative)


class PerformanceSerializerUpdate(serializers.ModelSerializer):
    value = serializers.FloatField(help_text="Performance value")

    class Meta:
        model = models.Performance
        fields = "__all__"
        extra_kwargs = {
            'criterion': {'read_only': True},
            'alternative': {'read_only': True}
        }


class CriterionFunctionPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CriterionFunctionPoint
        exclude = ['criterion']


class PreferenceIntensitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PreferenceIntensity
        exclude = ['project']

    def save(self, **kwargs):

        # we need to check if all four alternatives and criterion belong to the same project as specified in the URL
        project = kwargs.get('project')
        if project:
            # Get four alternatives
            alternatives = [self.validated_data.get(f'alternative_{_id}') for _id in range(1, 5)]
            # Get criterion
            criterion = self.validated_data.get('criterion')

            alternatives_invalid = any(
                [True if alternative.project != project else False for alternative in alternatives])
            if alternatives_invalid or (criterion and criterion.project != project):
                raise ValidationError(
                    {
                        "details": "The alternatives and criterion must belong to the same project as preference intensity."
                    }
                )

        super().save(**kwargs)


class PairwiseComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PairwiseComparison
        exclude = ['project']

    def save(self, **kwargs):
        # checking if alternatives belong to the same project
        project = kwargs.get('project')
        if project:
            alternative_1 = self.validated_data.get('alternative_1')
            alternative_2 = self.validated_data.get('alternative_2')
            if alternative_1.project != alternative_2.project or alternative_1.project != project:
                raise ValidationError(
                    {
                        "details": "The alternatives must belong to the same project as pairwise comparison."
                    }
                )
        super().save(**kwargs)

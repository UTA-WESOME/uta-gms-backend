from django.contrib.auth.hashers import make_password
from django_celery_results.models import TaskResult
from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed, ValidationError

from utagmsapi import models
from utagmsapi.models import (AcceptabilityIndex, Alternative, Category, Criterion, CriterionCategory, FunctionPoint,
                              Inconsistency, Job, PairwiseComparison, PairwiseWinning, Performance, PreferenceIntensity,
                              Ranking, Relation)


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
        optional_fields = ['description']


class ProjectSerializerWhole(serializers.ModelSerializer):
    criteria = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    alternatives = serializers.SerializerMethodField()
    preference_intensities = serializers.SerializerMethodField()

    def get_criteria(self, obj):
        criteria = Criterion.objects.filter(project=obj)
        return CriterionSerializer(criteria, many=True).data

    def get_categories(self, obj):
        categories = Category.objects.filter(project=obj)
        return CategorySerializerWhole(categories, many=True).data

    def get_alternatives(self, obj):
        alternatives = Alternative.objects.filter(project=obj)
        return AlternativeSerializerWithPerformances(alternatives, many=True).data

    def get_preference_intensities(self, obj):
        preference_intensities = PreferenceIntensity.objects.filter(project=obj)
        return PreferenceIntensitySerializer(preference_intensities, many=True).data

    class Meta:
        model = models.Project
        fields = '__all__'

    def create(self, validated_data):
        raise MethodNotAllowed("Create operation not allowed")

    def update(self, instance, validated_data):
        raise MethodNotAllowed("Update operation not allowed")


class ProjectSerializerJobs(serializers.ModelSerializer):
    jobs = serializers.SerializerMethodField()

    def get_jobs(self, obj):
        jobs = Job.objects.filter(project=obj)
        return JobSerializer(jobs, many=True).data

    class Meta:
        model = models.Project
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        exclude = ['project']


class CategorySerializerWhole(serializers.ModelSerializer):
    criterion_categories = serializers.SerializerMethodField()
    function_points = serializers.SerializerMethodField()
    pairwise_comparisons = serializers.SerializerMethodField()
    rankings = serializers.SerializerMethodField()
    acceptability_indices = serializers.SerializerMethodField()
    pairwise_winnings = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()
    inconsistencies = serializers.SerializerMethodField()

    def get_criterion_categories(self, obj):
        criterion_categories = CriterionCategory.objects.filter(category=obj)
        return CriterionCategorySerializer(criterion_categories, many=True).data

    def get_function_points(self, obj):
        function_points = FunctionPoint.objects.filter(category=obj)
        return FunctionPointSerializer(function_points, many=True).data

    def get_pairwise_comparisons(self, obj):
        pairwise_comparisons = PairwiseComparison.objects.filter(category=obj)
        return PairwiseComparisonSerializer(pairwise_comparisons, many=True).data

    def get_rankings(self, obj):
        rankings = Ranking.objects.filter(category=obj)
        return RankingSerializer(rankings, many=True).data

    def get_acceptability_indices(self, obj):
        acceptability_indices = AcceptabilityIndex.objects.filter(category=obj)
        return AcceptabilityIndexSerializer(acceptability_indices, many=True).data

    def get_pairwise_winnings(self, obj):
        pairwise_winnings = PairwiseWinning.objects.filter(category=obj)
        return PairwiseWinningSerializer(pairwise_winnings, many=True).data

    def get_relations(self, obj):
        relations = Relation.objects.filter(category=obj)
        return RelationSerializer(relations, many=True).data

    def get_inconsistencies(self, obj):
        inconsistencies = Inconsistency.objects.filter(category=obj)
        return InconsistencySerializer(inconsistencies, many=True).data

    class Meta:
        model = models.Category
        fields = '__all__'


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Criterion
        exclude = ['project']


class CriterionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CriterionCategory
        exclude = ['category']

    def save(self, **kwargs):
        category = kwargs.get('category')
        if category:

            criterion = self.validated_data.get('criterion')
            if criterion.project != category.project:
                raise ValidationError({"details": "criterion and category do not belong to the same project"})

        super().save(category=category)

    def create(self, validated_data):
        category = validated_data.get('category')
        criterion = validated_data.get('criterion')
        criterion_category = CriterionCategory.objects.filter(criterion=criterion).filter(category=category).first()
        if criterion_category:
            raise ValidationError({"details": "criterion_category already exists"})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        category = validated_data.get('category')
        criterion = validated_data.get('criterion')
        criterion_category = CriterionCategory.objects.filter(criterion=criterion).filter(category=category).first()
        if criterion_category and instance.id != criterion_category.id:
            raise ValidationError({"details": "criterion_category already exists"})

        return super().update(instance, validated_data)


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


class FunctionPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FunctionPoint
        exclude = ['category']


class PreferenceIntensitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PreferenceIntensity
        exclude = ['project']

    def save(self, **kwargs):

        # we need to check if all four alternatives and category/criterion
        # belong to the same project as specified in the URL
        project = kwargs.get('project')
        if project:
            # Get four alternatives
            alternatives = [self.validated_data.get(f'alternative_{_id}') for _id in range(1, 5)]
            # Get criterion
            criterion = self.validated_data.get('criterion')
            # Get category
            category = self.validated_data.get('category')

            alternatives_invalid = any([True if alternative.project != project else False
                                        for alternative in alternatives])
            if (
                    alternatives_invalid
                    or (criterion and criterion.project != project)
                    or (category and category.project != project)
            ):
                raise ValidationError({
                    "details": "The alternatives and criterion must belong to the same project as preference intensity."
                })

        super().save(**kwargs)


class PairwiseComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PairwiseComparison
        exclude = ['category']

    def save(self, **kwargs):
        # checking if alternatives belong to the same project
        category = kwargs.get('category')
        if category:
            alternative_1 = self.validated_data.get('alternative_1')
            alternative_2 = self.validated_data.get('alternative_2')
            if alternative_1.project != alternative_2.project or alternative_1.project != category.project:
                raise ValidationError({
                    "details": "The alternatives must belong to the same project as pairwise comparison."
                })
        super().save(**kwargs)


class RankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ranking
        exclude = ['category']

    def save(self, **kwargs):
        # checking if alternative and category belong to the same project
        category = kwargs.get('category')
        if category:
            alternative = self.validated_data.get('alternative')
            if category.project != alternative.project:
                raise ValidationError({
                    "details": "The alternative and category must belong to the same project."
                })

        super().save(**kwargs)


class AcceptabilityIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AcceptabilityIndex
        exclude = ['category']


class PairwiseWinningSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PairwiseWinning
        exclude = ['category']


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Relation
        exclude = ['category']


class InconsistencySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Inconsistency
        exclude = ['category']


class JobSerializer(serializers.ModelSerializer):
    ready = serializers.SerializerMethodField()
    finished_at = serializers.SerializerMethodField()

    class Meta:
        model = models.Job
        fields = '__all__'

    def get_ready(self, obj):
        task = TaskResult.objects.filter(task_id=obj.task).first()
        if task is None:
            return None
        return task.status

    def get_finished_at(self, obj):
        if TaskResult.objects.filter(task_id=obj.task).exists():
            return TaskResult.objects.filter(task_id=obj.task).first().date_done
        return None

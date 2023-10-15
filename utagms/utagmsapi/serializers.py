from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, MethodNotAllowed

from utagmsapi import models
from utagmsapi.models import Performance, Criterion, Alternative, PreferenceIntensity


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

    def get_criteria(self, obj):
        criteria = Criterion.objects.filter(project=obj)
        return CriterionSerializer(criteria, many=True).data

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


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Criterion
        exclude = ['project']


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


class CriterionFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CriterionFunction
        fields = "__all__"


class HasseGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HasseGraph
        fields = "__all__"


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

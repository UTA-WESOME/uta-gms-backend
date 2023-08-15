from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from utagmsapi import models


class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=32, help_text="User email")
    password = serializers.CharField(max_length=255, help_text="User password")
    name = serializers.CharField(max_length=64, help_text="User first name")
    surname = serializers.CharField(max_length=64, help_text="User last name")

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
    name = serializers.CharField(max_length=64, help_text="Project name")
    description = serializers.CharField(max_length=256, help_text="Project description")
    shareable = serializers.BooleanField(help_text="Project shareability")

    class Meta:
        model = models.Project
        exclude = ['user']
        # fields = "__all__"


class CriterionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=64, help_text="Criterion name")
    gain = serializers.BooleanField(help_text="Criterion is the type of gain")

    class Meta:
        model = models.Criterion
        exclude = ['project']
        # fields = "__all__"


class AlternativeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=64, help_text="Alternative name")
    reference_ranking = serializers.IntegerField(help_text="Alternative reference ranking")
    ranking = serializers.IntegerField(help_text="Alternative ranking")

    class Meta:
        model = models.Alternative
        fields = "__all__"


class PerformanceSerializer(serializers.ModelSerializer):
    value = serializers.FloatField(help_text="Performance value")

    class Meta:
        model = models.Performance
        fields = "__all__"


class CriterionFunctionSerializer(serializers.ModelSerializer):
    ordinate = serializers.FloatField(help_text="Ordinate")
    abscissa = serializers.FloatField(help_text="Abscissa")

    class Meta:
        model = models.CriterionFunction
        fields = "__all__"


class HasseGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HasseGraph
        fields = "__all__"

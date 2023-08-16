from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from utagmsapi import models


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
        # fields = "__all__"


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Criterion
        fields = "__all__"


class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alternative
        fields = "__all__"


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Performance
        fields = "__all__"


class CriterionFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CriterionFunction
        fields = "__all__"


class HasseGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HasseGraph
        fields = "__all__"

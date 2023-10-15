from django.core.validators import MinValueValidator
from django.db import models


class User(models.Model):
    email = models.CharField(max_length=32, unique=True, help_text="User email")
    password = models.CharField(max_length=255, help_text="User password")
    name = models.CharField(max_length=64, help_text="User first name")
    surname = models.CharField(max_length=64, help_text="User last name")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "surname", "email",)


class Project(models.Model):
    name = models.CharField(max_length=64, help_text="Project name")
    description = models.CharField(max_length=256, help_text="Project description", blank=True)
    shareable = models.BooleanField(help_text="Project shareability")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hasse_graph = models.JSONField(null=True, help_text="Graph that represents necessary relations between project's alternatives")

    class Meta:
        ordering = ("name", "user",)


class Criterion(models.Model):
    name = models.CharField(max_length=64, help_text="Criterion name")
    gain = models.BooleanField(help_text="Criterion is the type of gain")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="criteria")
    linear_segments = models.IntegerField(help_text="How many linear segments does the criterion have")
    weight = models.FloatField(
        default=1.0,
        help_text="Weight of the criterion",
        validators=[MinValueValidator(0.0, "Weight must be at least 0")]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)


class Alternative(models.Model):
    name = models.CharField(max_length=64, help_text="Alternative name")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="alternatives")
    reference_ranking = models.IntegerField(blank=True, null=True, help_text="Alternative reference ranking")
    ranking = models.IntegerField(help_text="Alternative ranking")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)


class Performance(models.Model):
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, related_name="performances")
    alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="performances")
    value = models.FloatField(help_text="Performance value")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("criterion", "alternative",)


class CriterionFunction(models.Model):
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, related_name="criterion_functions")
    ordinate = models.FloatField(help_text="Ordinate")
    abscissa = models.FloatField(help_text="Abscissa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("criterion",)


class HasseGraph(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="hasse_graphs")
    alternative_up = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="hasse_graphs_up")
    alternative_down = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="hasse_graphs_down")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("project", "alternative_up", "alternative_down",)


class PreferenceIntensity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="preference_intensities")
    alternative_1 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_1")
    alternative_2 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_2")
    alternative_3 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_3")
    alternative_4 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_4")
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, null=True,
                                  related_name="preference_intensities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('project', 'criterion',)

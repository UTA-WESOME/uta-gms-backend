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
    pairwise_mode = models.BooleanField(default=False, help_text="Set to 'True' if Pairwise Comparisons will be used, "
                                                                 "or 'False' if Reference Ranking is preferred.")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "user",)


class Category(models.Model):
    name = models.CharField(max_length=64, help_text="Category name")
    color = models.CharField(max_length=15, help_text="Color of the category")
    active = models.BooleanField(default=True, help_text="Should the category be used in calculating results?")
    hasse_graph = models.JSONField(null=True,
                                   help_text="Graph that represents necessary relations between project's alternatives")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class Criterion(models.Model):
    name = models.CharField(max_length=64, help_text="Criterion name")
    gain = models.BooleanField(help_text="Is the criterion of the type gain?")
    linear_segments = models.IntegerField(help_text="How many linear segments does the criterion have?")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="criteria")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class CriterionCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="criterion_categories")
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, related_name="criterion_categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("category",)


class Alternative(models.Model):
    name = models.CharField(max_length=64, help_text="Alternative name")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="alternatives")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class Ranking(models.Model):
    reference_ranking = models.IntegerField(blank=True, null=True, help_text="Alternative reference ranking")
    ranking = models.IntegerField(help_text="Alternative ranking")
    ranking_value = models.FloatField(default=0.0, help_text="Alternative's final value in the ranking")
    worst_position = models.IntegerField(blank=True, null=True,
                                         help_text="Worst position the alternative can have in the final ranking")
    best_position = models.IntegerField(blank=True, null=True,
                                        help_text="Best position the alternative can have in the final ranking")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rankings')
    alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name='rankings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("category", "alternative",)


class Performance(models.Model):
    value = models.FloatField(help_text="Performance value")
    alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="performances")
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, related_name="performances")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("criterion", "alternative",)


class FunctionPoint(models.Model):
    ordinate = models.FloatField(help_text="Ordinate")
    abscissa = models.FloatField(help_text="Abscissa")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="function_points")
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, related_name="function_points")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("criterion",)


class PreferenceIntensity(models.Model):
    PREFERENCE = '>'
    WEAK_PREFERENCE = '>='
    INDIFFERENCE = '='

    TYPE_CHOICES = [
        (PREFERENCE, 'Preference'),
        (WEAK_PREFERENCE, 'Weak preference'),
        (INDIFFERENCE, 'Indifference')
    ]

    type = models.CharField(max_length=12, choices=TYPE_CHOICES, default=PREFERENCE)
    alternative_1 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_1")
    alternative_2 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_2")
    alternative_3 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_3")
    alternative_4 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="preference_intensities_4")
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, null=True, related_name="preference_intensities")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="preference_intensities")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="preference_intensities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class PairwiseComparison(models.Model):
    PREFERENCE = '>'
    WEAK_PREFERENCE = '>='
    INDIFFERENCE = '='

    TYPE_CHOICES = [
        (PREFERENCE, 'Preference'),
        (WEAK_PREFERENCE, 'Weak preference'),
        (INDIFFERENCE, 'Indifference'),
    ]

    type = models.CharField(max_length=12, choices=TYPE_CHOICES, default=PREFERENCE)
    alternative_1 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="pairwise_comparisons_1")
    alternative_2 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="pairwise_comparisons_2")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="pairwise_comparisons")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class Percentage(models.Model):
    position = models.IntegerField(help_text="Position of the percentage")
    percent = models.FloatField(help_text="How many percent of cases was the alternative in this position?")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="percentages")
    alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="percentages")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class AcceptabilityIndex(models.Model):
    percentage = models.FloatField(help_text="In how many percent of cases is alternative_1 better than alternative_2?")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="acceptability_indices")
    alternative_1 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="acceptability_indices_1")
    alternative_2 = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="acceptability_indices_2")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)


class Inconsistency(models.Model):
    PREFERENCE = '>'
    WEAK_PREFERENCE = '>='
    INDIFFERENCE = '='
    POSITION = 'position'
    INTENSITY = 'intensity'

    TYPE_CHOICES = [
        (PREFERENCE, 'Preference'),
        (WEAK_PREFERENCE, 'Weak preference'),
        (INDIFFERENCE, 'Indifference'),
        (POSITION, 'Position'),
        (INTENSITY, 'Intensity')
    ]
    group = models.IntegerField(help_text="Group of the inconsistency. Inconsistencies that belong to the same group"
                                          " should be deleted to make the problem consistent")
    data = models.TextField(help_text="Data of the inconsistency")
    type = models.CharField(choices=TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="inconsistencies")

    class Meta:
        ordering = ("category", "group", "id",)

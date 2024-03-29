# Generated by Django 4.2.3 on 2023-12-18 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0007_alter_ranking_extreme_best_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pairwisewinning',
            old_name='percentage',
            new_name='percent',
        ),
        migrations.RemoveField(
            model_name='ranking',
            name='extreme_best',
        ),
        migrations.RemoveField(
            model_name='ranking',
            name='extreme_worst',
        ),
        migrations.AddField(
            model_name='category',
            name='sampler_error',
            field=models.CharField(blank=True, help_text='Explanation of the sampler error', null=True),
        ),
        migrations.AddField(
            model_name='ranking',
            name='extreme_optimistic_best',
            field=models.IntegerField(default=0, help_text='Best possible position the alternative has using optimistic approach'),
        ),
        migrations.AddField(
            model_name='ranking',
            name='extreme_optimistic_worst',
            field=models.IntegerField(default=0, help_text='Worst possible position the alternative has using optimistic approach'),
        ),
        migrations.AddField(
            model_name='ranking',
            name='extreme_pessimistic_best',
            field=models.IntegerField(default=0, help_text='Best possible position the alternative has using pessimistic approach'),
        ),
        migrations.AddField(
            model_name='ranking',
            name='extreme_pessimistic_worst',
            field=models.IntegerField(default=0, help_text='Worst possible position the alternative has using pessimistic approach'),
        ),
    ]

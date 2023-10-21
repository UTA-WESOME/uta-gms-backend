# Generated by Django 4.2.3 on 2023-10-21 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0011_project_pairwise_mode_pairwisecomparison'),
    ]

    operations = [
        migrations.AddField(
            model_name='alternative',
            name='best_position',
            field=models.IntegerField(blank=True, help_text='Best position the alternative can have in the final ranking', null=True),
        ),
        migrations.AddField(
            model_name='alternative',
            name='worst_position',
            field=models.IntegerField(blank=True, help_text='Worst position the alternative can have in the final ranking', null=True),
        ),
    ]

# Generated by Django 4.2.3 on 2023-12-01 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0002_inconsistency'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferenceintensity',
            name='type',
            field=models.CharField(choices=[('>', 'Preference'), ('>=', 'Weak preference'), ('=', 'Indifference')], default='>', max_length=12),
        ),
        migrations.AlterField(
            model_name='pairwisecomparison',
            name='type',
            field=models.CharField(choices=[('>', 'Preference'), ('>=', 'Weak preference'), ('=', 'Indifference')], default='>', max_length=12),
        ),
    ]

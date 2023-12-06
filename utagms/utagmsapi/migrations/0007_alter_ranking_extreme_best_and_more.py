# Generated by Django 4.2.3 on 2023-12-06 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0006_ranking_extreme_best_ranking_extreme_worst'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ranking',
            name='extreme_best',
            field=models.IntegerField(default=0, help_text='Best possible position the alternative has'),
        ),
        migrations.AlterField(
            model_name='ranking',
            name='extreme_worst',
            field=models.IntegerField(default=0, help_text='Worst possible position the alternative has'),
        ),
        migrations.AlterField(
            model_name='ranking',
            name='ranking',
            field=models.IntegerField(default=0, help_text='Alternative ranking'),
        ),
    ]

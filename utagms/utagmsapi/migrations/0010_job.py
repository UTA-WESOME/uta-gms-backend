# Generated by Django 4.2.3 on 2024-02-25 20:18

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0009_category_samples'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Job's (category) name", max_length=255)),
                ('group', models.IntegerField(help_text='Jobs for a project with the same group were queued together.', validators=[django.core.validators.MinValueValidator(1)])),
                ('task', models.CharField(help_text='Celery ID of the task', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='utagmsapi.project')),
            ],
        ),
    ]

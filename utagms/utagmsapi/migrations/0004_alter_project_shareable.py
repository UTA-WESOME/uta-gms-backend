# Generated by Django 4.2.3 on 2023-08-16 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0003_alternative_created_at_alternative_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='shareable',
            field=models.BooleanField(blank=True, help_text='Project shareability'),
        ),
    ]

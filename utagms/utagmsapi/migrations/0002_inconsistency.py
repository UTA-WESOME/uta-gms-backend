# Generated by Django 4.2.3 on 2023-11-26 16:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('utagmsapi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inconsistency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.IntegerField(help_text='Group of the inconsistency. Inconsistencies that belong to the same group should be deleted to make the problem consistent')),
                ('data', models.TextField(help_text='Data of the inconsistency')),
                ('type', models.CharField(choices=[('preference', 'Preference'), ('indifference', 'Indifference'), ('position', 'Position'), ('intensity', 'Intensity')])),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inconsistencies', to='utagmsapi.category')),
            ],
            options={
                'ordering': ('category', 'group', 'id'),
            },
        ),
    ]

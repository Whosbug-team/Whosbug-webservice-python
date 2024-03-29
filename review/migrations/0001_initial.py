# Generated by Django 3.1 on 2022-07-30 18:47

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('diffs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.CharField(max_length=200)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diffs.project', verbose_name='White Rule of The Project')),
            ],
        ),
        migrations.CreateModel(
            name='Reviewer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.CharField(max_length=200)),
                ('reviewer', models.CharField(max_length=100, verbose_name='review the file')),
                ('review_rule', models.IntegerField(validators=[django.core.validators.MinValueValidator(-1)])),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diffs.project', verbose_name='Reviewer Belongs to the Project')),
            ],
        ),
    ]

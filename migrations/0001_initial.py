# Generated by Django 3.2.20 on 2024-04-03 05:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LONMetadataSync',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('report_name', models.CharField(max_length=500, verbose_name='Report Name')),
                ('app_name', models.CharField(max_length=500, verbose_name='App Name')),
                ('model_name', models.CharField(max_length=500, verbose_name='Model Name')),
                ('db_table', models.CharField(max_length=500, verbose_name='Table Name')),
                ('table_filters', models.CharField(max_length=4000, verbose_name='Filters')),
                ('table_update_on', models.CharField(max_length=4000, verbose_name='Update On')),
                ('inherit_parent_filter', models.CharField(max_length=4000, verbose_name='Inherit Parent Filter')),
                ('exclude_columns', models.CharField(max_length=4000, verbose_name='Columns to Exclude')),
                ('full_refresh', models.BooleanField(default=False)),
                ('ready_to_copy', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'LightsOn Site Metadata Sync',
                'db_table': '"site_dba"."lon_metadata_sync"',
            },
        ),
    ]
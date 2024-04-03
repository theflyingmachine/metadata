from django.db import models

from core.utils import dynamic_db_table


class LONMetadataSync(models.Model):
    id = models.IntegerField(primary_key=True)
    report_name = models.CharField(max_length=500)
    app_name = models.CharField(max_length=500)
    model_name = models.CharField(max_length=500)
    db_table = models.CharField(max_length=500)
    table_filters = models.CharField(max_length=4000)
    table_update_on = models.CharField(max_length=4000)
    inherit_parent_filter = models.CharField(max_length=4000)
    exclude_columns = models.CharField(max_length=4000)
    full_refresh = models.BooleanField(default=False)
    ready_to_copy = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    updt_dt_tm = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = dynamic_db_table('site_dba', 'lon_metadata_sync')
        verbose_name = 'LightsOn Site Metadata Sync'

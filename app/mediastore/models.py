from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager
from simple_history.models import HistoricalRecords


class IdentityType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    #display_name = models.CharField(max_length=255)
    #regex = models.CharField(max_length=255)

class S3Config(models.Model):
    url = models.URLField(max_length=255, unique=True)
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)

class StoreConfig(models.Model):
    BUCKETSTORE = 'BucketStore'
    FILESYSTEMSTORE = 'FilesystemStore'
    HASHDIRSTORE = 'HashdirStore'
    ZIPSTORE = 'ZipStore'
    SQLITESTORE = 'SqliteStore'
    DICTSTORE = 'DictStore'
    TYPES = ((BUCKETSTORE, 'BucketStore'),
             (FILESYSTEMSTORE, 'FilesystemStore'),
             (HASHDIRSTORE, 'HashdirStore'),
             (ZIPSTORE, 'ZipStore'),
             (SQLITESTORE, 'SqliteStore'),
             (DICTSTORE, 'DictStore'),
             )

    PENDING = 'PENDING'
    READY = 'READY'
    STATUSES = ((PENDING,'PENDING'),
                (READY,  'READY'))

    type = models.CharField(max_length=255, choices=TYPES)
    s3cfg = models.ForeignKey(S3Config, on_delete=models.SET_NULL, null=True, default=None)
    bucket = models.CharField(max_length=255)
    # bucket used as local_root path if used for FilesystemStore HashdirStore ZipStore SqliteStore, ie if s3_params = null

    def is_s3_type(self):
        return self.type == self.BUCKETSTORE


class Media(models.Model):
    pid = models.CharField(max_length=255, unique=True)
    pid_type = models.CharField(max_length=255)
    store_config = models.ForeignKey(StoreConfig, on_delete=models.RESTRICT)
    store_key = models.CharField(max_length=255, blank=True, null=False)
    store_status = models.CharField(max_length=12, choices=StoreConfig.STATUSES, default=StoreConfig.PENDING)
    identifiers = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    tags = TaggableManager()
    history = HistoricalRecords()
    # TODO lifecycle, other relationships

    def __str__(self):
        return f'{self.pid_type}:{self.pid}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store_key", "store_config"],
                name="unique_storeKey_per_storeConfig",
            ),
        ]
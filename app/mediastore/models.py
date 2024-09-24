from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager
from simple_history.models import HistoricalRecords

import storage.fs, storage.s3, storage.db, storage.object


class DictStoreSingleton(storage.object.DictStore):
    """
    Singleton version of storage.object.DictStore
    for use in repeat queries to RAMSTORE
    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def __init__(self):
        # Initialize objects only if not already initialized
        if not hasattr(self, 'objects'):
            self.objects = {}


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
    s3cfg = models.ForeignKey(S3Config, on_delete=models.RESTRICT, null=True, default=None)
    bucket = models.CharField(max_length=255)
    # bucket used as local_root path if used for FilesystemStore HashdirStore ZipStore SqliteStore, ie if s3_params = null

    def is_s3_type(self):
        return self.type == self.BUCKETSTORE

    @property
    def storage_is_context_managed(self):
        if self.type in [self.BUCKETSTORE, self.SQLITESTORE]:
            return True
        return False

    @property
    def storage_Store_kwargs(self):
        match self.type:
            case self.FILESYSTEMSTORE:
                return dict(root_path=self.bucket)
            case self.SQLITESTORE:
                return dict(db_path=self.bucket)
            case self.DICTSTORE:
                return dict()
            case self.BUCKETSTORE:
                return dict(
                    s3_url = self.s3cfg.url,
                    s3_access_key = self.s3cfg.access_key,
                    s3_secret_key = self.s3cfg.secret_key,
                    bucket_name = self.bucket)

    def get_storage_Store(self):
        match self.type:
            case self.FILESYSTEMSTORE:
                return storage.fs.FilesystemStore
            case self.SQLITESTORE:
                return storage.db.SqliteStore
            case self.DICTSTORE:
                return DictStoreSingleton
                #return storage.object.DictStore
            case self.BUCKETSTORE:
                return storage.s3.BucketStore

    def get_storage_store(self):
        Store = self.get_storage_Store()
        return Store(**self.storage_Store_kwargs)


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
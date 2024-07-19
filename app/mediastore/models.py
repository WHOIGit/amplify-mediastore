from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager
from simple_history.models import HistoricalRecords

class IdentityType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    #display_name = models.CharField(max_length=255)
    #regex = models.CharField(max_length=255)

class Media(models.Model):
    pid = models.CharField(max_length=255, unique=True)
    pid_type = models.CharField(max_length=255)
    s3url = models.CharField(max_length=255, null=True, blank=True)
    #TODO s3url may need to become more generic "storage pointer" field, which could be s3, disk, ram, something-else
    identifiers = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    tags = TaggableManager()
    history = HistoricalRecords()
    # TODO lifecycle, other relationships

    def __str__(self):
        return f'{self.pid_type}:{self.pid}'

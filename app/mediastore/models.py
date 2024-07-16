from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager

class Tag(models.Model):
    tag = models.CharField(max_length=255)
    def __str__(self):
        return self.tag

class IdentityType(models.Model):
    name = models.CharField(max_length=255)
    #display_name = models.CharField(max_length=255)
    #regex = models.CharField(max_length=255)

class Media(models.Model):
    pid = models.CharField(max_length=255, unique=True)
    pid_type = models.CharField(max_length=255)
    s3url = models.CharField(max_length=255, null=True, blank=True)
    identifiers = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    tags = TaggableManager()
    # TODO lifecycle Tags, Version, other relationships

    def __str__(self):
        return f'{self.pid_type}:{self.pid}'

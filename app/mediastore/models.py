from django.db import models
from django.utils.translation import gettext_lazy as _

class Media(models.Model):
    class MediaIDTypes(models.TextChoices):
        AMPID = "AMP", _("Amplify Global ID")
        S3_OBJ = "OBJ", _("Object Store ID")
        IFCB_BIN = "BIN", _("IFCB Bin ID")
        IFCB_BIN_IMG = "ROI", _("IFCB ROI ID")
        CHECKSUM = "CHK", _("CHECKSUM")
        FILENAME = "FLN", _("FILENAME")

    pid = models.CharField(max_length=255)
    pid_type = models.CharField(choices=MediaIDTypes)
    metadata = models.JSONField()
    # TODO lifecycle Tags, Version, other relationships, json field

    def __str__(self):
        return self.pid



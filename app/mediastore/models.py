from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Identity(models.Model):
    class IDTypes(models.TextChoices):
        AMPID = "AMP", _("Amplify Global ID")
        S3_OBJ = "OBJ", _("Object Store ID")
        IFCB_BIN = "BIN", _("IFCB Bin ID")
        IFCB_BIN_IMG = "ROI", _("IFCB ROI ID")
        CHECKSUM = "CHK", _("CHECKSUM")
        FILENAME = "FLN", _("FILENAME")

    type = models.CharField(choices=IDTypes, max_length=12)
    token = models.CharField(max_length=255, unique=True)
    media = models.ForeignKey('Media', on_delete=models.CASCADE, related_name='ids')
    is_pid = models.BooleanField(default=False)

    def __str__(self):
        return self.token

    def __repr__(self):
        return f'[{self.type}]:{self.token}'


class Media(models.Model):
    metadata = models.JSONField(default=dict)

    # TODO lifecycle Tags, Version, other relationships, json field

    @property
    def pid(self):
        return self.ids.filter(is_pid=True) if self.ids.exists() else None

    def clean(self):
        if self.ids.exists():
            id_count = self.ids.count()
            if id_count==1:  # set pid if only one identity
                pid = self.ids.first()
                pid.is_pid=True
                pid.save()
            else:

                pid_count = self.ids.filter(is_pid=True).count()
                if pid_count != 1:  # check only one pid
                    raise ValidationError(_(f'Exactly one Identity must have is_pid=True. {pid_count} of {id_count} IDs were set as pid'))

    def __str__(self):
        return repr(self.pid)
#    def __repr__(self):
#        id_reps = [repr(ident) for ident in self.ids.all()]
#        return ';'.join(id_reps)
    def ids_dict(self):
        ids = dict()
        for ident in self.ids.all():
            ids.update(ident.__dict__())

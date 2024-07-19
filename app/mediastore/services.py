from django.db import transaction
from mediastore.models import Media, IdentityType
from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate

from ninja.errors import ValidationError, HttpError

class MediaService:

    @staticmethod
    def serialize(media: Media) -> MediaSchema:
        return MediaSchema(
            pk = media.pk,
            pid = media.pid,
            pid_type = media.pid_type,
            s3url = media.s3url,
            identifiers = media.identifiers,
            metadata = media.metadata,
            tags = media.tags.names()
        )

    @staticmethod
    def create(payload: MediaSchemaCreate) -> MediaSchema:
        MediaService.clean_identifiers(payload)

        media = Media.objects.create(
            pid = payload.pid,
            pid_type = payload.pid_type,
            s3url = payload.s3url,
            identifiers = payload.identifiers, # already cleaned
            metadata = payload.metadata,
        )
        media.tags.set(payload.tags)
        return MediaService.serialize(media)

    @staticmethod
    def read(pid: str) -> MediaSchema:
        media = Media.objects.get(pid=pid)
        return MediaService.serialize(media)

    @staticmethod
    def update(pid, payload: MediaSchemaUpdate, putorpatch:str = 'patch') -> None:
        if putorpatch=='put':
            return MediaService.put(pid, payload)
        else:
            return MediaService.patch(pid, payload)

    @staticmethod
    def put(pid: str, payload: MediaSchemaUpdate) -> None:
        media = Media.objects.get(pid=pid)
        media.pid = payload.pid
        media.pid_type = payload.pid_type
        media.s3url = payload.s3url
        media.identifiers = MediaService.clean_identifiers(payload)
        media.metadata = payload.metadata
        media.save()
        media.tags.set(payload.tags)
        return media

    @staticmethod
    def patch(pid: str, payload: MediaSchemaUpdate) -> None:
        media = Media.objects.get(pid=pid)
        if payload.pid:
            media.pid = payload.pid
        if payload.pid_type:
            media.pid_type = payload.pid_type
        if payload.s3url:
            media.s3url = payload.s3url
        if payload.identifiers:
            MediaService.clean_identifiers(payload, media_obj=media)  # because sometimes PID is not included
            media.identifiers.update(**payload.identifiers)
        if payload.metadata:
            media.metadata.update(**payload.metadata)
        media.save()
        if payload.tags:
            media.tags.add(*payload.tags)
        return media

    @staticmethod
    def delete(pid: str) -> None:
        media = Media.objects.get(pid=pid)
        return media.delete()

    @staticmethod
    def list() -> list[MediaSchema]:
        medias = Media.objects.all()
        return [MediaService.serialize(media) for media in medias]

    @staticmethod
    def clean_identifiers(payload: MediaSchemaCreate|MediaSchemaUpdate, media_obj:Media|None = None):
        pop_me = None
        if media_obj:
            pid, pid_type = media_obj.pid, media_obj.pid_type
        else:
            pid, pid_type = payload.pid, payload.pid_type
        if not IdentityType.objects.filter(name=pid_type).exists(): raise ValidationError([dict(error=f'bad pid_type: {pid_type}')])
        for key, val in payload.identifiers.items():
            if not IdentityType.objects.filter(name=key).exists(): raise ValidationError([dict(error=f'bad identifier_type: {key}')])
            if key == pid_type:
                if not val == pid: raise ValidationError([dict(error=f'duplicate pid_type in identifiers DO NOT MATCH: media[{pid_type}]:{pid} =! identifier[{key}]:{val}')])
                pop_me = key
        if pop_me: payload.identifiers.pop(pop_me)
        return payload.identifiers

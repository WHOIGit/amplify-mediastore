from django.db import transaction
from mediastore.models import Media, IdentityType
from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaPatch
from mediastore.schemas import clean_identifiers


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
        clean_identifiers(payload)

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
    def update(pid, payload: MediaSchemaPatch, putorpatch:str = 'patch') -> None:
        if putorpatch=='put':
            return MediaService.put(pid, payload)
        else:
            return MediaService.patch(pid, payload)

    @staticmethod
    def put(pid: str, payload: MediaSchemaPatch) -> None:
        media = Media.objects.get(pid=pid)
        media.pid = payload.pid
        media.pid_type = payload.pid_type
        media.s3url = payload.s3url
        media.identifiers = clean_identifiers(payload)
        media.metadata = payload.metadata
        media.save()
        media.tags.set(payload.tags)

    @staticmethod
    def patch(pid: str, payload: MediaSchemaPatch) -> None:
        media = Media.objects.get(pid=pid)
        if payload.pid:
            media.pid = payload.pid
        if payload.pid_type:
            media.pid_type = payload.pid_type
        if payload.s3url:
            media.s3url = payload.s3url
        if payload.identifiers:
            clean_identifiers(payload, media_obj=media)
            media.identifiers.update(**payload.identifiers)
        if payload.metadata:
            media.metadata.update(**payload.metadata)
        media.save()
        if payload.tags:
            media.tags.add(*payload.tags)

    @staticmethod
    def delete(pid: str) -> None:
        media = Media.objects.get(pid=pid)
        return media.delete()

    @staticmethod
    def list() -> list[MediaSchema]:
        medias = Media.objects.all()
        return [MediaService.serialize(media) for media in medias]

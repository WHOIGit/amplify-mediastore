from django.db import transaction
from mediastore.models import Media, Identity
from mediastore.schemas import MediaSchema

class MediaService:

    @staticmethod
    def serialize(media: Media) -> MediaSchema:
        return MediaSchema(
            ids=media.ids.all(),
            metadata=media.metadata
        )

    @staticmethod
    def create(media_input: MediaSchema) -> MediaSchema:
        with transaction.atomic():
            media = Media.objects.create(
                metadata=media_input.metadata
            )
            for ident_schema in media_input.ids:
                #print(ident_schema.dict())
                ident_obj = Identity.objects.create(
                    type = ident_schema.type,
                    token = ident_schema.token,
                    media = media,
                    is_pid = ident_schema.is_pid if hasattr(ident_schema,'is_pid') else False)
            media.clean()
        return MediaService.serialize(media)

    @staticmethod
    def read(id: str) -> MediaSchema:
        media = Identity.objects.select_related('media').get(token=id).media
        return MediaService.serialize(media)

    @staticmethod
    def update(pid: str, media_input: MediaSchema) -> str:
        #media = Identity.objects.get(token=pid, is_pid=True).select_related('media').media
        media = Media.objects.filter(ids__is_pid=True, ids__token=pid)
        if media_input.metadata: media.update(metadata=media_input.metadata)
        media = media.first()
        extant_ids = Identity.objects.filter(media__id=media.id)
        for ident_schema in media_input.ids:
            extant_id = extant_ids.filter(type=ident_schema.type, token=ident_schema.token)
            if extant_id.exists():
                extant_id.update(ident_schema)
            else:
                ident_obj = Identity.objects.create(
                    type=ident_schema.type,
                    token=ident_schema.token,
                    media=media,
                    is_pid=ident_schema.is_pid if hasattr(ident_schema, 'is_pid') else False)

        return media

    @staticmethod
    def delete(pid: str) -> None:
        media = Identity.objects.select_related('media').get(token=pid).media
        return media.delete()

    @staticmethod
    def list() -> list[MediaSchema]:
        medias = Media.objects.all()
        return [MediaService.serialize(media) for media in medias]

import uuid

from django.core.exceptions import ObjectDoesNotExist
from ninja.errors import ValidationError, HttpError

from mediastore.models import Media, IdentityType, StoreConfig, S3Config
from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate, StoreConfigSchema, S3ConfigSchema


class StoreService:
    @staticmethod
    def serialize_s3config(s3config: S3Config, with_secret:bool=False):
        secret_key = s3config.secret_key if with_secret else False
        return S3ConfigSchema(url=s3config.url, access_key=s3config.access_key, secret_ket=secret_key)

    @staticmethod
    def serialize(store_config: StoreConfig, with_secret:bool=False):
        s3config = StoreService.serialize_s3config(store_config.s3_params, with_secret) if store_config.s3_params else None
        return StoreConfigSchema(type=store_config.type, bucket=store_config.bucket, s3_params=s3config)

    @staticmethod
    def get_or_create(store_config: StoreConfigSchema):
        StoreService.clean(store_config)
        store_config, storeconfig_created = StoreConfig.objects.get_or_create(type=store_config.type, bucket=store_config.bucket)
        s3config_created = None
        if store_config.type == StoreConfig.BUCKETSTORE:
            try:
                s3config = S3Config.objects.get(url=store_config.s3_params.url, access_key=store_config.s3_params.access_key)
                s3config_created = False
            except ObjectDoesNotExist:
                assert store_config.s3_params.secret_key, 'S3Config when created must include secret_key'
                s3config = S3Config.objects.create(url=store_config.s3_params.url,
                                     access_key=store_config.s3_params.access_key,
                                     secret_key=store_config.s3_params.secret_key)
                s3config_created = True
            store_config.s3_params = s3config
            store_config.save()
        return store_config, storeconfig_created, s3config_created

    @staticmethod
    def clean(payload: StoreConfigSchema):
        if payload.type == StoreConfig.BUCKETSTORE and payload.s3_params is None:
            raise ValidationError([dict(error='type[BUCKETSTORE] must include s3_params')])
        if payload.type != StoreConfig.BUCKETSTORE and payload.s3_params is not None:
            raise ValidationError([dict(error='Only type[BUCKETSTORE] may include s3_params')])
        return payload


class MediaService:
    @staticmethod
    def serialize(media: Media) -> MediaSchema:
        return MediaSchema(
            pk = media.pk,
            pid = media.pid,
            pid_type = media.pid_type,
            store_config = StoreService.serialize(media.store_config),
            store_key = media.store_key,
            store_status = media.store_status,
            identifiers = media.identifiers,
            metadata = media.metadata,
            tags = media.tags.names()
        )

    @staticmethod
    def create(payload: MediaSchemaCreate) -> MediaSchema:
        MediaService.clean_identifiers(payload)
        if not payload.store_key:
            payload.store_key = str(uuid.uuid4())
        store_config,storeconfig_created,s3config_created = StoreService.get_or_create(payload.store_config)
        media = Media.objects.create(
            pid = payload.pid,
            pid_type = payload.pid_type,
            store_config = store_config,
            store_key = payload.store_key,
            store_status = StoreConfig.PENDING,
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
        store_config,storeconfig_created,s3config_created = StoreService.get_or_create(payload.store_config)
        media = Media.objects.get(pid=pid)
        media.pid = payload.pid
        media.pid_type = payload.pid_type
        media.store_config = store_config
        media.store_key = payload.store_key
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
        if payload.store_key:
            media.store_key = payload.store_key
        if payload.store_config:
            store_config, storeconfig_created, s3config_created = StoreService.get_or_create(payload.store_config)
            media.store_config = store_config
        if payload.identifiers:
            MediaService.clean_identifiers(payload, media_obj=media)  # because sometimes PID is not included
            media.identifiers.update(**payload.identifiers)
        if payload.metadata:
            media.metadata.update(**payload.metadata)
        media.save()
        if payload.tags:
            media.tags.add(*payload.tags)
        return media

    #TODO CRUD for metadata,identifiers,tags SPECIFICALLY
    @staticmethod
    def update_status(pid:str, status:str):
        media = Media.objects.get(pid=pid)
        media.store_status = status
        media.save()
        return status

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



import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from ninja.errors import ValidationError, HttpError

from mediastore.models import Media, IdentityType, StoreConfig, S3Config
from mediastore.schemas import MediaSchema, MediaSchemaCreate, MediaSchemaUpdate, StoreConfigSchema, StoreConfigSchemaCreate, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys


class S3ConfigService:
    @staticmethod
    def serialize(s3cfg: S3Config):
        return S3ConfigSchemaSansKeys(pk=s3cfg.pk, url=s3cfg.url)

    @staticmethod
    def create(s3cfg_schema: S3ConfigSchemaCreate, as_schema=True):
        s3cfg, s3cfg_created = S3Config.objects.get_or_create(**dict(s3cfg_schema))
        if as_schema: return S3ConfigService.serialize(s3cfg)
        return s3cfg, s3cfg_created

    @staticmethod
    def read(pk: int):
        s3cfg = S3Config.objects.get(pk=pk)
        return S3ConfigService.serialize(s3cfg)

    @staticmethod  # PUT
    def update(pk: int, s3cfg_schema: S3ConfigSchemaCreate):
        s3cfg = S3Config.objects.get(pk=pk)
        s3cfg.url = s3cfg_schema.url
        s3cfg.access_key = s3cfg_schema.access_key
        s3cfg.secret_key = s3cfg_schema.secret_key
        s3cfg.save()

    @staticmethod
    def delete(pk: int):
        s3cfg = S3Config.objects.get(pk=pk)
        s3cfg.delete()
        # TODO also remove object store objects?

    @staticmethod
    def list() -> list[S3ConfigSchemaSansKeys]:
        s3cfgs = S3Config.objects.all()
        return [S3ConfigService.serialize(s3cfg) for s3cfg in s3cfgs]


class StoreService:
    @staticmethod
    def serialize(store_config: StoreConfig):
        s3_url = store_config.s3cfg.url if store_config.s3cfg else ''
        return StoreConfigSchema(pk=store_config.pk, type=store_config.type, bucket=store_config.bucket, s3_url=s3_url)

    @staticmethod
    def clean(payload: type[StoreConfigSchema|StoreConfigSchemaCreate]):
        if payload.type not in list(zip(*StoreConfig.TYPES))[0]:
            raise ValidationError([dict(error=f'type "{payload.type}" not supported.')])
        if payload.type == StoreConfig.BUCKETSTORE and not payload.s3_url:
            raise ValidationError([dict(error='type[BUCKETSTORE] must include s3_url')])
        if payload.type != StoreConfig.BUCKETSTORE and payload.s3_url:
            raise ValidationError([dict(error='Only type[BUCKETSTORE] may include s3_url')])
        return payload

    @staticmethod
    def create(storeconfig_schema: StoreConfigSchemaCreate, as_schema=True):
        StoreService.clean(storeconfig_schema)
        s3cfg = None
        if storeconfig_schema.type == StoreConfig.BUCKETSTORE:
            try: s3cfg = S3Config.objects.get(url=storeconfig_schema.s3_url)
            except ObjectDoesNotExist:
                raise ValidationError([dict(error=f'No S3Config with url="{storeconfig_schema.s3_url}" found. Please create S3Config credentials for this url first')])
        store_config, storeconfig_created = StoreConfig.objects.get_or_create(
            type=storeconfig_schema.type, bucket=storeconfig_schema.bucket, s3cfg=s3cfg)
        if as_schema: return StoreService.serialize(store_config)
        return store_config, storeconfig_created

    @staticmethod
    def read(pk: int):
        store_config = StoreConfig.objects.get(pk=pk)
        return StoreService.serialize(store_config)

    @staticmethod
    def update(pk: int, payload: StoreConfigSchemaCreate, putorpatch:str = 'put') -> None:
        if putorpatch=='patch': raise NotImplementedError
        store_config = StoreConfig.objects.get(pk=pk)
        if store_config.type != payload.type:
            raise ValidationError([dict(error=f'StoreConfig "type" may not be updated.')])
        if store_config.type == StoreConfig.BUCKETSTORE:
            try: store_config.s3cfg = S3Config.objects.get(url=payload.s3_url)
            except ObjectDoesNotExist:
                raise ValidationError([dict(error=f'No S3Config with url="{payload.s3_url}" found. Please create S3Config credentials for this url first')])
        if payload.type != StoreConfig.BUCKETSTORE and payload.s3_url:
            raise ValidationError([dict(error=f'Only StoreConfigs of type "{StoreConfig.BUCKETSTORE}" may update s3_url field')])
        store_config.bucket = payload.bucket
        store_config.save()

    @staticmethod
    def delete(pk:int):
        store_config = StoreConfig.objects.get(pk=pk)
        store_config.delete()

    @staticmethod
    def list() -> list[StoreConfigSchema]:
        store_configs = StoreConfig.objects.all()
        return [StoreService.serialize(store_config) for store_config in store_configs]


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
    def create(payload: MediaSchemaCreate, as_schema=True) -> MediaSchema:
        MediaService.clean_identifiers(payload)
        store_key = str(uuid.uuid4())  # CREATE STORE KEY #
        store_config,storeconfig_created = StoreService.create(payload.store_config, as_schema=False)
        try:
            media = Media.objects.create(
                pid = payload.pid,
                pid_type = payload.pid_type,
                store_config = store_config,
                store_key = store_key,
                store_status = StoreConfig.PENDING,
                identifiers = payload.identifiers, # already cleaned
                metadata = payload.metadata,
            )
        except IntegrityError as e:
            if str(e) == 'UNIQUE constraint failed: mediastore_media.store_key, mediastore_media.store_config_id':
                raise ValidationError([dict(error=f'store_key "{payload.store_key}" is not unique with this store_config')])
            else:
                raise ValidationError([dict(error=f'{type(e)}:{e}')])
        media.tags.set(payload.tags)
        if as_schema: return MediaService.serialize(media)
        return media

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
        store_config,storeconfig_created = StoreService.create(payload.store_config, as_schema=False)
        media = Media.objects.get(pid=pid)
        media.pid = payload.pid
        media.pid_type = payload.pid_type
        media.store_config = store_config
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
        if payload.store_config:
            store_config, storeconfig_created = StoreService.create(payload.store_config, as_schema=False)
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

    #TODO CRUD for metadata,identifiers,tags, store_key SPECIFICALLY
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
    def clean_identifiers(payload: type[MediaSchemaCreate|MediaSchemaUpdate], media_obj: type[Media|None] = None):
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



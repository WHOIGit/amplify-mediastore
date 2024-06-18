from pydantic import BaseModel

from mediastore.models import Media

class MediaInput(BaseModel):
    pid_type: str
    metadata: dict


class MediaOutput(BaseModel):
    pid: str
    pid_type: str
    metadata: dict


class MediaService:

    @staticmethod
    def serialize(media: Media) -> MediaOutput:
        return MediaOutput(
            pid=media.pid,
            pid_type=media.pid_type,
            metadata=media.metadata
        )

    @staticmethod
    def create(media_input: MediaInput) -> MediaOutput:
        media = Media.objects.create(
            # todo if not specified, create pid
            pid_type=media_input.pid_type,
            metadata=media_input.metadata
        )
        return MediaService.serialize(media)

    @staticmethod
    def read(pid: str) -> MediaOutput:
        media = Media.objects.get(pid=pid)
        return MediaService.serialize(media)

    @staticmethod
    def update(pid: str, media_input: MediaInput) -> str:
        return Media.objects.filter(pid=pid).update(
            pid_type=media_input.pid_type,
            metadata=media_input.metadata
        )

    @staticmethod
    def delete(pid: str) -> None:
        return Media.objects.filter(pid=pid).delete()

    @staticmethod
    def list() -> list[MediaOutput]:
        medias = Media.objects.all()
        return [MediaService.serialize(media) for media in medias]

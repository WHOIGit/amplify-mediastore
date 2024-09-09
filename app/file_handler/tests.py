import os
import base64

from django.utils.datastructures import MultiValueDict

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

import json
import io

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from ninja.testing import TestClient
from ninja import File
from ninja import UploadedFile
from rest_framework.authtoken.models import Token

from config.api import api

from mediastore.models import Media, IdentityType, StoreConfig, S3Config
from mediastore.schemas import MediaSchemaCreate,StoreConfigSchema, S3ConfigSchema

from .schemas import UploadSchemaInput, UploadSchemaOutput, DownloadSchemaInput, DownloadSchemaOutput

def encode64(content:bytes) -> str:
    encoded = base64.b64encode(content)
    return encoded.decode('ascii')

def decode64(content:str) -> bytes:
    content = content.encode("ascii")
    return base64.b64decode(content)


class FileHandlerFilestoreTests(TestCase):
    def setUp(self):
        IdentityType.objects.create(name='DEMO')
        self.filestore_dict = dict(StoreConfigSchema(type=StoreConfig.FILESYSTEMSTORE, bucket='/demobucket', s3_params=None))
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

    def test_upload_fs_minimal(self):
        PID = 'FSuploadPID'
        mediadata = dict(
            pid = PID, pid_type = 'DEMO',
            store_config = self.filestore_dict,
            store_key = 'test.txt')
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        return PID

    def test_download_fs_direct(self):
        PID = self.test_upload_fs_minimal()
        payload = dict(DownloadSchemaInput(pid=PID, direct=True))
        resp = self.client.post("/download", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        #print(data)
        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        uploaded_content = b'egg salad sand witch'
        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, uploaded_content)


class FileHandlerS3storeTests(TestCase):
    def setUp(self):
        IdentityType.objects.create(name='DEMO')
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

        self.s3_params,created_s3params = S3Config.objects.get_or_create(
            url=os.environ['TESTS_S3_URL'],
            access_key=os.environ['TESTS_S3_ACCESS'],
            secret_key=os.environ['TESTS_S3_SECRET'])
        self.s3store_dict = dict(StoreConfigSchema(type=StoreConfig.BUCKETSTORE, bucket=os.environ['TESTS_S3_BUCKET']))
        self.s3store_dict['s3_params'] = dict(url=self.s3_params.url, access_key=self.s3_params.access_key)

    def test_upload_s3_minimal(self):
        PID = 'S3uploadPID'
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.s3store_dict,
            store_key='test.txt'))
        upload_content = b'egg salad sand witch'
        encoded_content = encode64(upload_content)
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encoded_content))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        return PID

    def test_download_s3_direct(self):
        PID = self.test_upload_s3_minimal()
        payload = dict(DownloadSchemaInput(pid=PID, direct=True))
        resp = self.client.post("/download", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        uploaded_content = b'egg salad sand witch'
        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, uploaded_content)
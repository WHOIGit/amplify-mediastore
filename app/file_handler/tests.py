import os
import base64
import uuid
import json

os.environ["NINJA_SKIP_REGISTRY"] = "yes"

from django.test import TestCase
from ninja.testing import TestClient
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token

from config.api import api

from mediastore.models import Media, IdentityType, StoreConfig, S3Config
from mediastore.schemas import MediaSchemaCreate, StoreConfigSchema, S3ConfigSchema
from .schemas import UploadSchemaInput, DownloadSchemaInput

def encode64(content:bytes) -> str:
    encoded = base64.b64encode(content)
    return encoded.decode('ascii')

def decode64(content:str) -> bytes:
    content = content.encode("ascii")
    return base64.b64decode(content)


class FileHandlerFilestoreTests(TestCase):
    def setUp(self):
        IdentityType.objects.create(name='DEMO')
        self.storeconfig_dict = dict(StoreConfigSchema(type=StoreConfig.FILESYSTEMSTORE, bucket='/demobucket', s3_params=None))
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

    def test_updown_ram(self):
        PID = 'RAMuploadPID'
        mediadata = dict(
            pid = PID, pid_type = 'DEMO',
            store_config = self.storeconfig_dict,
            store_key = 'TESTS/test.txt')
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        #print(data)
        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)


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

    def test_updown_s3_direct(self):
        PID = 'S3uploadPID'
        mediadata = dict(MediaSchemaCreate(
            pid = PID, pid_type = 'DEMO',
            store_config = self.s3store_dict,
            store_key='TESTS/test.txt'))
        upload_content = b'egg salad sand witch'
        encoded_content = encode64(upload_content)
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encoded_content))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD DIRECT
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)

    def test_updown_s3_presigned(self):
        import requests
        PID = 'S3updownPresigned'
        mediadata = dict(MediaSchemaCreate(
            pid=PID, pid_type='DEMO',
            store_config=self.s3store_dict,
            store_key='TESTS/test2.txt'))
        upload_content = b'egg salad sand witch\n'+str(uuid.uuid1()).encode('ascii')
        payload = dict(UploadSchemaInput(mediadata=mediadata))  # sans base64 data
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        presigned_put = resp.json()['presigned_put']

        # Uploading file using presigned url for put.
        # Filename of uploaded file totally ignored, store_key from mediadata gets used.
        test_file = SimpleUploadedFile("TEST2.txt", upload_content)#, content_type="text/plain")
        download_response = requests.put(presigned_put, data=test_file)
        self.assertEqual(download_response.status_code, 200)

        # Fetching presigned S3 GET url
        resp = self.client.get(f"/download/url/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        presigned_get = json.loads(resp.content.decode())['presigned_get']

        # Downloading file using presigned GET url.
        # Filename of uploaded file totally ignored, store_key from mediadata gets used.
        download_response = requests.get(presigned_get)
        self.assertEqual(download_response.status_code, 200, download_response.content.decode())
        downloaded_content = download_response.content
        self.assertEqual(upload_content,downloaded_content)


class FileHandlerDictstoreTests(TestCase):
    def setUp(self):
        FileHandlerFilestoreTests.setUp(self)
        self.storeconfig_dict = dict(StoreConfigSchema(type=StoreConfig.DICTSTORE, bucket='/demobucket'))

    def test_updown_RAM(self):
        PID = 'RAMuploadPID'
        mediadata = dict(
            pid = PID, pid_type = 'DEMO',
            store_config = self.storeconfig_dict,
            store_key = 'TESTS/test.txt')
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)


class FileHandlerSqlitestoreTests(TestCase):
    def setUp(self):
        FileHandlerFilestoreTests.setUp(self)
        self.storeconfig_dict = dict(StoreConfigSchema(
            type=StoreConfig.SQLITESTORE, bucket='/demobucket/demodb.sqlite3'))

    def test_updown_Sqlite(self):
        PID = 'SqlitePID'
        mediadata = dict(
            pid = PID, pid_type = 'DEMO',
            store_config = self.storeconfig_dict,
            store_key = 'TESTS/test.txt')
        upload_content = b'egg salad sand witch'
        payload = dict(UploadSchemaInput(mediadata=mediadata, base64=encode64(upload_content)))
        resp = self.client.post("/upload", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        # DOWNLOAD
        resp = self.client.get(f"/download/{PID}")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        data = json.loads( resp.content.decode() )

        self.assertIn('mediadata', data)
        self.assertIn('store_status', data['mediadata'])
        store_status = data['mediadata']['store_status']
        self.assertEqual(store_status, StoreConfig.READY)

        downloaded_content = decode64( data['base64'] )
        self.assertEqual(downloaded_content, upload_content)
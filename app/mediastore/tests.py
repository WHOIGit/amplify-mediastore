import os
import uuid
os.environ["NINJA_SKIP_REGISTRY"] = "yes"

from django.test import TestCase
from ninja.testing import TestClient
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .models import Media, IdentityType, StoreConfig
from schemas.mediastore import StoreConfigSchema, StoreConfigSchemaCreate, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, \
    MediaSearchSchema, MediaSchemaUpdateIdentifiers, MediaSchemaUpdateMetadata, MediaSchemaUpdateTags

from config.api import api

def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

def whoami():
    import inspect
    return inspect.stack()[1][3]
def whosdaddy():
    import inspect
    return inspect.stack()[2][3]


class MediaApiTest(TestCase):

    def setUp(self):
        self.client = TestClient(api)
        IdentityType.objects.create(name='DEMO')
        IdentityType.objects.create(name='BIN')
        IdentityType.objects.create(name='DEMO2')
        self.demostore_dict = dict(StoreConfigSchemaCreate(type='FilesystemStore', bucket='/demobucket', s3_url=''))
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}

    def test_hello(self):
        response = self.client.get("/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "Hello, world!"})

    def test_MediaService_list(self):
        resp = self.client.get("/media/dump", headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_usertoken(self):
        user = User.objects.create_user(username='testuser2', password='uvwxyz')
        resp = self.client.post("/login", json=dict(username='testuser2', password='uvwxyz'))
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        token = resp.json()['token']
        resp2 = self.client.get("/media/dump", headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(resp2.status_code, 200, msg=resp2.content.decode())

    def test_MediaService_create(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
            metadata = {'egg':'nog'},
            identifiers = {'BIN':'bin_xyz'} )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_minimal(self):
        # minimal create
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        return resp

    def test_MediaService_create_dupeIDs(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            identifiers = {'DEMO':PID, 'BIN':'bin_xyz'},
            store_config = self.demostore_dict,
        )
        expected = dict(
            pid = PID,
            pid_type = 'DEMO',
            identifiers = {'BIN':'bin_xyz'},
            store_config=self.demostore_dict,
            store_status = StoreConfig.PENDING,
            metadata = {},
            tags = [],
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        resp2 = self.client.get(f"/media/{PID}", headers=self.auth_headers)
        received = resp2.json()
        received.pop('pk')
        received['store_config'].pop('pk')
        received = ordered(received)
        expected = ordered(expected)
        self.assertEqual(received, expected)

    def test_MediaService_create_dupeIDs_ambiguous(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
            identifiers = {'DEMO': f'not the {PID}', # this is different from above
                           'BIN': 'bin_xyz'},
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertNotEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_bad_identifiers(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
            identifiers = {'BIN': 123},
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 422, msg=resp.json())
        self.assertEqual(resp.json()['detail'][0]['msg'], 'Input should be a valid string')

    def test_MediaService_create_bad_identifier_types(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMOxxx',
            identifiers = {'BIN': '123'},
            store_config = self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        content = resp.json()
        self.assertEqual(resp.status_code, 422, msg=content)
        self.assertEqual(content["detail"][0]["error"], "bad pid_type: DEMOxxx", content["detail"])

        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            identifiers = {'BINxxx': '123'},
            store_config = self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        content = resp.json()
        self.assertEqual(resp.status_code, 422, msg=content)
        self.assertEqual(content["detail"][0]["error"], "bad identifier_type: BINxxx", content["detail"])

    def test_MediaService_create_uniquecheck(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        demo2 = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
        )
        resp2 = self.client.post("/media", json=demo2, headers=self.auth_headers)
        content = resp2.json()
        expected_error = "django.db.utils.IntegrityError"
        self.assertIn(expected_error, content["detail"][0]["error"], content["detail"])

    def test_MediaService_create_read_delete(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        resp2 = self.client.get(f"/media/{PID}", headers=self.auth_headers)
        self.assertEqual(resp2.status_code, 200, msg=resp2.content.decode())

        resp3 = self.client.delete(f"/media/{PID}", headers=self.auth_headers)
        self.assertEqual(resp3.status_code, 204, msg=resp3.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp4 = self.client.get(f"/media/{PID}", headers=self.auth_headers)


    def test_create_patch(self):
        PID = f'{whosdaddy()}.{whoami()}'
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
            metadata = {'egg':'nog', 'zip':'zap', 'quick':'quack'},
            tags = ['one', 'two'],
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  resp.json()
        PK = received1['pk']

        payload_tags = dict(MediaSchemaUpdateTags(pid=PID, tags=['two','three']))
        payload_ident = dict(MediaSchemaUpdateIdentifiers(pid=PID, identifiers={'DEMO2':'newvalue'}))
        payload_metadata = dict(pid=PID, data={'EGG':'NOG','zip':'ZAP'})  # MediaSchemaUpdateMetadata

        resp_tags = self.client.patch(f'/media/update/tags', json=[payload_tags], headers=self.auth_headers)
        self.assertEqual(resp_tags.status_code, 200, msg=resp_tags.content.decode())
        self.assertEqual(resp_tags.json()['successes'],[PID], resp_tags.content.decode())

        resp_ident = self.client.put(f'/media/update/identifiers', json=[payload_ident], headers=self.auth_headers)
        self.assertEqual(resp_ident.status_code, 200, msg=resp_ident.content.decode())
        self.assertEqual(resp_ident.json()['successes'],[PID], resp_ident.content.decode())

        resp_metadata = self.client.patch(f'/media/update/metadata', json=[payload_metadata], headers=self.auth_headers)
        self.assertEqual(resp_metadata.status_code, 200, msg=resp_metadata.content.decode())
        self.assertEqual(resp_metadata.json()['successes'],[PID], resp_metadata.content.decode())

        resp = self.client.get(f'/media/{PID}', headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received3 = resp.json()
        received3['store_config'].pop('pk')
        received3 = ordered(received3)

        expected = dict(
            pk = PK,
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
            store_status = StoreConfig.PENDING,
            identifiers = {'DEMO2':'newvalue'},
            metadata = {'egg':'nog', 'EGG':'NOG', 'zip':'ZAP', 'quick':'quack'},
            tags = ['one', 'two', 'three'],
        )
        expected = ordered(expected)
        self.assertEqual(received3, expected, msg=f'{received3} != {expected}')
        return PK


    def test_create_patch_dupeidentifiers(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config = self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  resp.json()
        PK = received1['pk']

        payload_ident = dict(MediaSchemaUpdateIdentifiers(
            pid=PID, identifiers={'DEMO2':'newvalue','DEMO':PID} ))
        # "'DEMO':PID" is what's different vs. test_create_patch

        resp_ident = self.client.put(f'/media/update/identifiers', json=[payload_ident], headers=self.auth_headers)
        self.assertEqual(resp_ident.status_code, 200, msg=resp_ident.content.decode())
        self.assertEqual(resp_ident.json()['successes'],[PID], resp_ident.content.decode())

        resp3 = self.client.get(f'/media/{PID}', headers=self.auth_headers)
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())
        received3 = resp3.json()
        received3['store_config'].pop('pk')
        received3 = ordered(received3)

        expected = dict(
            pk = PK,
            pid = PID,
            pid_type = 'DEMO',
            identifiers = {'DEMO2':'newvalue'},
            store_config = self.demostore_dict,
            store_status = StoreConfig.PENDING,
            metadata = {},
            tags = [],
        )
        expected = ordered(expected)
        self.assertEqual(received3, expected, msg=f'{received3} != {expected}')
        return PK


    def test_create_patch_dupeidentifiers_AMBIGUOUS(self):
        PID = whoami()
        payload = dict(
            pid = PID,
            pid_type = 'DEMO',
            store_config=self.demostore_dict,
        )
        resp = self.client.post("/media", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received1 =  resp.json()
        PK = received1['pk']

        payload_ident = dict(MediaSchemaUpdateIdentifiers(
            pid=PID, identifiers={'DEMO2':'newvalue','DEMO':f'not the {PID}'} ))
        # "'DEMO':not the PID" is what's different vs. test_create_patch_dupeidentifiers

        resp_ident = self.client.put(f'/media/update/identifiers', json=[payload_ident], headers=self.auth_headers)
        self.assertEqual(resp_ident.status_code, 200, msg=resp_ident.content.decode())
        returned_error = resp_ident.json()['failures'][0]
        self.assertEqual(returned_error['pid'],PID, resp_ident.content.decode())
        self.assertIn('ValidationError', returned_error['error'])
        self.assertIn('duplicate pid_type in identifiers DO NOT MATCH', returned_error['msg'])

    def test_BULK_create_search_read_delete(self):
        TAG = 'BULK'
        PID1 = whoami()+'_1'
        PID2 = whoami()+'_2'
        payload = [dict(pid=PID1, pid_type='DEMO', store_config=self.demostore_dict, tags=[TAG]),
                   dict(pid=PID2, pid_type='DEMO', store_config=self.demostore_dict, tags=[TAG]),]

        resp = self.client.post("/media/create", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        payload = dict(MediaSearchSchema(tags=[TAG]))
        resp = self.client.post("/media/search", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received_search = sorted(resp.json(), key=lambda m: m['pid'])
        pids = [m['pid'] for m in received_search]
        self.assertEqual(pids, sorted([PID1,PID2]), msg=resp.content.decode())

        resp = self.client.post("/media/read", json=[PID1, PID2], headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received_read = sorted(resp.json(), key=lambda m: m['pid'])
        self.assertEqual(received_read, received_search)

        # todo PATCH /media/update

        resp = self.client.post("/media/delete", json=[PID1, PID2], headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        expected = dict(successes=[PID1,PID2], failures=[])
        received_delete = resp.json()
        self.assertEqual(received_delete, expected)

    #todo
    # PUT /media/update/storekeys
    # PUT PATCH DELETE /media/update/metadata
    # PATCH /media/update
    # POST /media/search identifiers+pid w/ wildcard, metadata, store_status, store_key, pid_type

    def test_metadata(self):
        PID = whoami()
        d = {"a": {"r": 1,
                   "s": 2,
                   "t": 3},
             "b": {"u": 4,
                   "v": {"x": 5,
                         "y": 6,
                         "z": 7},
                   "w": 8}
             }
        expected = d.copy()
        payload = dict(pid=PID, pid_type='DEMO', store_config=self.demostore_dict, metadata=d)
        resp = self.client.post("/media/create", json=[payload], headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        payload_delete = dict(pid=PID, keys=['b','w'])
        del expected['b']['w']
        resp = self.client.delete("/media/update/metadata", json=[payload_delete], headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        resp = self.client.get(f'/media/{PID}', headers=self.auth_headers)
        received = resp.json()
        received_metadata = received['metadata']
        self.assertEqual(ordered(received_metadata),ordered(expected))




class MediaVersioningTest(TestCase):

    def setUp(self):
        MediaApiTest.setUp(self)

    def test_Versioning_patch(self):
        PK = MediaApiTest.test_create_patch(self)
        media = Media.objects.get(pk=PK)
        m1 = media.history.earliest()   # first one   .first() not correrct
        m2 = media.history.latest()     # most recent .last() not correct

        self.assertEqual(m1.metadata, {'egg':'nog', 'zip':'zap', 'quick':'quack'})
        self.assertEqual(m2.metadata, {'egg':'nog', 'EGG':'NOG', 'zip':'ZAP', 'quick':'quack'} )

        model_diff = m2.diff_against(m1)  # NEWER INSTANCE diff_against OLDER INSTANCE
        expected_changed_fields = sorted(['identifiers','metadata'])  # tags is foreign key and not diff'd
        self.assertEqual(sorted(model_diff.changed_fields), expected_changed_fields )

        metadata_changes = [modelchange for modelchange in model_diff.changes if modelchange.field=='metadata'][0]
        dict_diff = set(metadata_changes.new.items()) - set(metadata_changes.old.items())
        expected = {'EGG':'NOG','zip':'ZAP'}   # the PATCH that was used
        self.assertEqual(dict_diff, set(expected.items()))

        # METADATA dict COMPARE WORKS FOR PATCH (additive) BUT NOT PUT
        # for true comparison need "new KEYs (and val)"  "changed key:VALs"  "removed KEYs (and val)"
        # and that's out of scope for rn


class StoreCRUDTests(TestCase):

    def setUp(self):
        self.user, created_user = User.objects.get_or_create(username='testuser')
        self.token, created_token = Token.objects.get_or_create(user=self.user)
        self.auth_headers = {'Authorization':f'Bearer {self.token}'}
        self.client = TestClient(api, headers=self.auth_headers)

    def test_store_crud(self):
        # CREATE
        payload = dict(StoreConfigSchemaCreate(type='FilesystemStore', bucket='/demobucket', s3_url=''))
        resp = self.client.post("/store", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        received = resp.json()
        PK = received['pk']
        expected = dict(pk=PK, type='FilesystemStore', bucket='/demobucket', s3_url='')

        received,expected = ordered(received),ordered(expected)
        self.assertEqual(received, expected)

        # GET
        resp = self.client.get(f"/store/{PK}")
        received = resp.json()
        received = ordered(received)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(received, expected)

        # GET LIST
        resp = self.client.get(f"/stores")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(ordered(resp.json()), [expected])

        # DELETE
        resp = self.client.delete(f"/store/{PK}")
        self.assertEqual(resp.status_code, 204, msg=resp.content.decode())

        # GET LIST empty
        resp = self.client.get(f"/stores")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(resp.json(), [])


    def test_store_crud_s3(self):
        # CREATE S3CFG
        url1 = os.getenv('TESTS_S3_URL') or 'https://my.endpoint.s3'
        access_key = os.getenv('TESTS_S3_ACCESS') or 'bingus'
        secret_key = os.getenv('TESTS_S3_SECRET') or 'secretbingus'
        payload = dict(S3ConfigSchemaCreate(url=url1, access_key=access_key, secret_key=secret_key))

        resp = self.client.post("/s3cfg", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        received = resp.json()
        S3CFG_PK = received['pk']
        expected = dict(S3ConfigSchemaSansKeys(pk=S3CFG_PK, url=url1))
        self.assertEqual(ordered(received),ordered(expected))

        # GET S3CFG
        resp = self.client.get(f"/s3cfg/{S3CFG_PK}")
        self.assertEqual(ordered(resp.json()),ordered(expected))

        # PUT
        url2 = url1.replace('http','https')
        payload = dict(S3ConfigSchemaCreate(url=url2, access_key=access_key, secret_key=secret_key))
        resp = self.client.put(f"/s3cfg/{S3CFG_PK}", json=payload)
        self.assertEqual(resp.status_code, 204, msg=resp.content.decode())

        # GET S3CFG list
        resp = self.client.get(f"/s3cfgs")
        expected = dict(S3ConfigSchemaSansKeys(pk=S3CFG_PK, url=url2))
        self.assertEqual(ordered(resp.json()), [ordered(expected)])


        # CREATE Store
        payload = dict(StoreConfigSchemaCreate(type='BucketStore', bucket='/demobucket', s3_url=url2))
        resp = self.client.post("/store", json=payload)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

        received = resp.json()
        STORE_PK = received['pk']
        expected = dict(pk=STORE_PK, type='BucketStore', bucket='/demobucket', s3_url=url2)

        received,expected = ordered(received),ordered(expected)
        self.assertEqual(received, expected)

        # GET Store
        resp = self.client.get(f"/store/{STORE_PK}")
        received = resp.json()
        received = ordered(received)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(received, expected)

        # GET Store LIST
        resp = self.client.get(f"/stores")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(ordered(resp.json()), [expected])

        # DELETE Store
        resp = self.client.delete(f"/store/{STORE_PK}")
        self.assertEqual(resp.status_code, 204, msg=resp.content.decode())
        # GET Store LIST empty
        resp = self.client.get(f"/stores")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(resp.json(), [])

        # DELETE S3CFG
        resp = self.client.delete(f"/s3cfg/{S3CFG_PK}")
        self.assertEqual(resp.status_code, 204, msg=resp.content.decode())
        # GET S3CFG LIST empty
        resp = self.client.get(f"/s3cfgs")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        self.assertEqual(resp.json(), [])

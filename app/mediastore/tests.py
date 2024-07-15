import os
os.environ["NINJA_SKIP_REGISTRY"] = "yes"
import json

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError
from ninja.testing import TestClient

from .models import Media, Identity
from .schemas import MediaSchema, IdentitySchema
from .services import MediaService

from .views import api

class MediaApiTest(TestCase):


    def setUp(self):
        self.client = TestClient(api)

    def test_hello(self):
        response = self.client.get("/hello")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "Hello, world!"})

    def test_MediaService_list(self):
        resp = self.client.get("/media")
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_id1(self):
        m1 = dict(metadata={'egg': 'nog'},
                  ids=[dict(type='AMP', token='m1')])
        resp = self.client.post("/media", json=m1)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_id2(self):
        # multiple pid
        m2 = dict(metadata={},
                  ids=[dict(type='AMP', token='m2', is_pid=True),
                       dict(type='OBJ', token='bucketA:xyz123')])
        resp = self.client.post("/media", json=m2)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())

    def test_MediaService_create_id3_bad(self):
        # ambiguous pid
        m3 = dict(metadata={},
                  ids=[dict(type='AMP', token='m3'),
                       dict(type='OBJ', token='bucketA:xyz123')])
        with self.assertRaises(ValidationError):
            self.client.post("/media", json=m3)

    def test_MediaService_create_id4_bad(self):
        # multiple pid
        m4 = dict(metadata={},
                  ids=[dict(type='AMP', token='m4', is_pid=True),
                       dict(type='OBJ', token='bucketA:xyz123', is_pid=True)])
        with self.assertRaises(ValidationError):
            resp = self.client.post("/media", json=m4)

    def test_MediaService_create_id5_once(self):
        # pid already exists
        m5 = dict(metadata={},
                  ids=[dict(type='AMP', token='m5', is_pid=True),
                       dict(type='OBJ', token='bucketA:xyz123')])
        resp = self.client.post("/media", json=m5)
        self.assertEqual(resp.status_code, 200, msg=resp.content.decode())
        m5b = dict(metadata={},
                   ids=[dict(type='AMP', token='m5', is_pid=True),  # should already exist
                        dict(type='FLN', token='myfile.txt')])      # even if this different
        with self.assertRaises(IntegrityError):
            resp2 = self.client.post("/media", json=m5b)

    def test_MediaService_create_put_read_delete(self):
        m6 = MediaSchema(metadata={'egg':'nog'},
                ids=[IdentitySchema(type='AMP', token='m6', is_pid=True)])
        resp1 = self.client.post("/media", json=m6.dict())
        self.assertEqual(resp1.status_code, 200, msg=resp1.content.decode())
        m6b = MediaSchema(metadata={'EGG':'NOG'},
                ids=[IdentitySchema(type='AMP', token='new_m6', is_pid=True)])
        resp2 = self.client.put("/media/m6", json=m6b.dict())
        self.assertEqual(resp2.status_code, 204, msg=resp2.content.decode())
        expected = {"metadata": {"EGG": "NOG"},
                    "ids": [{"type": "AMP", "token": "new_m6", "is_pid": True}]}
        resp3 = self.client.get("/media/new_m6")
        received = resp3.content.decode()
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())

        def ordered(obj):
            if isinstance(obj, dict):
                return sorted((k, ordered(v)) for k, v in obj.items())
            if isinstance(obj, list):
                return sorted(ordered(x) for x in obj)
            else:
                return obj

        received = ordered(json.loads(received))
        expected = ordered(expected)
        self.assertEqual(received, expected, msg=f'{received} != {expected}')

        resp4 = self.client.get("/media")
        self.assertEqual(resp4.status_code, 200, msg=resp4.content.decode())
        received = ordered(json.loads(resp4.content.decode()))
        self.assertEqual(received, [expected], msg=resp4.content.decode())

        resp5 = self.client.delete("/media/new_m6")
        self.assertEqual(resp5.status_code, 204, msg=resp5.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp6 = self.client.get("/media/new_m6")

        resp7 = self.client.get("/media")
        self.assertEqual(resp7.status_code, 200, msg=resp7.content.decode())
        self.assertEqual(resp7.content.decode(), '[]', msg=resp7.content.decode())


    def test_MediaService_create_read_delete_detailed(self):
        m7 = MediaSchema(metadata={'egg':'nog'},
                ids=[IdentitySchema(type='AMP', token='m7', is_pid=True)])
        resp1 = self.client.post("/media", json=m7.dict())
        self.assertEqual(resp1.status_code, 200, msg=resp1.content.decode())
        resp2 = self.client.get("/media/m7")
        received = resp2.content.decode()
        self.assertEqual(resp2.status_code, 200, msg=resp2.content.decode())

        def ordered(obj):
            if isinstance(obj, dict):
                return sorted((k, ordered(v)) for k, v in obj.items())
            if isinstance(obj, list):
                return sorted(ordered(x) for x in obj)
            else:
                return obj

        received = ordered(json.loads(received))
        expected = ordered(m7.dict())
        self.assertEqual(received, expected, msg=f'{received} != {expected}')

        resp3 = self.client.get("/media")
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())
        received = ordered(json.loads(resp3.content.decode()))
        self.assertEqual(received, [expected], msg=resp3.content.decode())

        resp4 = self.client.delete("/media/m7")
        self.assertEqual(resp4.status_code, 204, msg=resp4.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp5 = self.client.get("/media/m7")

        resp6 = self.client.get("/media")
        self.assertEqual(resp6.status_code, 200, msg=resp6.content.decode())
        self.assertEqual(resp6.content.decode(), '[]', msg=resp6.content.decode())


    def test_MediaService_create_read_delete(self):
        m8 = MediaSchema(metadata={'egg':'nog'},
                ids=[IdentitySchema(type='AMP', token='m8', is_pid=True)])
        resp1 = self.client.post("/media", json=m8.dict())
        self.assertEqual(resp1.status_code, 200, msg=resp1.content.decode())
        resp2 = self.client.get("/media/m8")
        self.assertEqual(resp2.status_code, 200, msg=resp2.content.decode())

        resp3 = self.client.delete("/media/m8")
        self.assertEqual(resp3.status_code, 204, msg=resp3.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp4 = self.client.get("/media/m8")

    def test_MediaService_create_patch_read(self):
        m9 = MediaSchema(metadata={'egg':'nog'},
                ids=[IdentitySchema(type='AMP', token='m9', is_pid=True)])
        resp1 = self.client.post("/media", json=m9.dict())
        self.assertEqual(resp1.status_code, 200, msg=resp1.content.decode())
        m9b = MediaSchema(metadata={'EGG':'NOG'},
                ids=[IdentitySchema(type='OBJ', token='quack', is_pid=False)])
        resp2 = self.client.patch("/media/m9", json=m9b.dict())
        self.assertEqual(resp2.status_code, 204, msg=resp2.content.decode())
        expected = {"metadata": {"EGG": "NOG", 'egg':'nog'},
                    "ids": [{"type": "AMP", "token": "m9", "is_pid": True},
                            {"type": "OBJ", "token": "quack", "is_pid": False}]}
        resp3 = self.client.get("/media/m9")
        received = resp3.content.decode()
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())

        def ordered(obj):
            if isinstance(obj, dict):
                return sorted((k, ordered(v)) for k, v in obj.items())
            if isinstance(obj, list):
                return sorted(ordered(x) for x in obj)
            else:
                return obj

        received = ordered(json.loads(received))
        expected = ordered(expected)
        self.assertEqual(received, expected, msg=f'{received} != {expected}')

        resp4 = self.client.get("/media")
        self.assertEqual(resp4.status_code, 200, msg=resp4.content.decode())
        received = ordered(json.loads(resp4.content.decode()))
        self.assertEqual(received, [expected], msg=resp4.content.decode())

        resp5 = self.client.delete("/media/m9")
        self.assertEqual(resp5.status_code, 204, msg=resp5.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp6 = self.client.get("/media/m9")

        resp7 = self.client.get("/media")
        self.assertEqual(resp7.status_code, 200, msg=resp7.content.decode())
        self.assertEqual(resp7.content.decode(), '[]', msg=resp7.content.decode())

    def test_MediaService_create_patch2_read(self):
        mA = MediaSchema(metadata={'egg':'nog', 'quick':'quack', 'ping':'pong'},
                ids=[IdentitySchema(type='AMP', token='mA', is_pid=True)])
        resp1 = self.client.post("/media", json=mA.dict())
        self.assertEqual(resp1.status_code, 200, msg=resp1.content.decode())
        mA = MediaSchema(metadata={'EGG':'NOG', 'quick':'QUACK'},
                ids=[IdentitySchema(type='AMP', token='mA', is_pid=False),
                     IdentitySchema(type='OBJ', token='quack', is_pid=True)])
        resp2 = self.client.patch("/media/mA", json=mA.dict())
        self.assertEqual(resp2.status_code, 204, msg=resp2.content.decode())
        expected = {"metadata": {"EGG": "NOG", 'egg':'nog', 'quick':'QUACK', 'ping':'pong'},
                    "ids": [{"type": "AMP", "token": "mA", "is_pid": False},
                            {"type": "OBJ", "token": "quack", "is_pid": True}]}
        resp3 = self.client.get("/media/quack")
        received = resp3.content.decode()
        self.assertEqual(resp3.status_code, 200, msg=resp3.content.decode())

        def ordered(obj):
            if isinstance(obj, dict):
                return sorted((k, ordered(v)) for k, v in obj.items())
            if isinstance(obj, list):
                return sorted(ordered(x) for x in obj)
            else:
                return obj

        received = ordered(json.loads(received))
        expected = ordered(expected)
        self.assertEqual(received, expected, msg=f'{received} != {expected}')

        resp4 = self.client.get("/media")
        self.assertEqual(resp4.status_code, 200, msg=resp4.content.decode())
        received = ordered(json.loads(resp4.content.decode()))
        self.assertEqual(received, [expected], msg=resp4.content.decode())

        resp5 = self.client.delete("/media/quack")
        self.assertEqual(resp5.status_code, 204, msg=resp5.content.decode())

        with self.assertRaises(ObjectDoesNotExist):
            resp6 = self.client.get("/media/quack")

        resp7 = self.client.get("/media")
        self.assertEqual(resp7.status_code, 200, msg=resp7.content.decode())
        self.assertEqual(resp7.content.decode(), '[]', msg=resp7.content.decode())
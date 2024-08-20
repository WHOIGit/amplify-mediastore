import os
os.environ["NINJA_SKIP_REGISTRY"] = "yes"

import json

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from ninja.testing import TestClient
from rest_framework.authtoken.models import Token



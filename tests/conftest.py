import os

import pytest
from django.http import HttpRequest
from rest_framework.request import Request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django.settings")


@pytest.fixture()
def drf_request() -> Request:
    return Request(HttpRequest())

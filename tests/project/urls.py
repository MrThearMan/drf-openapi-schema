from contextlib import suppress
from typing import Any

from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import include, path
from django.views.generic import TemplateView
from pipeline_views.serializers import HeaderAndCookieSerializer
from pipeline_views.typing import Optional
from pipeline_views.views import BasePipelineView
from pydantic import BaseModel
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from openapi_schema.schema import OpenAPISchema
from openapi_schema.utils import deprecate
from openapi_schema.views import get_schema_view

with suppress(Exception):
    call_command("makemigrations")
    call_command("migrate")
    if not User.objects.filter(username="x", email="user@user.com").exists():
        User.objects.create_superuser(username="x", email="user@user.com", password="x")


class InputSerializer(serializers.Serializer):
    """Example Input"""

    name = serializers.CharField()
    age = serializers.IntegerField()


class OutputSerializer(serializers.Serializer):
    """Example Output"""

    email = serializers.EmailField()
    age = serializers.IntegerField()


class HeaderAndCookieInputSerializer(HeaderAndCookieSerializer):
    """Example Input"""

    take_from_headers = ["Header-Name"]
    take_from_cookies = ["Cookie-Name"]

    name = serializers.CharField()
    age = serializers.IntegerField()


class HeaderAndCookieOutputSerializer(serializers.Serializer):
    """Example Input"""

    email = serializers.EmailField()
    age = serializers.IntegerField()
    header_name = serializers.CharField(allow_null=True, required=False, allow_blank=True)
    cookie_name = serializers.CharField(allow_null=True, required=False, allow_blank=True)


class PydanticInput(BaseModel):
    name: str
    age: int


class PydanticOutput(BaseModel):
    email: str
    age: int


def example_method(name: str, age: int):
    return {"email": f"{name.lower()}@email.com", "age": age}


def example_header_and_cookie_method(name: str, age: int, header_name: Optional[str], cookie_name: Optional[str]):
    return {"email": f"{name.lower()}@email.com", "age": age, "header_name": header_name, "cookie_name": cookie_name}


class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }

    schema = OpenAPISchema()


class ExampleWebhook(BasePipelineView):
    """Example Webhook"""

    pipelines = {
        "POST": [
            InputSerializer,
            OutputSerializer,
        ],
    }

    schema = OpenAPISchema()


class ExamplePathView(BasePipelineView):
    """Example Path View"""

    pipelines = {
        "PATCH": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }

    schema = OpenAPISchema(
        public={
            "PATCH": True,
        },
    )


class ExampleHeaderAndCookieView(BasePipelineView):
    """Example Header View"""

    pipelines = {
        "PATCH": [
            HeaderAndCookieInputSerializer,
            example_header_and_cookie_method,
            HeaderAndCookieOutputSerializer,
        ],
    }

    schema = OpenAPISchema(
        public={
            "PATCH": True,
        },
    )


class ExamplePrivateView(BasePipelineView):
    """Example View"""

    permission_classes = [IsAuthenticated]

    pipelines = {
        "PUT": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }

    schema = OpenAPISchema(
        public={
            "PUT": False,
        },
    )


@deprecate(methods=["GET"])
class PydanticView(BasePipelineView):
    """Pydantic View"""

    pipelines = {
        "GET": [
            PydanticInput,
            example_method,
            PydanticOutput,
        ],
    }

    schema = OpenAPISchema()


class PlainView(APIView):
    """Plain API View"""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(data={"json": "foo"})


class PlainViewSet(ViewSet):
    """Plain ViewSet"""

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(data={"json": "foo"})


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
        ]


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


router = DefaultRouter()
router.register(r"plain/viewset", PlainViewSet, basename="test_plain_viewset")
router.register(r"users", UserViewSet, basename="test_users")


urlpatterns = [
    path("api/example/", ExampleView.as_view(), name="test_view"),
    path("api/example/deprecated", deprecate(ExampleView).as_view(), name="test_view_deprecated"),
    path("api/example/<int:age>", ExamplePathView.as_view(), name="test_path_view"),
    path("api/example/headers-and-cookies", ExampleHeaderAndCookieView.as_view(), name="test_header_and_cookie_view"),
    path("api/example/private", ExamplePrivateView.as_view(), name="test_private_view"),
    path("api/pydantic", PydanticView.as_view(), name="test_pydantic_view"),
    path("api/plain", PlainView.as_view(), name="test_plain_view"),
    path("api/", include(router.urls)),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            root_url="api",
            description="API for all things",
            version="1.0.0",
            webhooks={
                "ExampleWebhook": {
                    "method": "POST",
                    "request_data": InputSerializer,
                    "responses": {
                        200: OutputSerializer,
                    },
                },
            },
            contact={"email": "user@example.com"},
            license={"name": "MIT"},
            terms_of_service="example.com",
            security_schemes={
                "my_security": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
                "another": {
                    "type": "http",
                    "scheme": "basic",
                },
            },
            security_rules={
                AllowAny: {
                    "my_security": [],
                },
                (IsAuthenticated,): {
                    "another": [],
                },
            },
        ),
        name="openapi-schema",
    ),
    path(
        "swagger-ui/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
]

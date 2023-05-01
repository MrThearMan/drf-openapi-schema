from django.urls import URLPattern, URLResolver
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.renderers import BrowsableAPIRenderer, JSONOpenAPIRenderer, OpenAPIRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from .generator import OpenAPISchemaGenerator
from .typing import (
    APIContact,
    APILicense,
    APISecurityScheme,
    AsView,
    EventName,
    GenericView,
    ModuleType,
    Optional,
    SchemaWebhook,
    SchemeName,
    SecurityRules,
    Union,
    UrlPath,
)


class OpenAPISchemaView(APIView):
    _ignore_model_permissions: bool = True
    schema = None  # exclude from schema
    schema_generator = OpenAPISchemaGenerator()
    renderer_classes = [OpenAPIRenderer, JSONOpenAPIRenderer]
    public: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if BrowsableAPIRenderer in api_settings.DEFAULT_RENDERER_CLASSES:
            self.renderer_classes += [BrowsableAPIRenderer]

    def get(self, request: Request, *args, **kwargs) -> Response:
        schema = self.schema_generator.get_schema(request, self.public)
        return Response(schema)

    def handle_exception(self, exc: Exception) -> Response:  # pragma: no cover
        # Schema renderers do not render exceptions, so re-perform content
        # negotiation with default renderers.
        self.renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
        neg = self.perform_content_negotiation(self.request, force=True)
        self.request.accepted_renderer, self.request.accepted_media_type = neg
        return super().handle_exception(exc)


def get_schema_view(
    *,
    title: Optional[str] = None,
    root_url: Optional[UrlPath] = None,
    description: Optional[str] = None,
    patterns: Optional[list[Union[URLPattern, URLResolver]]] = None,
    urlconf: Optional[Union[str, ModuleType]] = None,
    version: Optional[str] = None,
    webhooks: Optional[dict[EventName, SchemaWebhook]] = None,
    contact: Optional[APIContact] = None,
    license: Optional[APILicense] = None,
    terms_of_service: UrlPath = "",
    public: Optional[bool] = None,
    security_schemes: Optional[dict[SchemeName, APISecurityScheme]] = None,
    security_rules: Optional[SecurityRules] = None,
    authentication_classes: Optional[list[type[BaseAuthentication]]] = None,
    permission_classes: Optional[list[type[BasePermission]]] = None,
) -> AsView[GenericView]:
    """Return a schema view.

    :param title: The name of the API (required).
    :param root_url: The root URL prefix of the API schema. Useful for defining versioned API.
    :param description: Longer descriptive text.
    :param patterns: A list of URLs to inspect when generating the schema.
                     Defaults to the project's URL conf.
    :param urlconf: A URL conf module to use when generating the schema.
                    Defaults to settings.ROOT_URLCONF.
    :param version: The version of the API. Defaults to 0.1.0.
    :param webhooks: Webhooks defined in the API.
    :param contact: API developer contact information.
    :param license: API license information.
    :param terms_of_service: API terms of service link.
    :param public: If False, hide endpoint schema if the user does not have permissions to view it.
    :param security_schemes: Mapping of security scheme name to its definition.
    :param security_rules: Security schemes to apply if defined authentication or
                           permission class(es) exist on an endpoint.
    :param authentication_classes: Authentication classes for the OpenAPI SchemaView.
    :param permission_classes: Permission classes for the OpenAPI SchemaView.
    """

    generator = OpenAPISchemaGenerator(
        title=title,
        root_url=root_url,
        description=description,
        patterns=patterns,
        urlconf=urlconf,
        version=version,
        webhooks=webhooks,
        contact=contact,
        license=license,
        security_schemes=security_schemes,
        security_rules=security_rules,
        terms_of_service=terms_of_service,
    )

    return OpenAPISchemaView.as_view(  # type: ignore
        schema_generator=generator,
        public=public,
        authentication_classes=(
            authentication_classes
            if authentication_classes is not None
            else api_settings.DEFAULT_AUTHENTICATION_CLASSES
        ),
        permission_classes=(
            permission_classes if permission_classes is not None else api_settings.DEFAULT_PERMISSION_CLASSES
        ),
    )

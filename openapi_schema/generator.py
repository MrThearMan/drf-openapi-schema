from importlib import import_module
from types import ModuleType

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import URLPattern, URLResolver
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.serializers import ListSerializer

from .typing import (
    APIContact,
    APIInfo,
    APILicense,
    APIOperation,
    APIPathItem,
    APISchema,
    APISecurityScheme,
    CompatibleView,
    ComponentName,
    EventName,
    HTTPMethod,
    OpenAPI,
    Optional,
    PathAndMethod,
    SchemaWebhook,
    SchemeName,
    SecurityRules,
    Union,
    UrlPath,
)
from .utils import (
    get_api_endpoints,
    get_local_path,
    is_serializer_class,
    map_serializer,
    warn_component_override,
    warn_method_override,
)


class OpenAPISchemaGenerator:
    def __init__(
        self,
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
        security_schemes: Optional[dict[SchemeName, APISecurityScheme]] = None,
        security_rules: Optional[SecurityRules] = None,
        terms_of_service: UrlPath = "",
    ):
        """Custom Schema Generator for Django Rest Framework views.

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
        :param security_schemes: Mapping of security scheme name to its definition.
        :param security_rules: Security schemes to apply if defined authentication or
                               permission class(es) exist on an endpoint.
        :param terms_of_service: API terms of service link.
        """

        if root_url is None:
            root_url = "/"
        else:
            # 'root_url' should always start with a '/' and never end in a '/'
            root_url = root_url.removesuffix("/")
            if not root_url.startswith("/"):
                root_url = "/" + root_url

        self.title = title
        self.root_url = root_url
        self.description = description
        self.patterns = patterns
        self.urlconf = urlconf
        self.version = version
        self.webhooks = webhooks or {}
        self.contact = contact or {}
        self.license = license or {}
        self.security_schemes = security_schemes or {}
        self.security_rules = security_rules or {}
        self.terms_of_service = terms_of_service
        self.endpoints: Optional[list[tuple[str, HTTPMethod, CompatibleView]]] = None

    def get_endpoints(self, request: Optional[Request]) -> list[tuple[UrlPath, HTTPMethod, CompatibleView]]:
        if self.endpoints is None:
            if self.patterns is None:
                if self.urlconf is None:
                    self.urlconf = settings.ROOT_URLCONF
                if isinstance(self.urlconf, str):
                    self.urlconf = import_module(self.urlconf)

                self.patterns = self.urlconf.urlpatterns

            self.endpoints = get_api_endpoints(patterns=self.patterns, root=self.root_url, request=request)
        return self.endpoints

    def get_schema(self, request: Optional[Request], public: bool) -> OpenAPI:
        schema: OpenAPI = OpenAPI(openapi="3.0.2", info=self.get_info())

        operation_ids: dict[str, PathAndMethod] = {}

        for path, method, view in self.get_endpoints(None if public else request):
            self.set_security_schemes(method, view)

            if not self.has_view_permissions(view, method, public):
                continue  # pragma: no cover

            local_path = get_local_path(path, self.root_url)

            new_operation = self.get_operation(local_path, method, view)
            if new_operation:
                operation_id = new_operation["operationId"]
                if operation_id in operation_ids:
                    warn_method_override(path, method, operation_id, operation_ids)  # pragma: no cover

                operation_ids[operation_id] = PathAndMethod(path=path, method=method)
                schema.setdefault("paths", {}).setdefault(path, {})
                schema["paths"][path][method.lower()] = new_operation

            new_components = self.get_components(local_path, method, view)
            if new_components:
                schema.setdefault("components", {}).setdefault("schemas", {})

                for name, component in new_components.items():
                    if component != schema["components"]["schemas"].get(name, component):
                        warn_component_override(name)  # pragma: no cover

                schema["components"]["schemas"].update(new_components)

        webhooks = self.get_webhook()
        if webhooks:
            schema.setdefault("webhooks", {})
            schema["webhooks"].update(webhooks)

        if self.security_schemes:
            schema.setdefault("components", {}).setdefault("securitySchemes", {})
            schema["components"]["securitySchemes"] = self.security_schemes

        return schema

    def get_info(self) -> APIInfo:
        info = APIInfo(
            title=self.title or "",
            version=self.version or "",
        )
        if self.description is not None:
            info["description"] = self.description
        if self.contact:
            info["contact"] = self.contact
        if self.license:
            info["license"] = self.license
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service
        return info

    def set_security_schemes(self, method: HTTPMethod, view: CompatibleView) -> None:
        if hasattr(view.schema, "security"):
            for classes, rules in self.security_rules.items():
                if not isinstance(classes, tuple):
                    classes = (classes,)

                if any(cls in view.permission_classes or cls in view.authentication_classes for cls in classes):
                    view.schema.security.setdefault(method, {})
                    # View specific rules take higher priority
                    view.schema.security[method] = {**rules, **view.schema.security[method]}

    def has_view_permissions(self, view: CompatibleView, method: HTTPMethod, public: bool) -> bool:
        method_public: Optional[bool] = getattr(view.schema, "public", {}).get(method, None)

        if method_public is True:
            return True

        if public and method_public is not False:
            return True  # pragma: no cover

        if view.request is None:
            return True  # pragma: no cover

        try:
            view.check_permissions(view.request)
        except (APIException, Http404, PermissionDenied):  # pragma: no cover
            return False

        return True

    def get_operation(
        self,
        local_path: UrlPath,
        method: HTTPMethod,
        view: CompatibleView,
    ) -> APIOperation:
        return view.schema.get_operation(local_path, method)

    def get_components(
        self,
        local_path: UrlPath,
        method: HTTPMethod,
        view: CompatibleView,
    ) -> dict[ComponentName, APISchema]:
        return view.schema.get_components(local_path, method)

    def get_webhook(self) -> dict[EventName, APIPathItem]:
        webhooks: dict[EventName, APIPathItem] = {}  # type: ignore

        for webhook_name, webhook in self.webhooks.items():
            input_serializer = webhook["request_data"](many=getattr(webhook["request_data"], "many", False))
            if isinstance(input_serializer, ListSerializer):
                input_serializer = getattr(input_serializer, "child", input_serializer)  # pragma: no cover

            webhooks[webhook_name] = {  # type: ignore
                webhook["method"]: APIOperation(
                    requestBody={
                        "description": input_serializer.__class__.__doc__ or "",
                        "content": {
                            "application/json": {
                                "schema": map_serializer(input_serializer),
                            },
                        },
                    },
                    # TODO: Handle unions
                    responses={  # type: ignore
                        str(status_code): {
                            "description": response.__doc__ or "",
                            "content": {"application/json": map_serializer(response)},
                        }
                        if is_serializer_class(response)
                        else {"description": response or ""}
                        for status_code, response in webhook["responses"].items()
                    },
                ),
            }

        return webhooks

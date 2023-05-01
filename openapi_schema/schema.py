import re
from contextlib import suppress
from inspect import cleandoc

from django.utils.encoding import smart_str
from rest_framework.permissions import AllowAny
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.serializers import ListSerializer, Serializer
from serializer_inference import (
    MockSerializer,
    serializer_from_callable,
    snake_case_to_camel_case,
    snake_case_to_pascal_case,
)

from .typing import (
    APIExternalDocumentation,
    APILinks,
    APIOperation,
    APIParameter,
    APIPathItem,
    APIRequestBody,
    APIResponses,
    APISchema,
    CompatibleView,
    ComponentName,
    CookieParameter,
    EventName,
    HeaderParameter,
    HTTPMethod,
    MediaType,
    OperationBaseName,
    Optional,
    QueryParameter,
    ResponseKind,
    SchemaCallbackData,
    SchemeName,
    ScopeName,
    SerializerOrSerializerType,
    SerializerType,
    StatusCode,
    TagName,
    Union,
    UrlPath,
)
from .utils import (
    EmptySerializer,
    convert_to_schema,
    get_path_parameters,
    is_serializer_class,
    map_field,
    map_serializer,
    serializer_pattern,
)


class OpenAPISchema:
    def __init__(
        self,
        *,
        responses: Optional[dict[HTTPMethod, dict[StatusCode, Union[ResponseKind, list[ResponseKind]]]]] = None,
        callbacks: Optional[dict[EventName, dict[UrlPath, dict[HTTPMethod, SchemaCallbackData]]]] = None,
        links: Optional[dict[HTTPMethod, dict[StatusCode, dict[EventName, APILinks]]]] = None,
        query_parameters: Optional[dict[HTTPMethod, list[QueryParameter]]] = None,
        header_parameters: Optional[dict[HTTPMethod, list[HeaderParameter]]] = None,
        cookie_parameters: Optional[dict[HTTPMethod, list[CookieParameter]]] = None,
        deprecated: Optional[list[HTTPMethod]] = None,
        security: Optional[dict[HTTPMethod, dict[SchemeName, list[ScopeName]]]] = None,
        external_docs: Optional[dict[HTTPMethod, APIExternalDocumentation]] = None,
        public: Optional[dict[HTTPMethod, bool]] = None,
        tags: Optional[list[TagName]] = None,
        operation_id_base: Optional[OperationBaseName] = None,
    ):
        """Create an OpenAPI 3.0.2 schema for a Django Rest Framework view.

        :param responses: Additional responses given in the endpoints.
        :param callbacks: Asynchronous, out-of-band requests that are made on the endpoint.
                          https://swagger.io/docs/specification/callbacks/
        :param links: Describes how the endpoints relate to other endpoints.
                      https://swagger.io/docs/specification/links/
        :param query_parameters: Which parameters in the input serializer are query parameters?
        :param header_parameters: Which parameters in the input serializer are header parameters?
        :param cookie_parameters: Which parameters in the input serializer are cookie parameters?
        :param deprecated: Is this endpoint deprecated?
        :param security: Which security schemes the endpoints use.
        :param external_docs: External docs for the endpoints.
        :param public: Is the endpoint public or not?
        :param tags: User-defined tags for the endpoint. If not set, will be deducted from the path.
        :param operation_id_base: User-defined operation ID for the endpoint.
                                  If not set, it will be deducted from the input serializer.
        """
        self.responses = responses or {}
        self.callbacks = callbacks or {}
        self.links = links or {}
        self.query_parameters = query_parameters or {}
        self.header_parameters = header_parameters or {}
        self.cookie_parameters = cookie_parameters or {}
        self.deprecated = deprecated or {}
        self.security = security or {}
        self.external_docs = external_docs or {}
        self.public = public or {}
        self.operation_id_base = operation_id_base
        self.tags = tags

        self.__view: Optional[CompatibleView] = None

    def __get__(self, instance: Optional[CompatibleView], owner: type[CompatibleView]) -> "OpenAPISchema":
        self.__view = instance
        return self

    @property
    def view(self) -> CompatibleView:
        if self.__view is None:  # pragma: no cover
            raise AttributeError(
                "View has not been set. "
                "Schema accessed on a view class and not an instance, or not used as a descriptor."
            )
        return self.__view

    def get_description(self) -> str:
        serializer_class = self.view.get_serializer_class()
        description = serializer_class.__doc__ or (self.view.__class__.__doc__ or "")
        return cleandoc(smart_str(description))

    def get_operation_id(self, path: UrlPath, method: HTTPMethod) -> str:
        path_part = snake_case_to_pascal_case(re.sub(r"\W", "_", re.sub(r"[{}]", "", path.lower())))

        method_mapping = {
            "GET": "retrieve",
            "POST": "create",
            "PUT": "update",
            "PATCH": "partialUpdate",
            "DELETE": "destroy",
        }

        action = "list"
        if not getattr(self.get_response_serializer_class(), "many", False):
            action = method_mapping.get(method) or snake_case_to_camel_case(method.lower())

        if self.operation_id_base is not None:
            return action + self.operation_id_base + path_part

        serializer_class_name = self.get_request_serializer_class().__name__
        operation_id_base = serializer_pattern.sub("", serializer_class_name)

        if operation_id_base == "":
            raise ValueError(  # pragma: no cover
                f"{serializer_class_name!r} is an invalid class name for schema generation. "
                f"Serializer's class name should be unique and explicit. e.g., 'ItemSerializer'."
            )

        return action + operation_id_base + path_part

    def get_tags(self, path: UrlPath) -> list[TagName]:
        if self.tags:
            return self.tags

        return [path.split("/")[0].replace("_", "-")]

    def get_operation(self, path: UrlPath, method: HTTPMethod) -> APIOperation:
        operation: APIOperation = {
            "operationId": self.get_operation_id(path, method),
            "tags": self.get_tags(path),
            "description": self.get_description(),
            "parameters": self.get_parameters(path, method),
        }

        request_body = self.get_request_body(path, method)
        if request_body is not None:
            operation["requestBody"] = request_body

        callbacks = self.get_callbacks()
        if callbacks:
            operation["callbacks"] = callbacks

        operation["responses"] = self.get_responses(method)

        if method in self.deprecated:
            operation["deprecated"] = True

        security = self.security.get(method)
        if security is not None:
            operation["security"] = [security]

        external_docs = self.external_docs.get(method)
        if external_docs is not None:
            operation["externalDocs"] = external_docs

        return operation

    def get_component_name(self, serializer: SerializerOrSerializerType) -> ComponentName:
        if isinstance(serializer, ListSerializer):
            serializer = getattr(serializer, "child", serializer)

        if not is_serializer_class(serializer):
            serializer = serializer.__class__

        serializer_class_name = serializer.__name__
        component_name = serializer_pattern.sub("", serializer_class_name)

        if component_name == "":
            raise ValueError(  # pragma: no cover
                f"{serializer_class_name!r} is an invalid class name for schema generation. "
                f"Serializer's class name should be unique and explicit. e.g., 'ItemSerializer'"
            )

        return component_name

    def initialize_serializer(self, serializer_class: SerializerType) -> Serializer:
        return serializer_class(many=getattr(serializer_class, "many", False))

    def get_request_serializer_class(self) -> SerializerType:
        return self.view.get_serializer_class()

    def get_response_serializer_class(self) -> Optional[SerializerType]:
        with suppress(TypeError):
            return self.view.get_serializer_class(output=True)  # type: ignore

        return getattr(self.view, "output_serializer_class", None)  # pragma: no cover

    def get_components(self, *args, **kwargs) -> dict[ComponentName, APISchema]:
        components: dict[ComponentName, APISchema] = {}

        request_serializer_class = self.get_request_serializer_class()
        response_serializer_class = self.get_response_serializer_class()

        for serializer_class in (request_serializer_class, response_serializer_class):
            self.add_component(components, serializer_class)

        for method_responses in self.responses.values():
            for info in method_responses.values():
                if isinstance(info, list):
                    for item in info:
                        self.add_component(components, item)
                    continue

                self.add_component(components, info)

        return components

    def add_component(self, components: dict[ComponentName, APISchema], item: Optional[ResponseKind]) -> None:
        if not is_serializer_class(item):
            return

        serializer = self.initialize_serializer(item)
        content = map_serializer(serializer)
        component_name = self.get_component_name(serializer)
        components.setdefault(component_name, content)

    def get_callbacks(self) -> dict[EventName, dict[UrlPath, APIPathItem]]:
        if not self.callbacks:
            return {}

        callback_data = {}

        for event, callbacks in self.callbacks.items():
            callback_data.setdefault(event, {})
            for callback_url, methods in callbacks.items():
                callback_data[event].setdefault(callback_url, {})
                for method_name, data in methods.items():
                    callback_data[event][callback_url].setdefault(method_name.lower(), {})

                    request_body = data["request_body"]
                    if not is_serializer_class(request_body):
                        request_body = serializer_from_callable(request_body)

                    callback_data[event][callback_url][method_name.lower()]["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": map_serializer(request_body),
                            },
                        },
                    }

                    output_serializers = {}
                    for status_code, response in data["responses"].items():
                        if not is_serializer_class(response):
                            response = serializer_from_callable(response)

                        output_serializers[status_code] = {
                            "content": {
                                "application/json": {
                                    "schema": map_serializer(response),
                                },
                            },
                        }

                    callback_data[event][callback_url][method_name.lower()]["responses"] = output_serializers

        return callback_data

    def get_parameters(self, path: UrlPath, method: HTTPMethod) -> list[APIParameter]:
        serializer = self.view.get_serializer()
        if isinstance(serializer, ListSerializer):
            serializer = getattr(serializer, "child", serializer)

        parameters: list[APIParameter] = []
        path_parameters = list(get_path_parameters(path))
        query_parameters = self.query_parameters.get(method, [])
        header_parameters = self.header_parameters.get(method, [])
        cookie_parameters = self.cookie_parameters.get(method, [])

        if hasattr(serializer, "take_from_headers") and isinstance(serializer.take_from_headers, list):
            for header_name in serializer.take_from_headers:
                if header_name not in header_parameters:
                    header_parameters.append(header_name)

        if hasattr(serializer, "take_from_cookies") and isinstance(serializer.take_from_cookies, list):
            for cookie_name in serializer.take_from_cookies:
                if cookie_name not in cookie_parameters:
                    cookie_parameters.append(cookie_name)

        for field_name, field in serializer.fields.items():
            parameter = APIParameter(
                name=field_name,
                required=field.required,
                description=str(field.help_text) if field.help_text is not None else "",
                schema=map_field(field),
            )

            if field_name in path_parameters:
                parameter["in"] = "path"
                parameter["required"] = True
            elif field_name in query_parameters:
                parameter["in"] = "query"
            elif field_name in header_parameters:
                parameter["in"] = "header"
            elif field_name in cookie_parameters:
                parameter["in"] = "cookie"
            elif method == "GET":
                parameter["in"] = "query"
            else:
                continue

            parameters.append(parameter)

        return parameters

    def get_parsers(self) -> list[MediaType]:
        return [parser_class.media_type for parser_class in self.view.parser_classes]  # type: ignore

    def get_renderers(self) -> list[MediaType]:
        return [  # type: ignore
            renderer.media_type
            for renderer in self.view.renderer_classes
            if not issubclass(renderer, BrowsableAPIRenderer)
        ]

    def get_reference(self, serializer: Serializer) -> APISchema:
        if isinstance(serializer, MockSerializer):
            if serializer.fields:
                return map_serializer(serializer)
            return convert_to_schema(serializer._example)

        if isinstance(serializer, ListSerializer):
            serializer = getattr(serializer, "child", serializer)

        return APISchema(**{"$ref": f"#/components/schemas/{self.get_component_name(serializer)}"})

    def get_request_body(self, path: UrlPath, method: HTTPMethod) -> Optional[APIRequestBody]:
        if method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None

        input_serializer = self.view.get_serializer()

        params: set[str] = {param["name"] for param in self.get_parameters(path, method)}

        if params:
            is_list_serializer = isinstance(input_serializer, ListSerializer)
            child_serializer = getattr(input_serializer, "child", input_serializer)

            fields = {key: value for key, value in child_serializer.fields.items() if key not in params}
            new_serializer_class = type(child_serializer.__class__.__name__, (MockSerializer,), fields)
            if is_list_serializer:
                new_serializer_class.many = True  # pragma: no cover

            new_serializer_class.__doc__ = (
                input_serializer.__class__.__doc__ or child_serializer.__class__.__doc__ or ""
            )
            input_serializer = self.initialize_serializer(serializer_class=new_serializer_class)  # type: ignore

        item_schema = (
            self.get_no_result_schema()
            if isinstance(input_serializer, EmptySerializer)
            else {"schema": self.get_reference(input_serializer)}
        )

        if not item_schema["schema"].get("properties", True):
            return None  # pragma: no cover

        return APIRequestBody(
            content={content_type: item_schema for content_type in self.get_parsers()},
        )

    def get_responses(self, method: HTTPMethod) -> APIResponses:
        data = APIResponses()

        responses = self.responses.get(method, {})
        method_links = self.links.get(method, {})
        authentication_classes = self.view.authentication_classes
        permission_classes = self.view.permission_classes

        if ... not in list(responses.values()):
            responses.setdefault(200, ...)

        if authentication_classes:
            responses.setdefault(401, "Unauthenticated.")

        if permission_classes and permission_classes != [AllowAny]:
            responses.setdefault(403, "Permission Denied.")

        for status_code, info in responses.items():
            serializer_class: Optional[SerializerType] = None

            if info is ...:
                serializer_class = self.get_response_serializer_class()
                if serializer_class is None:
                    continue  # pragma: no cover
                info = serializer_class.__doc__ or ""

            elif is_serializer_class(info):
                serializer_class = info
                info = serializer_class.__doc__ or ""

            if serializer_class is not None:
                serializer = self.initialize_serializer(serializer_class=serializer_class)

                if status_code // 100 == 2 and isinstance(serializer, ListSerializer):
                    data.setdefault("204", self.get_no_result_schema())

                if isinstance(serializer, EmptySerializer):
                    status_code = 204
                    response_schema = self.get_no_result_schema()
                else:
                    response_schema = {"schema": self.get_reference(serializer)}

            elif isinstance(info, list):
                response_schema = {"schema": APISchema(anyOf=[])}

                for item in info:
                    if is_serializer_class(item):
                        serializer = self.initialize_serializer(serializer_class=item)
                        response_schema["schema"]["anyOf"].append(self.get_reference(serializer))
                        continue

                    response_schema["schema"]["anyOf"].append(self.get_error_message_schema())

                info = ""

            else:
                response_schema = {"schema": self.get_error_message_schema()}

            data[str(status_code)] = {
                "content": {content_type: response_schema for content_type in self.get_renderers()},
                "description": info,
            }

            links = method_links.get(status_code, None)
            if links is not None:
                data[str(status_code)]["links"] = links

        return data

    def get_no_result_schema(self, description: str = "no results") -> APIParameter:
        return APIParameter(
            content={"application/json": APISchema(type="string", default="")},
            description=description,
        )

    def get_error_message_schema(self, error_message: str = "error message") -> APISchema:
        return APISchema(
            type="object",
            properties={"detail": APISchema(type="string", default=error_message)},
        )

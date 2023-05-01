import copy
import re
import warnings
from decimal import Decimal
from functools import partial
from inspect import cleandoc

from django.contrib.admindocs.views import simplify_regex
from django.core import validators
from django.urls import URLPattern, URLResolver
from rest_framework import fields, serializers
from rest_framework.fields import _UnvalidatedField, empty
from rest_framework.request import Request, clone_request
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from .typing import (
    Any,
    APISchema,
    APIType,
    AsView,
    CompatibleView,
    ComponentName,
    Generator,
    HTTPMethod,
    Optional,
    PathAndMethod,
    SerializerOrSerializerType,
    TypeGuard,
    Union,
    UrlPath,
)

url_variables_pattern = re.compile("{([^}]+)}")
serializer_pattern = re.compile("serializer", flags=re.IGNORECASE)
path_parameter_pattern = re.compile(r"<[^>:]*:?(?P<parameter>\w+)>")
path_format_parameter = re.compile(r"^[^.]*[.]\{[^}]+}/?$")


def is_serializer_class(obj: Any) -> TypeGuard[Serializer]:
    return isinstance(obj, type) and issubclass(obj, Serializer)


def convert_to_schema(schema: Union[list[Any], dict[str, Any], Any]) -> APISchema:
    """Recursively convert a json-like object to OpenAPI example response."""
    if isinstance(schema, list):
        return APISchema(
            type="array",
            items=convert_to_schema(schema[0] if len(schema) > 0 else "???"),
        )

    if isinstance(schema, dict):
        return APISchema(
            type="object",
            properties={str(key): convert_to_schema(value) for key, value in schema.items()},
        )

    return APISchema(
        type="string",
        default=str(schema),
    )


def map_field(field: fields.Field) -> APISchema:  # pragma: no cover
    if isinstance(field, ListSerializer):
        return APISchema(type="array", items=map_serializer(field.child))

    if isinstance(field, Serializer):
        return map_serializer(field)

    if isinstance(field, fields.ChoiceField):
        choices = list(dict.fromkeys(field.choices))
        type_: Optional[APIType] = None

        if all(isinstance(choice, bool) for choice in choices):
            type_ = "boolean"
        elif all(isinstance(choice, int) for choice in choices):
            type_ = "integer"
        elif all(isinstance(choice, (int, float, Decimal)) for choice in choices):
            type_ = "number"
        elif all(isinstance(choice, str) for choice in choices):
            type_ = "string"

        mapping = APISchema(enum=choices)
        if type_ is not None:
            mapping["type"] = type_

        if isinstance(field, fields.MultipleChoiceField):
            return APISchema(type="array", items=mapping)
        return mapping

    if isinstance(field, fields.ListField):
        mapping = APISchema(type="array", items={})
        if not isinstance(field.child, _UnvalidatedField):
            mapping["items"] = map_field(field.child)
        return mapping

    if isinstance(field, fields.DateField):
        return APISchema(type="string", format="date")

    if isinstance(field, fields.DateTimeField):
        return APISchema(type="string", format="date-time")

    if isinstance(field, fields.EmailField):
        return APISchema(type="string", format="email")

    if isinstance(field, fields.URLField):
        return APISchema(type="string", format="uri")

    if isinstance(field, fields.UUIDField):
        return APISchema(type="string", format="uuid")

    if isinstance(field, fields.IPAddressField):
        content = APISchema(type="string")
        if field.protocol != "both":
            content["format"] = field.protocol  # type: ignore
        return content

    if isinstance(field, fields.DecimalField):
        if getattr(field, "coerce_to_string", api_settings.COERCE_DECIMAL_TO_STRING):
            content = APISchema(type="string", format="decimal")
        else:
            content = APISchema(type="number")

        if field.decimal_places:
            content["multipleOf"] = float("." + (field.decimal_places - 1) * "0" + "1")
        if field.max_whole_digits:
            content["maximum"] = int(field.max_whole_digits * "9") + 1
            content["minimum"] = -content["maximum"]
        if field.max_value:
            content["maximum"] = field.max_value
        if field.min_value:
            content["minimum"] = field.min_value

        return content

    if isinstance(field, fields.FloatField):
        content = APISchema(type="number")
        if field.max_value:
            content["maximum"] = field.max_value
        if field.min_value:
            content["minimum"] = field.min_value
        return content

    if isinstance(field, fields.IntegerField):
        content = APISchema(type="integer")
        if field.max_value:
            content["maximum"] = field.max_value
            if field.max_value > 2_147_483_647:
                content["format"] = "int64"
        if field.min_value:
            content["minimum"] = field.min_value
            if field.min_value > 2_147_483_647:
                content["format"] = "int64"
        return content

    if isinstance(field, fields.FileField):
        return APISchema(type="string", format="binary")

    if isinstance(field, fields.BooleanField):
        return APISchema(type="boolean")

    if isinstance(field, fields.JSONField):
        return APISchema(type="object")

    if isinstance(field, fields.DictField):
        return APISchema(type="object")

    if isinstance(field, fields.HStoreField):
        return APISchema(type="object")

    return APISchema(type="string")


def map_serializer(serializer: SerializerOrSerializerType) -> APISchema:
    required = []
    result = APISchema(type="object", properties={})

    if is_serializer_class(serializer):
        serializer = serializer(many=getattr(serializer, "many", False))

    if isinstance(serializer, ListSerializer):
        return APISchema(type="array", items=map_serializer(getattr(serializer, "child", serializer)))

    for field in serializer.fields.values():  # pragma: no cover
        if isinstance(field, fields.HiddenField):
            continue

        if field.required:
            required.append(field.field_name)

        schema = map_field(field)

        if field.read_only:
            schema["readOnly"] = True
        if field.write_only:
            schema["writeOnly"] = True
        if field.allow_null:
            schema["nullable"] = True
        if field.default is not None and field.default != empty and not callable(field.default):
            schema["default"] = field.default
        if field.help_text:
            schema["description"] = str(field.help_text)

        map_field_validators(field, schema)

        result["properties"][field.field_name] = schema

    if required:
        result["required"] = required

    return result


def map_field_validators(field: fields.Field, schema: APISchema) -> None:  # pragma: no cover
    for validator in field.validators:
        if isinstance(validator, validators.EmailValidator):
            schema["format"] = "email"

        if isinstance(validator, validators.URLValidator):
            schema["format"] = "uri"

        if isinstance(validator, validators.RegexValidator):
            schema["pattern"] = validator.regex.pattern.replace("\\Z", "\\z")

        elif isinstance(validator, validators.MaxLengthValidator):
            attr_name = "maxItems" if isinstance(field, fields.ListField) else "maxLength"
            schema[attr_name] = validator.limit_value

        elif isinstance(validator, validators.MinLengthValidator):
            attr_name = "minItems" if isinstance(field, fields.ListField) else "minLength"
            schema[attr_name] = validator.limit_value

        elif isinstance(validator, validators.MaxValueValidator):
            schema["maximum"] = validator.limit_value

        elif isinstance(validator, validators.MinValueValidator):
            schema["minimum"] = validator.limit_value

        elif isinstance(validator, validators.DecimalValidator) and not getattr(
            field, "coerce_to_string", api_settings.COERCE_DECIMAL_TO_STRING
        ):
            if validator.decimal_places:
                schema["multipleOf"] = float("." + (validator.decimal_places - 1) * "0" + "1")
            if validator.max_digits:
                digits = validator.max_digits
                if validator.decimal_places is not None and validator.decimal_places > 0:
                    digits -= validator.decimal_places
                schema["maximum"] = int(digits * "9") + 1
                schema["minimum"] = -schema["maximum"]


def get_api_endpoints(
    patterns: list[Union[URLPattern, URLResolver]],
    root: UrlPath,
    request: Optional[Request],
) -> list[tuple[UrlPath, HTTPMethod, CompatibleView]]:
    api_endpoints: list[tuple[UrlPath, HTTPMethod, CompatibleView]] = []

    for pattern in patterns:
        path = simplify_regex(str(pattern.pattern))
        if not path.endswith("/"):
            path += "/"
        if not path.startswith(root):
            path = root + path

        if isinstance(pattern, URLPattern):
            path = re.sub(path_parameter_pattern, r"{\g<parameter>}", path)
            callback: AsView = pattern.callback

            if should_include_endpoint(path, callback):
                for method in get_methods(callback):
                    view = create_view(callback, method, request)
                    api_endpoints.append((path, method, view))

        elif isinstance(pattern, URLResolver):  # pragma: no cover
            api_endpoints += get_api_endpoints(
                patterns=pattern.url_patterns,
                root=path.removesuffix("/"),
                request=request,
            )

    return sorted(api_endpoints, key=endpoint_ordering)


def should_include_endpoint(path: UrlPath, callback: AsView) -> bool:  # pragma: no cover
    if not hasattr(callback, "cls"):
        return False

    if not issubclass(callback.cls, APIView):
        return False

    if callback.cls.schema is None:
        return False

    if callback.initkwargs.get("schema", ...) is None:
        return False

    # Ignore urls ending with file types
    match = re.match(path_format_parameter, path)
    if match is not None:
        return False

    return True


def get_methods(callback: AsView) -> list[HTTPMethod]:
    if hasattr(callback.cls, "pipelines"):
        return list(callback.cls.pipelines)

    if hasattr(callback, "actions"):
        actions = set(callback.actions)
        http_method_names = set(callback.cls.http_method_names)
        methods = [method.upper() for method in actions & http_method_names]
    else:
        methods = callback.cls().allowed_methods

    return [method for method in methods if method not in ("OPTIONS", "HEAD")]  # type: ignore


def create_view(callback: AsView, method: HTTPMethod, request: Optional[Request]) -> CompatibleView:
    view = callback.cls(**callback.initkwargs)
    view.args = ()
    view.kwargs = {}
    view.format_kwarg = None
    view.request = clone_request(request, method) if request is not None else None
    return view


def endpoint_ordering(endpoint: tuple[UrlPath, HTTPMethod, CompatibleView]) -> tuple[UrlPath, int]:
    method_priority = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}.get(endpoint[1], 5)
    return endpoint[0], method_priority


def get_local_path(path: UrlPath, root_url: UrlPath) -> UrlPath:
    path = path.removeprefix("/")
    root_url = root_url.removeprefix("/")
    path = path.removeprefix(root_url)
    path = path.removeprefix("/")
    return path


def get_path_parameters(path: UrlPath) -> Generator[str, Any, None]:
    for match in url_variables_pattern.finditer(path):
        yield match.groups()[0]


def warn_component_override(name: ComponentName) -> None:
    warnings.warn(  # pragma: no cover
        f"Schema component {name!r} has been overriden with a different value.",
        stacklevel=2,
    )


def warn_method_override(
    path: UrlPath,
    method: HTTPMethod,
    operation_id: str,
    operation_ids: dict[str, PathAndMethod],
) -> None:
    warnings.warn(  # pragma: no cover
        cleandoc(
            f"""
            You have a duplicated operationId in your OpenAPI schema: {operation_id}
                Route: {operation_ids[operation_id]["path"]!r}, Method: {operation_ids[operation_id]["method"]!r}
                Route: {path!r}, Method: {method!r}
            An operationId has to be unique across your schema.
            Your schema may not work in other tools.
            """
        ),
        stacklevel=2,
    )


class EmptySerializer(serializers.Serializer):
    # Used for schema 204 responses
    pass


def deprecate(
    __view: Optional[type[CompatibleView]] = None,
    *,
    methods: Optional[list[HTTPMethod]] = None,
) -> type[CompatibleView]:
    """Deprecate a view in the OpenAPI schema while retaining the original.

    :param methods: HTTP methods to deprecate. Deprecate all if not given.
    """

    def view(_view: type[CompatibleView], _methods: Optional[list[HTTPMethod]] = None) -> type[CompatibleView]:
        # Mock the "get_serializer_class" method to change the calculated "operation_id"
        def new_get_serializer_class(old_method):
            def inner(self, output: bool = False):
                serializer = old_method.__get__(self, new_view)(output)
                new_serializer = type(f"Deprecated{serializer.__name__}", (serializer,), {})
                new_serializer.__doc__ = serializer.__doc__ or ""
                return new_serializer

            return inner

        new_view: type[CompatibleView] = type(f"Deprecated{_view.__name__}", (_view,), {})  # type: ignore
        new_view.__doc__ = _view.__doc__ or ""
        new_view.get_serializer_class = new_get_serializer_class(new_view.get_serializer_class)

        if _methods is None:
            _methods = list(get_methods(new_view.as_view()))

        new_view.schema = copy.deepcopy(new_view.schema)
        new_view.schema.deprecated = _methods
        return new_view  # type: ignore

    if callable(__view):
        return view(__view, methods)  # type: ignore

    return partial(view, _methods=methods)  # type: ignore

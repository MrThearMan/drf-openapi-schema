from __future__ import annotations

from types import ModuleType
from typing import (
    Annotated,
    Any,
    Callable,
    Generator,
    Literal,
    Optional,
    Protocol,
    Sequence,
    TypedDict,
    TypeVar,
    Union,
)

# New in version 3.10
try:
    from typing import TypeAlias, TypeGuard
except ImportError:
    from typing_extensions import TypeAlias, TypeGuard

# New in version 3.11
try:
    from typing import Required
except ImportError:
    from typing_extensions import Required

from django.http.response import HttpResponseBase
from rest_framework.authentication import BaseAuthentication
from rest_framework.parsers import BaseParser  # noqa: TC002
from rest_framework.permissions import BasePermission
from rest_framework.renderers import BaseRenderer  # noqa: TC002
from rest_framework.request import Request  # noqa: TC002
from rest_framework.response import Response  # noqa: TC002
from rest_framework.serializers import Serializer

__all__ = [
    "APIXML",
    "APICallback",
    "APIComponents",
    "APIContact",
    "APIDiscriminator",
    "APIEncoding",
    "APIExample",
    "APIExternalDocumentation",
    "APIHeader",
    "APIInfo",
    "APIKeySecurityScheme",
    "APIKeySecurityType",
    "APILicense",
    "APILinks",
    "APIMediaType",
    "APIOperation",
    "APIParameter",
    "APIPathItem",
    "APIPaths",
    "APIReference",
    "APIRequestBody",
    "APIResponse",
    "APIResponses",
    "APISchema",
    "APISecurityRequirement",
    "APISecurityScheme",
    "APIServer",
    "APIServerVariable",
    "APIStyle",
    "APITag",
    "APIType",
    "Annotated",
    "Any",
    "AsView",
    "AuthOrPerm",
    "AuthScheme",
    "Callable",
    "CompatibleSchema",
    "CompatibleView",
    "ComponentName",
    "CookieParameter",
    "ErrorText",
    "EventName",
    "Generator",
    "Generator",
    "GenericView",
    "HTTPMethod",
    "HTTPSecurityScheme",
    "HTTPSecurityType",
    "HeaderParameter",
    "Literal",
    "MediaType",
    "ModuleType",
    "MutualTLSSecurityScheme",
    "MutualTLSSecurityType",
    "OAuth2SecurityScheme",
    "OAuth2SecurityType",
    "OAuthFlowAuthorizationCode",
    "OAuthFlowClientCredentials",
    "OAuthFlowImplicit",
    "OAuthFlowPassword",
    "OAuthFlows",
    "OpenAPI",
    "OpenIDConnectSecurityScheme",
    "OpenIDConnectSecurityType",
    "OperationBaseName",
    "Optional",
    "PathAndMethod",
    "PathParameter",
    "Protocol",
    "QueryParameter",
    "Required",
    "ResponseKind",
    "SchemaCallbackData",
    "SchemaLinks",
    "SchemaWebhook",
    "SchemeName",
    "ScopeName",
    "SecurityRules",
    "SecuritySchemeType",
    "SerializerOrSerializerType",
    "SerializerType",
    "StatusCode",
    "TypeAlias",
    "TypeGuard",
    "TypeVar",
    "TypedDict",
    "Union",
    "UrlPath",
    "http_method",
]


SerializerType: TypeAlias = type[Serializer]
SerializerOrSerializerType = Union[Serializer, SerializerType]

HTTPMethod: TypeAlias = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
http_method: TypeAlias = Literal["get", "post", "put", "patch", "delete", "trace", "options"]  # noqa: PYI042
AuthOrPerm: TypeAlias = Union[type[BasePermission], type[BaseAuthentication]]
SecurityRules: TypeAlias = dict[Union[tuple[AuthOrPerm, ...], AuthOrPerm], dict[str, list[str]]]

UrlPath: TypeAlias = str
EventName: TypeAlias = str
TagName: TypeAlias = str
ComponentName: TypeAlias = str
SchemeName: TypeAlias = str
ScopeName: TypeAlias = str
ErrorText: TypeAlias = str
StatusCode: TypeAlias = int
PathParameter: TypeAlias = str
QueryParameter: TypeAlias = str
HeaderParameter: TypeAlias = str
CookieParameter: TypeAlias = str
OperationBaseName: TypeAlias = str
ResponseKind = Union[ErrorText, SerializerType]

_View = TypeVar("_View", bound=Callable[..., HttpResponseBase])


class CompatibleSchema(Protocol):
    def get_operation(self, path: UrlPath, method: HTTPMethod) -> Any:
        """Get operation"""

    def get_components(self, path: UrlPath, method: HTTPMethod) -> Any:
        """Get component"""


class CompatibleView(Protocol):
    http_method_names: list[http_method]
    allowed_methods: list[http_method]
    request: Optional[Request]

    renderer_classes: Sequence[type[BaseRenderer]]
    parser_classes: Sequence[type[BaseParser]]
    authentication_classes: Sequence[type[BaseAuthentication]]
    permission_classes: Sequence[type[BasePermission]]

    schema: CompatibleSchema

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init"""

    @classmethod
    def as_view(cls, **kwargs: Any) -> AsView:
        """As View"""

    def get_serializer(self, *args: Any, **kwargs: Any) -> Serializer:
        """Get serializer"""

    def get_serializer_class(self) -> SerializerType:
        """Get serializer class"""

    def check_permissions(self, request: Request) -> None:
        """Check permissions"""


class AsView(Protocol[_View]):
    cls: type[CompatibleView]
    view_class: type[CompatibleView]
    view_initkwargs: dict[str, Any]
    initkwargs: dict[str, Any]
    csrf_exempt: bool
    __call__: _View


class GenericView(Protocol):
    def __call__(self: CompatibleView, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Generic view"""


class SchemaWebhook(TypedDict):
    method: http_method
    request_data: SerializerType
    responses: dict[int, Union[str, SerializerType]]


class SchemaLinks(TypedDict):
    method: HTTPMethod
    request_data: SerializerType
    responses: dict[int, Union[str, SerializerType]]


class SchemaCallbackData(TypedDict):
    request_body: SerializerType
    responses: dict[int, SerializerType]


class PathAndMethod(TypedDict):
    path: str
    method: HTTPMethod


_APIRefNotRequired = TypedDict("_APIRefNotRequired", {"$ref": str}, total=False)
_APIRefRequired = TypedDict("_APIRefRequired", {"$ref": str})


class APIReference(_APIRefRequired, total=False):
    summary: str
    description: str


class OpenAPI(TypedDict, total=False):
    openapi: Required[Literal["3.0.2"]]
    info: Required[APIInfo]
    jsonSchemaDialect: str
    servers: list[APIServer]
    paths: APIPaths
    webhooks: dict[Annotated[str, "webhook_name"], Union[APIPathItem, APIReference]]
    components: APIComponents
    security: list[APISecurityRequirement]
    tags: list[APITag]
    externalDocs: APIExternalDocumentation


class APIInfo(TypedDict, total=False):
    title: Required[str]
    version: Required[str]
    description: str
    contact: APIContact
    license: APILicense
    termsOfService: str


class APIContact(TypedDict, total=False):
    name: str
    url: str
    email: str


class APILicense(TypedDict, total=False):
    name: Required[str]
    identifier: str
    url: str


class APIServer(TypedDict, total=False):
    url: Required[str]
    description: str
    variables: dict[Annotated[str, "variable_name"], APIServerVariable]


class APIServerVariable(TypedDict, total=False):
    enum: list[str]
    default: Required[str]
    description: str


class APIComponents(TypedDict, total=False):
    schemas: dict[Annotated[str, "component_name"], APISchema]
    responses: dict[Annotated[str, "response_name"], Union[APIResponse, APIReference]]
    parameters: dict[Annotated[str, "parameter_name"], Union[APIParameter, APIReference]]
    examples: dict[Annotated[str, "example_name"], Union[APIExample, APIReference]]
    requestBodies: dict[Annotated[str, "request_body_name"], Union[APIRequestBody, APIReference]]
    headers: dict[Annotated[str, "header_name"], Union[APIHeader, APIReference]]
    securitySchemes: dict[Annotated[str, "security_scheme_name"], Union[APISecurityScheme, APIReference]]
    links: dict[Annotated[str, "link_name"], Union[APILinks, APIReference]]
    callbacks: dict[Annotated[str, "callback_name"], Union[APICallback, APIReference]]
    pathItems: dict[Annotated[str, "path_item_name"], Union[APIPathItem, APIReference]]


class APIPathItem(_APIRefNotRequired, total=False):
    summary: str
    description: str
    get: APIOperation
    put: APIOperation
    post: APIOperation
    delete: APIOperation
    options: APIOperation
    head: APIOperation
    patch: APIOperation
    trace: APIOperation
    servers: list[APIServer]
    parameters: list[Union[APIParameter, APIReference]]


APIPaths = dict[Annotated[str, "/{path}"], APIPathItem]


class APIOperation(TypedDict, total=False):
    tags: list[str]
    summary: str
    description: str
    externalDocs: APIExternalDocumentation
    operationId: Annotated[str, "unique"]
    parameters: list[Union[APIParameter, APIReference]]
    requestBody: Union[APIRequestBody, APIReference]
    responses: APIResponses
    callbacks: dict[str, dict[str, Union[APIPathItem, APIReference]]]
    deprecated: bool
    security: list[dict[str, list[str]]]
    servers: list[APIServer]


class APIExternalDocumentation(TypedDict, total=False):
    url: Required[str]
    description: str


MediaType: TypeAlias = str
APIStyle = Literal["form", "simple", "matrix", "label", "spaceDelimited", "pipeDelimited", "deepObject"]
_APIParameter = TypedDict("_APIParameter", {"in": Literal["path", "query", "header", "cookie"]})


class APIParameter(_APIParameter, total=False):
    name: Required[str]
    description: str
    required: bool
    deprecated: bool
    allowEmptyValue: bool
    style: APIStyle
    explode: bool
    allowReserved: bool
    schema: APISchema
    example: Any
    examples: dict[Annotated[str, "example_name"], Union[APIExample, APIReference]]
    content: dict[MediaType, APIMediaType]


class APIRequestBody(TypedDict, total=False):
    content: Required[dict[MediaType, APIMediaType]]
    description: str
    required: bool


class APIMediaType(TypedDict, total=False):
    schema: APISchema
    example: Any
    examples: dict[Annotated[str, "example_name"], Union[APIExample, APIReference]]
    encoding: dict[Annotated[str, "property_name"], APIEncoding]


class APIEncoding(TypedDict, total=False):
    contentType: MediaType
    headers: dict[Annotated[str, "header_name"], Union[APIHeader, APIReference]]
    style: APIStyle
    explode: bool
    allowReserved: bool


class APIResponse(TypedDict, total=False):
    description: Required[str]
    headers: dict[Annotated[str, "header_name"], Union[APIHeader, APIReference]]
    content: dict[MediaType, Union[APIMediaType, APIReference]]
    links: dict[Annotated[str, "link_name"], Union[APILinks, APIReference]]


_APIResponses = TypedDict(
    "_APIResponses",
    {
        "1XX": Union[APIResponse, APIReference],
        "2XX": Union[APIResponse, APIReference],
        "3XX": Union[APIResponse, APIReference],
        "4XX": Union[APIResponse, APIReference],
        "5XX": Union[APIResponse, APIReference],
        "100": Union[APIResponse, APIReference],
        "101": Union[APIResponse, APIReference],
        "102": Union[APIResponse, APIReference],
        "103": Union[APIResponse, APIReference],
        "104": Union[APIResponse, APIReference],
        "105": Union[APIResponse, APIReference],
        "106": Union[APIResponse, APIReference],
        "107": Union[APIResponse, APIReference],
        "108": Union[APIResponse, APIReference],
        "109": Union[APIResponse, APIReference],
        "110": Union[APIResponse, APIReference],
        "111": Union[APIResponse, APIReference],
        "112": Union[APIResponse, APIReference],
        "113": Union[APIResponse, APIReference],
        "114": Union[APIResponse, APIReference],
        "115": Union[APIResponse, APIReference],
        "116": Union[APIResponse, APIReference],
        "117": Union[APIResponse, APIReference],
        "118": Union[APIResponse, APIReference],
        "119": Union[APIResponse, APIReference],
        "120": Union[APIResponse, APIReference],
        "121": Union[APIResponse, APIReference],
        "122": Union[APIResponse, APIReference],
        "123": Union[APIResponse, APIReference],
        "124": Union[APIResponse, APIReference],
        "125": Union[APIResponse, APIReference],
        "126": Union[APIResponse, APIReference],
        "127": Union[APIResponse, APIReference],
        "128": Union[APIResponse, APIReference],
        "129": Union[APIResponse, APIReference],
        "130": Union[APIResponse, APIReference],
        "131": Union[APIResponse, APIReference],
        "132": Union[APIResponse, APIReference],
        "133": Union[APIResponse, APIReference],
        "134": Union[APIResponse, APIReference],
        "135": Union[APIResponse, APIReference],
        "136": Union[APIResponse, APIReference],
        "137": Union[APIResponse, APIReference],
        "138": Union[APIResponse, APIReference],
        "139": Union[APIResponse, APIReference],
        "140": Union[APIResponse, APIReference],
        "141": Union[APIResponse, APIReference],
        "142": Union[APIResponse, APIReference],
        "143": Union[APIResponse, APIReference],
        "144": Union[APIResponse, APIReference],
        "145": Union[APIResponse, APIReference],
        "146": Union[APIResponse, APIReference],
        "147": Union[APIResponse, APIReference],
        "148": Union[APIResponse, APIReference],
        "149": Union[APIResponse, APIReference],
        "150": Union[APIResponse, APIReference],
        "151": Union[APIResponse, APIReference],
        "152": Union[APIResponse, APIReference],
        "153": Union[APIResponse, APIReference],
        "154": Union[APIResponse, APIReference],
        "155": Union[APIResponse, APIReference],
        "156": Union[APIResponse, APIReference],
        "157": Union[APIResponse, APIReference],
        "158": Union[APIResponse, APIReference],
        "159": Union[APIResponse, APIReference],
        "160": Union[APIResponse, APIReference],
        "161": Union[APIResponse, APIReference],
        "162": Union[APIResponse, APIReference],
        "163": Union[APIResponse, APIReference],
        "164": Union[APIResponse, APIReference],
        "165": Union[APIResponse, APIReference],
        "166": Union[APIResponse, APIReference],
        "167": Union[APIResponse, APIReference],
        "168": Union[APIResponse, APIReference],
        "169": Union[APIResponse, APIReference],
        "170": Union[APIResponse, APIReference],
        "171": Union[APIResponse, APIReference],
        "172": Union[APIResponse, APIReference],
        "173": Union[APIResponse, APIReference],
        "174": Union[APIResponse, APIReference],
        "175": Union[APIResponse, APIReference],
        "176": Union[APIResponse, APIReference],
        "177": Union[APIResponse, APIReference],
        "178": Union[APIResponse, APIReference],
        "179": Union[APIResponse, APIReference],
        "180": Union[APIResponse, APIReference],
        "181": Union[APIResponse, APIReference],
        "182": Union[APIResponse, APIReference],
        "183": Union[APIResponse, APIReference],
        "184": Union[APIResponse, APIReference],
        "185": Union[APIResponse, APIReference],
        "186": Union[APIResponse, APIReference],
        "187": Union[APIResponse, APIReference],
        "188": Union[APIResponse, APIReference],
        "189": Union[APIResponse, APIReference],
        "190": Union[APIResponse, APIReference],
        "191": Union[APIResponse, APIReference],
        "192": Union[APIResponse, APIReference],
        "193": Union[APIResponse, APIReference],
        "194": Union[APIResponse, APIReference],
        "195": Union[APIResponse, APIReference],
        "196": Union[APIResponse, APIReference],
        "197": Union[APIResponse, APIReference],
        "198": Union[APIResponse, APIReference],
        "199": Union[APIResponse, APIReference],
        "200": Union[APIResponse, APIReference],
        "201": Union[APIResponse, APIReference],
        "202": Union[APIResponse, APIReference],
        "203": Union[APIResponse, APIReference],
        "204": Union[APIResponse, APIReference],
        "205": Union[APIResponse, APIReference],
        "206": Union[APIResponse, APIReference],
        "207": Union[APIResponse, APIReference],
        "208": Union[APIResponse, APIReference],
        "209": Union[APIResponse, APIReference],
        "210": Union[APIResponse, APIReference],
        "211": Union[APIResponse, APIReference],
        "212": Union[APIResponse, APIReference],
        "213": Union[APIResponse, APIReference],
        "214": Union[APIResponse, APIReference],
        "215": Union[APIResponse, APIReference],
        "216": Union[APIResponse, APIReference],
        "217": Union[APIResponse, APIReference],
        "218": Union[APIResponse, APIReference],
        "219": Union[APIResponse, APIReference],
        "220": Union[APIResponse, APIReference],
        "221": Union[APIResponse, APIReference],
        "222": Union[APIResponse, APIReference],
        "223": Union[APIResponse, APIReference],
        "224": Union[APIResponse, APIReference],
        "225": Union[APIResponse, APIReference],
        "226": Union[APIResponse, APIReference],
        "227": Union[APIResponse, APIReference],
        "228": Union[APIResponse, APIReference],
        "229": Union[APIResponse, APIReference],
        "230": Union[APIResponse, APIReference],
        "231": Union[APIResponse, APIReference],
        "232": Union[APIResponse, APIReference],
        "233": Union[APIResponse, APIReference],
        "234": Union[APIResponse, APIReference],
        "235": Union[APIResponse, APIReference],
        "236": Union[APIResponse, APIReference],
        "237": Union[APIResponse, APIReference],
        "238": Union[APIResponse, APIReference],
        "239": Union[APIResponse, APIReference],
        "240": Union[APIResponse, APIReference],
        "241": Union[APIResponse, APIReference],
        "242": Union[APIResponse, APIReference],
        "243": Union[APIResponse, APIReference],
        "244": Union[APIResponse, APIReference],
        "245": Union[APIResponse, APIReference],
        "246": Union[APIResponse, APIReference],
        "247": Union[APIResponse, APIReference],
        "248": Union[APIResponse, APIReference],
        "249": Union[APIResponse, APIReference],
        "250": Union[APIResponse, APIReference],
        "251": Union[APIResponse, APIReference],
        "252": Union[APIResponse, APIReference],
        "253": Union[APIResponse, APIReference],
        "254": Union[APIResponse, APIReference],
        "255": Union[APIResponse, APIReference],
        "256": Union[APIResponse, APIReference],
        "257": Union[APIResponse, APIReference],
        "258": Union[APIResponse, APIReference],
        "259": Union[APIResponse, APIReference],
        "260": Union[APIResponse, APIReference],
        "261": Union[APIResponse, APIReference],
        "262": Union[APIResponse, APIReference],
        "263": Union[APIResponse, APIReference],
        "264": Union[APIResponse, APIReference],
        "265": Union[APIResponse, APIReference],
        "266": Union[APIResponse, APIReference],
        "267": Union[APIResponse, APIReference],
        "268": Union[APIResponse, APIReference],
        "269": Union[APIResponse, APIReference],
        "270": Union[APIResponse, APIReference],
        "271": Union[APIResponse, APIReference],
        "272": Union[APIResponse, APIReference],
        "273": Union[APIResponse, APIReference],
        "274": Union[APIResponse, APIReference],
        "275": Union[APIResponse, APIReference],
        "276": Union[APIResponse, APIReference],
        "277": Union[APIResponse, APIReference],
        "278": Union[APIResponse, APIReference],
        "279": Union[APIResponse, APIReference],
        "280": Union[APIResponse, APIReference],
        "281": Union[APIResponse, APIReference],
        "282": Union[APIResponse, APIReference],
        "283": Union[APIResponse, APIReference],
        "284": Union[APIResponse, APIReference],
        "285": Union[APIResponse, APIReference],
        "286": Union[APIResponse, APIReference],
        "287": Union[APIResponse, APIReference],
        "288": Union[APIResponse, APIReference],
        "289": Union[APIResponse, APIReference],
        "290": Union[APIResponse, APIReference],
        "291": Union[APIResponse, APIReference],
        "292": Union[APIResponse, APIReference],
        "293": Union[APIResponse, APIReference],
        "294": Union[APIResponse, APIReference],
        "295": Union[APIResponse, APIReference],
        "296": Union[APIResponse, APIReference],
        "297": Union[APIResponse, APIReference],
        "298": Union[APIResponse, APIReference],
        "299": Union[APIResponse, APIReference],
        "300": Union[APIResponse, APIReference],
        "301": Union[APIResponse, APIReference],
        "302": Union[APIResponse, APIReference],
        "303": Union[APIResponse, APIReference],
        "304": Union[APIResponse, APIReference],
        "305": Union[APIResponse, APIReference],
        "306": Union[APIResponse, APIReference],
        "307": Union[APIResponse, APIReference],
        "308": Union[APIResponse, APIReference],
        "309": Union[APIResponse, APIReference],
        "310": Union[APIResponse, APIReference],
        "311": Union[APIResponse, APIReference],
        "312": Union[APIResponse, APIReference],
        "313": Union[APIResponse, APIReference],
        "314": Union[APIResponse, APIReference],
        "315": Union[APIResponse, APIReference],
        "316": Union[APIResponse, APIReference],
        "317": Union[APIResponse, APIReference],
        "318": Union[APIResponse, APIReference],
        "319": Union[APIResponse, APIReference],
        "320": Union[APIResponse, APIReference],
        "321": Union[APIResponse, APIReference],
        "322": Union[APIResponse, APIReference],
        "323": Union[APIResponse, APIReference],
        "324": Union[APIResponse, APIReference],
        "325": Union[APIResponse, APIReference],
        "326": Union[APIResponse, APIReference],
        "327": Union[APIResponse, APIReference],
        "328": Union[APIResponse, APIReference],
        "329": Union[APIResponse, APIReference],
        "330": Union[APIResponse, APIReference],
        "331": Union[APIResponse, APIReference],
        "332": Union[APIResponse, APIReference],
        "333": Union[APIResponse, APIReference],
        "334": Union[APIResponse, APIReference],
        "335": Union[APIResponse, APIReference],
        "336": Union[APIResponse, APIReference],
        "337": Union[APIResponse, APIReference],
        "338": Union[APIResponse, APIReference],
        "339": Union[APIResponse, APIReference],
        "340": Union[APIResponse, APIReference],
        "341": Union[APIResponse, APIReference],
        "342": Union[APIResponse, APIReference],
        "343": Union[APIResponse, APIReference],
        "344": Union[APIResponse, APIReference],
        "345": Union[APIResponse, APIReference],
        "346": Union[APIResponse, APIReference],
        "347": Union[APIResponse, APIReference],
        "348": Union[APIResponse, APIReference],
        "349": Union[APIResponse, APIReference],
        "350": Union[APIResponse, APIReference],
        "351": Union[APIResponse, APIReference],
        "352": Union[APIResponse, APIReference],
        "353": Union[APIResponse, APIReference],
        "354": Union[APIResponse, APIReference],
        "355": Union[APIResponse, APIReference],
        "356": Union[APIResponse, APIReference],
        "357": Union[APIResponse, APIReference],
        "358": Union[APIResponse, APIReference],
        "359": Union[APIResponse, APIReference],
        "360": Union[APIResponse, APIReference],
        "361": Union[APIResponse, APIReference],
        "362": Union[APIResponse, APIReference],
        "363": Union[APIResponse, APIReference],
        "364": Union[APIResponse, APIReference],
        "365": Union[APIResponse, APIReference],
        "366": Union[APIResponse, APIReference],
        "367": Union[APIResponse, APIReference],
        "368": Union[APIResponse, APIReference],
        "369": Union[APIResponse, APIReference],
        "370": Union[APIResponse, APIReference],
        "371": Union[APIResponse, APIReference],
        "372": Union[APIResponse, APIReference],
        "373": Union[APIResponse, APIReference],
        "374": Union[APIResponse, APIReference],
        "375": Union[APIResponse, APIReference],
        "376": Union[APIResponse, APIReference],
        "377": Union[APIResponse, APIReference],
        "378": Union[APIResponse, APIReference],
        "379": Union[APIResponse, APIReference],
        "380": Union[APIResponse, APIReference],
        "381": Union[APIResponse, APIReference],
        "382": Union[APIResponse, APIReference],
        "383": Union[APIResponse, APIReference],
        "384": Union[APIResponse, APIReference],
        "385": Union[APIResponse, APIReference],
        "386": Union[APIResponse, APIReference],
        "387": Union[APIResponse, APIReference],
        "388": Union[APIResponse, APIReference],
        "389": Union[APIResponse, APIReference],
        "390": Union[APIResponse, APIReference],
        "391": Union[APIResponse, APIReference],
        "392": Union[APIResponse, APIReference],
        "393": Union[APIResponse, APIReference],
        "394": Union[APIResponse, APIReference],
        "395": Union[APIResponse, APIReference],
        "396": Union[APIResponse, APIReference],
        "397": Union[APIResponse, APIReference],
        "398": Union[APIResponse, APIReference],
        "399": Union[APIResponse, APIReference],
        "400": Union[APIResponse, APIReference],
        "401": Union[APIResponse, APIReference],
        "402": Union[APIResponse, APIReference],
        "403": Union[APIResponse, APIReference],
        "404": Union[APIResponse, APIReference],
        "405": Union[APIResponse, APIReference],
        "406": Union[APIResponse, APIReference],
        "407": Union[APIResponse, APIReference],
        "408": Union[APIResponse, APIReference],
        "409": Union[APIResponse, APIReference],
        "410": Union[APIResponse, APIReference],
        "411": Union[APIResponse, APIReference],
        "412": Union[APIResponse, APIReference],
        "413": Union[APIResponse, APIReference],
        "414": Union[APIResponse, APIReference],
        "415": Union[APIResponse, APIReference],
        "416": Union[APIResponse, APIReference],
        "417": Union[APIResponse, APIReference],
        "418": Union[APIResponse, APIReference],
        "419": Union[APIResponse, APIReference],
        "420": Union[APIResponse, APIReference],
        "421": Union[APIResponse, APIReference],
        "422": Union[APIResponse, APIReference],
        "423": Union[APIResponse, APIReference],
        "424": Union[APIResponse, APIReference],
        "425": Union[APIResponse, APIReference],
        "426": Union[APIResponse, APIReference],
        "427": Union[APIResponse, APIReference],
        "428": Union[APIResponse, APIReference],
        "429": Union[APIResponse, APIReference],
        "430": Union[APIResponse, APIReference],
        "431": Union[APIResponse, APIReference],
        "432": Union[APIResponse, APIReference],
        "433": Union[APIResponse, APIReference],
        "434": Union[APIResponse, APIReference],
        "435": Union[APIResponse, APIReference],
        "436": Union[APIResponse, APIReference],
        "437": Union[APIResponse, APIReference],
        "438": Union[APIResponse, APIReference],
        "439": Union[APIResponse, APIReference],
        "440": Union[APIResponse, APIReference],
        "441": Union[APIResponse, APIReference],
        "442": Union[APIResponse, APIReference],
        "443": Union[APIResponse, APIReference],
        "444": Union[APIResponse, APIReference],
        "445": Union[APIResponse, APIReference],
        "446": Union[APIResponse, APIReference],
        "447": Union[APIResponse, APIReference],
        "448": Union[APIResponse, APIReference],
        "449": Union[APIResponse, APIReference],
        "450": Union[APIResponse, APIReference],
        "451": Union[APIResponse, APIReference],
        "452": Union[APIResponse, APIReference],
        "453": Union[APIResponse, APIReference],
        "454": Union[APIResponse, APIReference],
        "455": Union[APIResponse, APIReference],
        "456": Union[APIResponse, APIReference],
        "457": Union[APIResponse, APIReference],
        "458": Union[APIResponse, APIReference],
        "459": Union[APIResponse, APIReference],
        "460": Union[APIResponse, APIReference],
        "461": Union[APIResponse, APIReference],
        "462": Union[APIResponse, APIReference],
        "463": Union[APIResponse, APIReference],
        "464": Union[APIResponse, APIReference],
        "465": Union[APIResponse, APIReference],
        "466": Union[APIResponse, APIReference],
        "467": Union[APIResponse, APIReference],
        "468": Union[APIResponse, APIReference],
        "469": Union[APIResponse, APIReference],
        "470": Union[APIResponse, APIReference],
        "471": Union[APIResponse, APIReference],
        "472": Union[APIResponse, APIReference],
        "473": Union[APIResponse, APIReference],
        "474": Union[APIResponse, APIReference],
        "475": Union[APIResponse, APIReference],
        "476": Union[APIResponse, APIReference],
        "477": Union[APIResponse, APIReference],
        "478": Union[APIResponse, APIReference],
        "479": Union[APIResponse, APIReference],
        "480": Union[APIResponse, APIReference],
        "481": Union[APIResponse, APIReference],
        "482": Union[APIResponse, APIReference],
        "483": Union[APIResponse, APIReference],
        "484": Union[APIResponse, APIReference],
        "485": Union[APIResponse, APIReference],
        "486": Union[APIResponse, APIReference],
        "487": Union[APIResponse, APIReference],
        "488": Union[APIResponse, APIReference],
        "489": Union[APIResponse, APIReference],
        "490": Union[APIResponse, APIReference],
        "491": Union[APIResponse, APIReference],
        "492": Union[APIResponse, APIReference],
        "493": Union[APIResponse, APIReference],
        "494": Union[APIResponse, APIReference],
        "495": Union[APIResponse, APIReference],
        "496": Union[APIResponse, APIReference],
        "497": Union[APIResponse, APIReference],
        "498": Union[APIResponse, APIReference],
        "499": Union[APIResponse, APIReference],
        "500": Union[APIResponse, APIReference],
        "501": Union[APIResponse, APIReference],
        "502": Union[APIResponse, APIReference],
        "503": Union[APIResponse, APIReference],
        "504": Union[APIResponse, APIReference],
        "505": Union[APIResponse, APIReference],
        "506": Union[APIResponse, APIReference],
        "507": Union[APIResponse, APIReference],
        "508": Union[APIResponse, APIReference],
        "509": Union[APIResponse, APIReference],
        "510": Union[APIResponse, APIReference],
        "511": Union[APIResponse, APIReference],
        "512": Union[APIResponse, APIReference],
        "513": Union[APIResponse, APIReference],
        "514": Union[APIResponse, APIReference],
        "515": Union[APIResponse, APIReference],
        "516": Union[APIResponse, APIReference],
        "517": Union[APIResponse, APIReference],
        "518": Union[APIResponse, APIReference],
        "519": Union[APIResponse, APIReference],
        "520": Union[APIResponse, APIReference],
        "521": Union[APIResponse, APIReference],
        "522": Union[APIResponse, APIReference],
        "523": Union[APIResponse, APIReference],
        "524": Union[APIResponse, APIReference],
        "525": Union[APIResponse, APIReference],
        "526": Union[APIResponse, APIReference],
        "527": Union[APIResponse, APIReference],
        "528": Union[APIResponse, APIReference],
        "529": Union[APIResponse, APIReference],
        "530": Union[APIResponse, APIReference],
        "531": Union[APIResponse, APIReference],
        "532": Union[APIResponse, APIReference],
        "533": Union[APIResponse, APIReference],
        "534": Union[APIResponse, APIReference],
        "535": Union[APIResponse, APIReference],
        "536": Union[APIResponse, APIReference],
        "537": Union[APIResponse, APIReference],
        "538": Union[APIResponse, APIReference],
        "539": Union[APIResponse, APIReference],
        "540": Union[APIResponse, APIReference],
        "541": Union[APIResponse, APIReference],
        "542": Union[APIResponse, APIReference],
        "543": Union[APIResponse, APIReference],
        "544": Union[APIResponse, APIReference],
        "545": Union[APIResponse, APIReference],
        "546": Union[APIResponse, APIReference],
        "547": Union[APIResponse, APIReference],
        "548": Union[APIResponse, APIReference],
        "549": Union[APIResponse, APIReference],
        "550": Union[APIResponse, APIReference],
        "551": Union[APIResponse, APIReference],
        "552": Union[APIResponse, APIReference],
        "553": Union[APIResponse, APIReference],
        "554": Union[APIResponse, APIReference],
        "555": Union[APIResponse, APIReference],
        "556": Union[APIResponse, APIReference],
        "557": Union[APIResponse, APIReference],
        "558": Union[APIResponse, APIReference],
        "559": Union[APIResponse, APIReference],
        "560": Union[APIResponse, APIReference],
        "561": Union[APIResponse, APIReference],
        "562": Union[APIResponse, APIReference],
        "563": Union[APIResponse, APIReference],
        "564": Union[APIResponse, APIReference],
        "565": Union[APIResponse, APIReference],
        "566": Union[APIResponse, APIReference],
        "567": Union[APIResponse, APIReference],
        "568": Union[APIResponse, APIReference],
        "569": Union[APIResponse, APIReference],
        "570": Union[APIResponse, APIReference],
        "571": Union[APIResponse, APIReference],
        "572": Union[APIResponse, APIReference],
        "573": Union[APIResponse, APIReference],
        "574": Union[APIResponse, APIReference],
        "575": Union[APIResponse, APIReference],
        "576": Union[APIResponse, APIReference],
        "577": Union[APIResponse, APIReference],
        "578": Union[APIResponse, APIReference],
        "579": Union[APIResponse, APIReference],
        "580": Union[APIResponse, APIReference],
        "581": Union[APIResponse, APIReference],
        "582": Union[APIResponse, APIReference],
        "583": Union[APIResponse, APIReference],
        "584": Union[APIResponse, APIReference],
        "585": Union[APIResponse, APIReference],
        "586": Union[APIResponse, APIReference],
        "587": Union[APIResponse, APIReference],
        "588": Union[APIResponse, APIReference],
        "589": Union[APIResponse, APIReference],
        "590": Union[APIResponse, APIReference],
        "591": Union[APIResponse, APIReference],
        "592": Union[APIResponse, APIReference],
        "593": Union[APIResponse, APIReference],
        "594": Union[APIResponse, APIReference],
        "595": Union[APIResponse, APIReference],
        "596": Union[APIResponse, APIReference],
        "597": Union[APIResponse, APIReference],
        "598": Union[APIResponse, APIReference],
        "599": Union[APIResponse, APIReference],
    },
    total=False,
)


class APIResponses(_APIResponses, total=False):
    default: Union[APIResponse, APIReference]


APICallback = dict[Annotated[str, "callback_url"], Union[APIPathItem, APIReference]]


class APIExample(TypedDict, total=False):
    summary: str
    description: str
    value: Any
    externalValue: Annotated[str, "uri"]


class APILinks(TypedDict, total=False):
    operationRef: Annotated[str, "ref"]
    operationId: Annotated[str, "unique"]
    parameters: dict[str, Any]
    requestBody: Any
    description: str
    server: APIServer


class APIHeader(TypedDict, total=False):
    description: str
    required: bool
    deprecated: bool
    allowEmptyValue: bool
    style: APIStyle
    explode: bool
    allowReserved: bool
    schema: APISchema
    example: Any
    examples: dict[Annotated[str, "example_name"], Union[APIExample, APIReference]]
    content: dict[MediaType, APIMediaType]


class APITag(TypedDict, total=False):
    name: Required[str]
    description: str
    externalDocs: APIExternalDocumentation


APIKeySecurityType = Literal["apiKey"]
HTTPSecurityType = Literal["http"]
MutualTLSSecurityType = Literal["mutualTLS"]
OAuth2SecurityType = Literal["oauth2"]
OpenIDConnectSecurityType = Literal["openIdConnect"]
SecuritySchemeType = Union[
    APIKeySecurityType,
    HTTPSecurityType,
    MutualTLSSecurityType,
    OAuth2SecurityType,
    OpenIDConnectSecurityType,
]
_APIKeySecurityScheme = TypedDict("_APIKeySecurityScheme", {"in": Literal["query", "header", "cookie"]})


class APIKeySecurityScheme(_APIKeySecurityScheme, total=False):
    type: Required[APIKeySecurityType]
    description: str
    name: Required[str]


AuthScheme = Literal[
    "basic",
    "bearer",
    "digest",
    "oauth",
    "mutual",
    "negotiate",
    "hoba",
    "scram-sha-1",
    "scram-sha-256",
    "vapid",
]


class HTTPSecurityScheme(TypedDict, total=False):
    type: Required[HTTPSecurityType]
    description: str
    scheme: Required[AuthScheme]
    bearerFormat: Annotated[str, "scheme=bearer"]


class MutualTLSSecurityScheme(TypedDict, total=False):
    type: Required[MutualTLSSecurityType]
    description: str


class OAuth2SecurityScheme(TypedDict, total=False):
    type: Required[OAuth2SecurityType]
    description: str
    flows: Required[OAuthFlows]


class OAuthFlows(TypedDict, total=False):
    implicit: OAuthFlowImplicit
    password: OAuthFlowPassword
    clientCredentials: OAuthFlowClientCredentials
    authorizationCode: OAuthFlowAuthorizationCode


class OAuthFlowImplicit(TypedDict, total=False):
    authorizationUrl: Required[str]
    refreshUrl: str
    scopes: Required[dict[Annotated[str, "scope_name"], Annotated[str, "short_description"]]]


class OAuthFlowPassword(TypedDict, total=False):
    tokenUrl: Required[str]
    refreshUrl: str
    scopes: Required[dict[Annotated[str, "scope_name"], Annotated[str, "short_description"]]]


class OAuthFlowClientCredentials(TypedDict, total=False):
    tokenUrl: Required[str]
    refreshUrl: str
    scopes: Required[dict[Annotated[str, "scope_name"], Annotated[str, "short_description"]]]


class OAuthFlowAuthorizationCode(TypedDict, total=False):
    authorizationUrl: Required[str]
    tokenUrl: Required[str]
    refreshUrl: str
    scopes: Required[dict[Annotated[str, "scope_name"], Annotated[str, "short_description"]]]


class OpenIDConnectSecurityScheme(TypedDict, total=False):
    type: Required[OpenIDConnectSecurityType]
    description: str
    openIdConnectUrl: Required[Annotated[str, "url"]]


APISecurityScheme = Union[
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    MutualTLSSecurityScheme,
    OAuth2SecurityScheme,
    OpenIDConnectSecurityScheme,
]
APISecurityRequirement = dict[SecuritySchemeType, list[Annotated[str, "scope_name"]]]
APIType = Literal["string", "integer", "number", "boolean", "object", "array"]
FormatType = Literal["binary", "int64", "decimal", "date", "date-time", "email", "uri", "uuid", "ipv4", "ipv6"]


class APISchema(_APIRefNotRequired, total=False):
    type: APIType
    items: APISchema
    properties: dict[Annotated[str, "property_name"], APISchema]
    required: list[Annotated[str, "property_name"]]
    default: str
    description: str
    format: FormatType
    enum: list[str]
    readOnly: bool
    writeOnly: bool
    nullable: bool
    minimum: float
    maximum: float
    minItems: float
    maxItems: float
    multipleOf: float
    pattern: Annotated[str, "regex"]
    content: dict[MediaType, APIMediaType]
    contentMediaType: MediaType
    contentEncoding: Literal["base64", "base64url", "base32", "base32hex", "base16", "hex", "quoted-printable"]
    discriminator: APIDiscriminator
    xml: APIXML
    externalDocs: APIExternalDocumentation
    example: Any
    oneOf: list[APISchema]
    anyOf: list[APISchema]
    allOf: list[APISchema]


class APIDiscriminator(TypedDict, total=False):
    propertyName: Required[str]
    mapping: dict[Annotated[str, "name"], Annotated[str, "ref_or_link"]]


class APIXML(TypedDict, total=False):
    name: str
    namespace: str
    prefix: str
    attribute: bool
    wrapped: bool

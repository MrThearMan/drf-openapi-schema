from rest_framework import serializers

from .typing import Any, Union


class EmptySerializer(serializers.Serializer):
    # Used for schema 204 responses
    pass


class ExampleSerializer(serializers.Serializer):
    # Used to define custom responses

    _example: Union[list[Any], dict[str, Any], Any] = {}

    @classmethod
    def with_example(
        cls,
        description: str,
        response: Union[list[Any], dict[str, Any], Any],
    ) -> type["ExampleSerializer"]:
        new_cls = type(ExampleSerializer.__name__, (cls,), {"_example": response})  # type: ignore
        new_cls.__doc__ = description
        return new_cls  # type: ignore

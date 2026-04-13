type _Primitive = bool | float | int | str | None
type JSONLikeValue = _Primitive | list[JSONLikeValue] | dict[str, JSONLikeValue]

import uuid
from typing import Any

from calc_runs.models import ScaffoldProject


class InputValidationError(ValueError):
    def __init__(self, message: str, *, field: str | None = None):
        super().__init__(message)
        self.field = field


PROJECT_FIELDS = {
    "name",
    "region",
    "status",
    "code",
    "client",
    "location",
    "designer",
    "note",
}
SCHEME_FIELDS = {"name", "module", "params", "last_run_id"}
TEXT_LIMITS = {
    "name": 200,
    "code": 100,
    "client": 200,
    "location": 255,
    "designer": 100,
    "module": 100,
}


def _mapping(data: Any) -> dict:
    if not isinstance(data, dict):
        raise InputValidationError("JSON body must be an object")
    return data


def _reject_unknown(data: dict, allowed: set[str]) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise InputValidationError(f"unknown field(s): {', '.join(unknown)}")


def _text(data: dict, field: str, *, required: bool, allow_blank: bool) -> str:
    value = data[field]
    if not isinstance(value, str):
        raise InputValidationError(f"{field} must be a string", field=field)
    value = value.strip()
    if required and not value:
        raise InputValidationError(f"{field} is required", field=field)
    if not allow_blank and not value:
        raise InputValidationError(f"{field} may not be blank", field=field)
    limit = TEXT_LIMITS.get(field)
    if limit is not None and len(value) > limit:
        raise InputValidationError(
            f"{field} must be at most {limit} characters",
            field=field,
        )
    return value


def _choice(data: dict, field: str, choices: tuple[tuple[str, str], ...]) -> str:
    value = _text(data, field, required=True, allow_blank=False)
    allowed = {choice[0] for choice in choices}
    if value not in allowed:
        raise InputValidationError(
            f"{field} must be one of: {', '.join(sorted(allowed))}",
            field=field,
        )
    return value


def validate_project_payload(data: Any, *, partial: bool = False) -> dict:
    data = _mapping(data)
    _reject_unknown(data, PROJECT_FIELDS)
    if partial and not data:
        raise InputValidationError("at least one field is required")
    if not partial:
        optional_text_fields = PROJECT_FIELDS - {"name", "region", "status"}
        missing = optional_text_fields - set(data)
        if missing:
            data = {**{field: "" for field in missing}, **data}
        if "name" not in data:
            raise InputValidationError("name is required", field="name")
        if "region" not in data:
            raise InputValidationError("region is required", field="region")

    if "name" in data:
        cleaned = {"name": _text(data, "name", required=True, allow_blank=False)}
    elif partial:
        cleaned = {}
    else:
        raise InputValidationError("name is required", field="name")

    if "region" in data:
        cleaned["region"] = _choice(
            data,
            "region",
            ScaffoldProject.REGION_CHOICES,
        )
    if "status" in data:
        cleaned["status"] = _choice(
            data,
            "status",
            ScaffoldProject.STATUS_CHOICES,
        )
    elif not partial:
        cleaned["status"] = "preparing"

    for field in PROJECT_FIELDS - {"name", "region", "status"}:
        if field in data:
            cleaned[field] = _text(data, field, required=False, allow_blank=True)
    return cleaned


def validate_scheme_payload(data: Any, *, partial: bool = False) -> dict:
    data = _mapping(data)
    _reject_unknown(data, SCHEME_FIELDS)
    if partial and not data:
        raise InputValidationError("at least one field is required")

    if not partial:
        for field in ("name", "module"):
            if field not in data:
                raise InputValidationError(f"{field} is required")

    cleaned = {}
    if "name" in data:
        cleaned["name"] = _text(data, "name", required=True, allow_blank=False)
    if "module" in data:
        cleaned["module"] = _text(data, "module", required=True, allow_blank=False)
    if "params" in data:
        params = data["params"]
        if not isinstance(params, dict):
            raise InputValidationError("params must be a JSON object")
        cleaned["params"] = params
    if "last_run_id" in data:
        value = data["last_run_id"]
        if value is None:
            cleaned["last_run_id"] = None
        else:
            try:
                cleaned["last_run_id"] = str(uuid.UUID(str(value)))
            except (TypeError, ValueError, AttributeError) as exc:
                raise InputValidationError("last_run_id must be a valid UUID") from exc
    return cleaned

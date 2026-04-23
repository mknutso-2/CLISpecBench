from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class MarcError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _subfield_list() -> list["Subfield"]:
    return []


@dataclass(slots=True)
class ControlField:
    tag: str
    value: str

    def to_dict(self) -> dict[str, str]:
        return {"tag": self.tag, "value": self.value}


@dataclass(slots=True)
class Subfield:
    code: str
    value: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "value": self.value}


@dataclass(slots=True)
class DataField:
    tag: str
    indicators: tuple[str, str]
    subfields: list[Subfield] = field(default_factory=_subfield_list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "indicators": [self.indicators[0], self.indicators[1]],
            "subfields": [entry.to_dict() for entry in self.subfields],
        }


@dataclass(slots=True)
class Record:
    leader_template: str
    control_fields: list[ControlField]
    data_fields: list[DataField]

    def to_dict(self) -> dict[str, Any]:
        return {
            "leader_template": self.leader_template,
            "control_fields": [field.to_dict() for field in self.control_fields],
            "data_fields": [field.to_dict() for field in self.data_fields],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Record":
        try:
            leader_template = str(data["leader_template"])
            control_fields = [
                ControlField(tag=str(entry["tag"]), value=str(entry["value"]))
                for entry in data.get("control_fields", [])
            ]
            data_fields = [
                DataField(
                    tag=str(entry["tag"]),
                    indicators=(str(entry["indicators"][0]), str(entry["indicators"][1])),
                    subfields=[
                        Subfield(code=str(sub["code"]), value=str(sub["value"]))
                        for sub in entry.get("subfields", [])
                    ],
                )
                for entry in data.get("data_fields", [])
            ]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise MarcError("invalid_request", f"Invalid canonical MARC record: {exc}") from exc
        return cls(
            leader_template=leader_template,
            control_fields=control_fields,
            data_fields=data_fields,
        )

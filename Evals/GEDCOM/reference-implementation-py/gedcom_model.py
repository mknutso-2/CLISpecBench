from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast


class GedcomError(Exception):
    def __init__(self, code: str, message: str, *, line: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.line = line


def _node_list() -> list["GedcomNode"]:
    return []


def _as_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GedcomError("invalid_request", f"{label} must be an object")
    return cast(dict[str, Any], value)


def _as_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GedcomError("invalid_request", f"{label} must be a list")
    return cast(list[Any], value)


@dataclass(slots=True)
class GedcomNode:
    tag: str
    xref: str | None = None
    payload: str | None = None
    children: list["GedcomNode"] = field(default_factory=_node_list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "xref": self.xref,
            "payload": self.payload,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, label: str = "node") -> "GedcomNode":
        tag = data.get("tag")
        if not isinstance(tag, str) or not tag:
            raise GedcomError("invalid_request", f"{label}.tag must be a non-empty string")

        xref = data.get("xref")
        if xref is not None and not isinstance(xref, str):
            raise GedcomError("invalid_request", f"{label}.xref must be a string or null")

        payload = data.get("payload")
        if payload is not None and not isinstance(payload, str):
            raise GedcomError("invalid_request", f"{label}.payload must be a string or null")

        children = [
            cls.from_dict(_as_dict(entry, f"{label}.children[]"), label=f"{label}.children[]")
            for entry in _as_list(data.get("children", []), f"{label}.children")
        ]
        return cls(tag=tag, xref=xref, payload=payload, children=children)


@dataclass(slots=True)
class GedcomDataset:
    records: list[GedcomNode] = field(default_factory=_node_list)

    def to_dict(self) -> dict[str, Any]:
        return {"records": [record.to_dict() for record in self.records]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GedcomDataset":
        records = [
            GedcomNode.from_dict(_as_dict(entry, "dataset.records[]"), label="dataset.records[]")
            for entry in _as_list(data.get("records", []), "dataset.records")
        ]
        return cls(records=records)

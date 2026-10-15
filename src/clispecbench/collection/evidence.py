"""Local, immutable evidence transport independent of the conversational terminal.

These primitives are not review validators or a source of authorization. Callers
must hold their collection's existing dispatch lock and supply the actual strict
review validator. Never pass credentials into this store.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class Artifact:
    sha256: str
    size: int


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("invalid_sha256")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_json_key")
        value[key] = item
    return value


def _create_once(path: Path, data: bytes) -> None:
    """Publish a complete file atomically without replacing an existing name.

    A hard link to a flushed sibling is an atomic exclusive creation, unlike
    rename/replace (which can clobber evidence). Unsupported filesystems fail
    closed. Interrupted temporary files are inert, not journal records.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class EvidenceStore:
    """Content-addressed bytes, always hash-verified on retrieval."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _path(self, sha256: str) -> Path:
        value = _hash(sha256)
        path = self.root / "objects" / value[:2] / value
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("evidence_path_escape")
        return path

    def put(self, data: bytes) -> Artifact:
        artifact = Artifact(digest(data), len(data))
        path = self._path(artifact.sha256)
        try:
            _create_once(path, data)
        except FileExistsError:
            # Idempotent recovery is allowed only for byte-identical evidence.
            if self.get(artifact.sha256) != data:
                raise ValueError("existing_evidence_conflict") from None
        return artifact

    def get(self, sha256: str) -> bytes:
        data = self._path(sha256).read_bytes()
        if digest(data) != sha256:
            raise ValueError("evidence_hash_mismatch")
        return data

    def save_review(
        self,
        relative_path: str,
        raw: bytes,
        expected_sha256: str,
        validate: Callable[[bytes], None],
    ) -> Artifact:
        """Validate and save the exact already-assembled UTF-8 review bytes.

        No float normalization, restamping, signature creation, or stdout copy.
        The callback must reject incomplete/invalid signatures and evidence.
        """
        if digest(raw) != _hash(expected_sha256):
            raise ValueError("review_transport_hash_mismatch")
        raw.decode("utf-8", errors="strict")
        validate(raw)
        relative = Path(relative_path)
        destination = self.root / relative
        if relative.is_absolute() or not destination.resolve().is_relative_to(self.root):
            raise ValueError("review_path_escape")
        if destination == self.root or destination.resolve().is_relative_to(self.root / "objects"):
            raise ValueError("review_path_reserved")
        artifact = self.put(raw)
        try:
            _create_once(destination, raw)
        except FileExistsError:
            if destination.read_bytes() != raw:
                raise ValueError("existing_review_conflict") from None
        if destination.read_bytes() != raw:
            raise ValueError("saved_review_transport_mismatch")
        validate(destination.read_bytes())
        return artifact


@dataclass(frozen=True)
class Event:
    sequence: int
    previous: str | None
    kind: str
    artifact: Artifact
    sha256: str


EVENT_KINDS = frozenset(
    {"prepared", "reserved", "started", "completed", "reviewed", "omitted", "held", "paused"}
)


class Journal:
    """Append-only local event chain, with optimistic head and exclusive names.

    The caller must hold the SAME collection dispatch lock, including during
    load/append. A conflicting append fails; it never starts another attempt.
    The journal stores artifact references, not arbitrary exception prose.
    """

    def __init__(self, root: Path, store: EvidenceStore) -> None:
        self.root = root.resolve()
        self.store = store

    def load(self) -> tuple[Event, ...]:
        events: list[Event] = []
        if not self.root.exists():
            return ()
        for index, path in enumerate(sorted(self.root.glob("*.json")), start=1):
            if not path.resolve().is_relative_to(self.root):
                raise ValueError("journal_path_escape")
            if path.name != f"{index:08d}.json":
                raise ValueError("journal_sequence_gap")
            raw = path.read_bytes()
            parsed: object = json.loads(raw, object_pairs_hook=_unique_object)
            if not isinstance(parsed, dict):
                raise ValueError("journal_schema_invalid")
            value = cast(dict[str, object], parsed)
            if set(value) != {"sequence", "previous", "kind", "artifact_sha256", "artifact_size"}:
                raise ValueError("journal_schema_invalid")
            previous = events[-1].sha256 if events else None
            kind, sha256, size = value["kind"], value["artifact_sha256"], value["artifact_size"]
            if (
                type(value["sequence"]) is not int
                or value["sequence"] != index
                or value["previous"] != previous
                or not isinstance(kind, str)
                or kind not in EVENT_KINDS
                or not isinstance(sha256, str)
                or type(size) is not int
            ):
                raise ValueError("journal_chain_invalid")
            payload = self.store.get(sha256)
            if len(payload) != size:
                raise ValueError("journal_artifact_size_mismatch")
            events.append(Event(index, previous, kind, Artifact(sha256, size), digest(raw)))
        return tuple(events)

    def append(self, kind: str, artifact: Artifact, *, expected_head: str | None) -> Event:
        if kind not in EVENT_KINDS:
            raise ValueError("journal_kind_invalid")
        events = self.load()
        head = events[-1].sha256 if events else None
        if head != expected_head:
            raise ValueError("journal_head_changed")
        if type(artifact.size) is not int or len(self.store.get(artifact.sha256)) != artifact.size:
            raise ValueError("journal_artifact_size_mismatch")
        sequence = len(events) + 1
        raw = json.dumps(
            {
                "sequence": sequence,
                "previous": head,
                "kind": kind,
                "artifact_sha256": artifact.sha256,
                "artifact_size": artifact.size,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        _create_once(self.root / f"{sequence:08d}.json", raw)
        return Event(sequence, head, kind, artifact, digest(raw))

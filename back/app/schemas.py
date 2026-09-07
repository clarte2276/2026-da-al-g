from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RelationType = Literal[
    "REFERENCES",
    "PROCEDURE",
    "EXCEPTION",
    "VISUAL_HELP",
    "SUPERSEDES",
    "RELATED",
]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    mime_type: str | None
    sha256: str
    status: str
    created_at: datetime


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    version_number: int
    status: str
    parser_name: str | None
    fragment_count: int = 0
    error_message: str | None = None


class LocalRootOut(BaseModel):
    id: str
    label: str


class LocalFileOut(BaseModel):
    id: str
    root_id: str
    relative_path: str
    filename: str
    suffix: str
    size_bytes: int
    modified_at: datetime


class LocalOpenRequest(BaseModel):
    root_id: str
    relative_path: str


class LocalOpenOut(BaseModel):
    root_id: str
    relative_path: str
    document: DocumentOut
    version: VersionOut


class FragmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_id: str
    parent_id: str | None
    stable_key: str
    kind: str
    ordinal: int
    title: str | None
    text: str | None
    html: str | None
    table_json: list[Any] | dict[str, Any] | None
    locator_json: dict[str, Any]
    bbox_json: dict[str, Any] | None
    asset_url: str | None
    content_hash: str
    metadata_json: dict[str, Any]


class SelectionAnchor(BaseModel):
    fragment_id: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    selected_text: str = Field(default="", max_length=10000)
    locator_json: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_offsets(self) -> SelectionAnchor:
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be greater than or equal to start_offset")
        return self

    @property
    def is_range(self) -> bool:
        return self.end_offset > self.start_offset


class EdgeCreate(BaseModel):
    source_fragment_id: str
    target_fragment_id: str
    relation_type: RelationType = "RELATED"
    note: str | None = Field(default=None, max_length=5000)
    source: Literal["manual", "ai_suggestion"] = "manual"
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_by: str | None = None
    source_anchor: SelectionAnchor | None = None
    target_anchor: SelectionAnchor | None = None


class EdgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_fragment_id: str
    target_fragment_id: str
    relation_type: str
    status: str
    source: str
    note: str | None
    confidence: float | None
    source_anchor: SelectionAnchor | None
    target_anchor: SelectionAnchor | None
    created_by: str | None
    approved_by: str | None
    created_at: datetime
    approved_at: datetime | None


class EdgeBatchCreate(BaseModel):
    """Create the fragment-level edges produced by one many-to-many selection."""

    source_anchors: list[SelectionAnchor] = Field(min_length=1, max_length=200)
    target_anchors: list[SelectionAnchor] = Field(min_length=1, max_length=200)
    relation_type: RelationType = "RELATED"
    note: str | None = Field(default=None, max_length=5000)
    source: Literal["manual", "ai_suggestion"] = "manual"
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_by: str | None = None


class EdgeBatchOut(BaseModel):
    edges: list[EdgeOut]
    created_count: int
    skipped_count: int


class EdgeDecision(BaseModel):
    actor: str | None = None


class NeighborOut(BaseModel):
    fragment: FragmentOut
    edge: EdgeOut
    direction: Literal["outgoing", "incoming"]
    hop: int


class RAGQuery(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    top_k: int = Field(default=5, ge=1, le=30)
    max_hops: int = Field(default=2, ge=0, le=4)
    relation_types: list[RelationType] | None = None
    model: str | None = None


class EvidenceOut(BaseModel):
    fragment: FragmentOut | None
    text: str | None = None
    score: float
    hop: int
    path: list[str] = Field(default_factory=list)
    via_relation: str | None = None
    link_id: str | None = None
    selection: dict[str, Any] | None = None
    document_id: str | None = None
    filename: str | None = None


class RAGResponse(BaseModel):
    answer: str
    evidence: list[EvidenceOut]
    embedding_provider: str
    graph_expanded: bool


class TextRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    exact: str = Field(min_length=1)
    prefix: str = ""
    suffix: str = ""


class TextSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["text"]
    version_id: str
    ranges: list[TextRange] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def accept_single_range(cls, value: Any) -> Any:
        """Links saved before multi-range selections stored one range inline."""
        if isinstance(value, dict) and "ranges" not in value and "start" in value:
            rest = {k: v for k, v in value.items() if k not in {"kind", "version_id"}}
            return {"kind": value["kind"], "version_id": value["version_id"], "ranges": [rest]}
        return value


class PageSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["pages"]
    version_id: str
    pages: list[int] = Field(min_length=1)


class LinkWrite(BaseModel):
    source_selection: TextSelection | PageSelection = Field(discriminator="kind")
    target_selection: TextSelection | PageSelection = Field(discriminator="kind")
    relation_type: RelationType = "RELATED"
    note: str | None = Field(default=None, max_length=5000)

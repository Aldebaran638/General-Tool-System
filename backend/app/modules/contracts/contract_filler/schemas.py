"""
Contract Filler Module Schemas

Request/response schemas for the contract_filler tool module.
"""

from sqlmodel import SQLModel


class ContractField(SQLModel):
    """A single fillable field in the contract template."""

    key: str
    label: str
    type: str = "text"
    default_value: str | None = None
    required: bool = True


class ContractFieldsPublic(SQLModel):
    data: list[ContractField]


class PreviewSegment(SQLModel):
    """A segment of the contract preview (paragraph or table)."""

    type: str  # "paragraph" or "table"
    text: str | None = None
    style: str | None = None
    rows: list[list[str]] | None = None


class ContractPreviewPublic(SQLModel):
    data: list[PreviewSegment]


class FilledValuesPayload(SQLModel):
    field_values: dict[str, str]


class ExportRequest(SQLModel):
    filename: str | None = None


class ExportResponse(SQLModel):
    download_url: str
    filename: str

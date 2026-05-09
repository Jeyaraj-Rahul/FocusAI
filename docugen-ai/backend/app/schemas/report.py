from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class TextAlignment(str, Enum):
    left = "left"
    center = "center"
    right = "right"
    justify = "justify"


class PageMargins(BaseModel):
    top: float = Field(default=1.0, ge=0.25, le=2.5)
    right: float = Field(default=1.0, ge=0.25, le=2.5)
    bottom: float = Field(default=1.0, ge=0.25, le=2.5)
    left: float = Field(default=1.0, ge=0.25, le=2.5)


class FormattingOptions(BaseModel):
    font_family: str = Field(default="Times New Roman", min_length=1, max_length=80)
    body_font_size: int = Field(default=12, ge=8, le=18)
    heading_font_size: int = Field(default=16, ge=10, le=28)
    title_font_size: int = Field(default=22, ge=14, le=36)
    line_spacing: float = Field(default=1.5, ge=1.0, le=2.5)
    paragraph_alignment: TextAlignment = TextAlignment.justify
    margins: PageMargins = Field(default_factory=PageMargins)


class ReportImage(BaseModel):
    path: str = Field(..., min_length=1)
    caption: str = Field(default="", max_length=240)
    width_inches: float = Field(default=5.8, ge=1.0, le=7.0)
    alignment: TextAlignment = TextAlignment.center
    section_heading: str | None = Field(default=None, max_length=180)

    @field_validator("path")
    @classmethod
    def validate_supported_image(cls, value: str) -> str:
        suffix = Path(value).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
            raise ValueError("Image must be PNG, JPG, JPEG, BMP, or GIF")
        return value


class ReportSection(BaseModel):
    heading: str = Field(..., min_length=1, max_length=180)
    paragraphs: list[str] = Field(default_factory=list)
    images: list[ReportImage] = Field(default_factory=list)


class DocxReportRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=220)
    subtitle: str | None = Field(default=None, max_length=220)
    author_name: str | None = Field(default=None, max_length=120)
    institution: str | None = Field(default=None, max_length=180)
    include_table_of_contents: bool = True
    template_id: int | None = Field(default=None, ge=1)
    image_ids: list[int] = Field(default_factory=list)
    formatting: FormattingOptions = Field(default_factory=FormattingOptions)
    sections: list[ReportSection] = Field(default_factory=list, min_length=1)


class GeneratedDocumentResponse(BaseModel):
    filename: str
    path: str


class ImageAssetRead(BaseModel):
    id: int
    original_filename: str
    file_path: str
    caption: str
    section_heading: str | None
    alignment: TextAlignment
    width_px: int
    height_px: int
    original_width_px: int
    original_height_px: int

    model_config = {"from_attributes": True}

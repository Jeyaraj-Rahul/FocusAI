from pydantic import BaseModel, Field


class PolishNotesRequest(BaseModel):
    rough_notes: str = Field(..., min_length=5, max_length=12000)
    audience: str = Field(default="academic evaluator", max_length=120)
    tone: str = Field(default="formal academic", max_length=80)


class GrammarRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=12000)


class ChapterInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    content: str = Field(..., min_length=10, max_length=12000)


class ChapterSummariesRequest(BaseModel):
    chapters: list[ChapterInput] = Field(..., min_length=1, max_length=20)
    summary_words: int = Field(default=120, ge=40, le=250)


class AbstractRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=220)
    project_notes: str = Field(..., min_length=20, max_length=16000)
    word_count: int = Field(default=180, ge=80, le=350)


class AcknowledgementRequest(BaseModel):
    project_title: str = Field(..., min_length=3, max_length=220)
    author_name: str | None = Field(default=None, max_length=120)
    institution: str | None = Field(default=None, max_length=180)
    mentors: list[str] = Field(default_factory=list, max_length=10)
    tone: str = Field(default="sincere and formal", max_length=80)


class AITextResponse(BaseModel):
    text: str


class ChapterSummary(BaseModel):
    title: str
    summary: str


class ChapterSummariesResponse(BaseModel):
    summaries: list[ChapterSummary]

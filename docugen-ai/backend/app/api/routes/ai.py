from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai import (
    AITextResponse,
    AbstractRequest,
    AcknowledgementRequest,
    ChapterSummariesRequest,
    ChapterSummariesResponse,
    GrammarRequest,
    PolishNotesRequest,
)
from app.services.openai_service import openai_service

router = APIRouter()


@router.get("/status")
def ai_module_status(_: User = Depends(get_current_user)) -> dict[str, str]:
    return {"module": "ai", "status": "ready"}


@router.post("/polish-notes", response_model=AITextResponse)
def polish_notes(payload: PolishNotesRequest, _: User = Depends(get_current_user)) -> AITextResponse:
    text = openai_service.polish_notes(
        rough_notes=payload.rough_notes,
        audience=payload.audience,
        tone=payload.tone,
    )
    return AITextResponse(text=text)


@router.post("/improve-grammar", response_model=AITextResponse)
def improve_grammar(payload: GrammarRequest, _: User = Depends(get_current_user)) -> AITextResponse:
    return AITextResponse(text=openai_service.improve_grammar(payload.text))


@router.post("/chapter-summaries", response_model=ChapterSummariesResponse)
def generate_chapter_summaries(
    payload: ChapterSummariesRequest,
    _: User = Depends(get_current_user),
) -> ChapterSummariesResponse:
    summaries = openai_service.generate_chapter_summaries(
        chapters=payload.chapters,
        summary_words=payload.summary_words,
    )
    return ChapterSummariesResponse(summaries=summaries)


@router.post("/abstract", response_model=AITextResponse)
def generate_abstract(payload: AbstractRequest, _: User = Depends(get_current_user)) -> AITextResponse:
    text = openai_service.generate_abstract(
        title=payload.title,
        project_notes=payload.project_notes,
        word_count=payload.word_count,
    )
    return AITextResponse(text=text)


@router.post("/acknowledgements", response_model=AITextResponse)
def generate_acknowledgements(
    payload: AcknowledgementRequest,
    _: User = Depends(get_current_user),
) -> AITextResponse:
    text = openai_service.generate_acknowledgements(
        project_title=payload.project_title,
        author_name=payload.author_name,
        institution=payload.institution,
        mentors=payload.mentors,
        tone=payload.tone,
    )
    return AITextResponse(text=text)

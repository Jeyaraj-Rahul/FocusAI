from fastapi import HTTPException, status
from openai import OpenAI, OpenAIError

from app.core.config import settings
from app.schemas.ai import ChapterInput, ChapterSummary


ACADEMIC_WRITING_SYSTEM_PROMPT = """
You are DocuGen AI, an academic document writing assistant.
Your job is to improve clarity, structure, grammar, and professionalism.
Rules:
- Preserve all user-provided facts.
- Do not invent technologies, results, citations, dates, metrics, people, or institutions.
- Use concise academic language suitable for reports.
- Avoid marketing language and exaggerated claims.
- Return only the requested content, without prefacing phrases.
""".strip()


class OpenAIService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL

    def polish_notes(self, rough_notes: str, audience: str, tone: str) -> str:
        prompt = f"""
Convert the rough project notes into polished academic writing.

Audience: {audience}
Tone: {tone}

Rough notes:
{rough_notes}

Output requirements:
- Write in complete paragraphs.
- Keep the meaning and facts unchanged.
- Expand shorthand into professional language only when the meaning is clear.
""".strip()
        return self._complete(prompt, temperature=0.35)

    def improve_grammar(self, text: str) -> str:
        prompt = f"""
Improve grammar, punctuation, sentence flow, and readability.

Text:
{text}

Output requirements:
- Preserve meaning.
- Keep technical terms unchanged.
- Return the corrected text only.
""".strip()
        return self._complete(prompt, temperature=0.2)

    def generate_chapter_summaries(self, chapters: list[ChapterInput], summary_words: int) -> list[ChapterSummary]:
        summaries: list[ChapterSummary] = []
        for chapter in chapters:
            prompt = f"""
Generate a concise academic summary for this report chapter.

Chapter title: {chapter.title}
Target length: about {summary_words} words

Chapter content:
{chapter.content}

Output requirements:
- Summarize purpose, implementation, and key points.
- Do not add information that is not present in the chapter.
- Return one polished paragraph.
""".strip()
            summaries.append(ChapterSummary(title=chapter.title, summary=self._complete(prompt, temperature=0.3)))
        return summaries

    def generate_abstract(self, title: str, project_notes: str, word_count: int) -> str:
        prompt = f"""
Write an academic abstract for a project report.

Project title: {title}
Target length: about {word_count} words

Project notes:
{project_notes}

Output requirements:
- Include context, objective, approach, implementation scope, and outcome if provided.
- Do not invent performance results or conclusions.
- Write as a single abstract paragraph.
""".strip()
        return self._complete(prompt, temperature=0.3)

    def generate_acknowledgements(
        self,
        project_title: str,
        author_name: str | None,
        institution: str | None,
        mentors: list[str],
        tone: str,
    ) -> str:
        mentor_text = ", ".join(mentors) if mentors else "the project mentors and faculty members"
        prompt = f"""
Write an acknowledgement section for an academic project report.

Project title: {project_title}
Author name: {author_name or "not provided"}
Institution: {institution or "not provided"}
People to acknowledge: {mentor_text}
Tone: {tone}

Output requirements:
- Keep it sincere, formal, and concise.
- Do not invent names or designations.
- If author or institution is not provided, avoid mentioning it.
- Return 1-2 paragraphs only.
""".strip()
        return self._complete(prompt, temperature=0.4)

    def _complete(self, user_prompt: str, temperature: float) -> str:
        if self.client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key is not configured. Set OPENAI_API_KEY in the backend environment.",
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": ACADEMIC_WRITING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except OpenAIError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI request failed: {exc.__class__.__name__}",
            ) from exc

        content = response.choices[0].message.content
        if not content:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI returned an empty response")
        return content.strip()


openai_service = OpenAIService()

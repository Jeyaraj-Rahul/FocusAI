from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.template import TemplateProfile
from app.models.user import User
from app.schemas.template import TemplateProfileRead
from app.services.file_storage import save_upload
from app.services.template_analyzer import analyze_docx_template

router = APIRouter()


@router.get("", response_model=list[TemplateProfileRead])
def list_template_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TemplateProfile]:
    return (
        db.query(TemplateProfile)
        .filter(TemplateProfile.owner_id == current_user.id)
        .order_by(TemplateProfile.created_at.desc())
        .all()
    )


@router.post("/upload", response_model=TemplateProfileRead)
async def upload_docx_template(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TemplateProfile:
    saved_path = await save_upload(file, "templates", allowed_suffixes={".docx"})
    profile = analyze_docx_template(saved_path)
    template = TemplateProfile(
        name=(file.filename or "DOCX template").rsplit(".", 1)[0],
        original_filename=file.filename or "template.docx",
        file_path=str(saved_path),
        profile=profile,
        owner_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateProfileRead)
def get_template_profile(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TemplateProfile:
    template = (
        db.query(TemplateProfile)
        .filter(TemplateProfile.id == template_id, TemplateProfile.owner_id == current_user.id)
        .first()
    )
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template profile not found")
    return template

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.asset import ImageAsset
from app.models.template import TemplateProfile
from app.models.user import User
from app.schemas.report import DocxReportRequest, ImageAssetRead, ReportImage, TextAlignment
from app.services.document_generator import docx_report_generator
from app.services.image_handler import process_screenshot_upload
from app.services.pdf_exporter import pdf_export_service
from app.services.template_analyzer import formatting_options_from_profile

router = APIRouter()


@router.get("/status")
def reports_module_status(_: User = Depends(get_current_user)) -> dict[str, str]:
    return {"module": "reports", "status": "starter"}


@router.get("/images", response_model=list[ImageAssetRead])
def list_uploaded_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ImageAsset]:
    return (
        db.query(ImageAsset)
        .filter(ImageAsset.owner_id == current_user.id)
        .order_by(ImageAsset.created_at.desc())
        .all()
    )


@router.post("/images/upload", response_model=ImageAssetRead, status_code=status.HTTP_201_CREATED)
async def upload_screenshot(
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    section_heading: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageAsset:
    processed = await process_screenshot_upload(file)
    image = ImageAsset(
        owner_id=current_user.id,
        original_filename=file.filename or "screenshot",
        file_path=str(processed["path"]),
        caption=caption.strip(),
        section_heading=section_heading.strip() if section_heading else None,
        alignment=processed["alignment"],
        width_px=processed["width_px"],
        height_px=processed["height_px"],
        original_width_px=processed["original_width_px"],
        original_height_px=processed["original_height_px"],
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.post("/generate-docx")
def generate_docx_report(
    payload: DocxReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    _prepare_report_payload(payload, current_user, db)
    output_path = docx_report_generator.generate(payload)
    filename = Path(output_path).name
    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/generate-pdf")
def generate_pdf_report(
    payload: DocxReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    _prepare_report_payload(payload, current_user, db)
    docx_path = docx_report_generator.generate(payload)
    pdf_path, temp_dir = pdf_export_service.convert_docx_to_pdf(docx_path)
    background_tasks.add_task(pdf_export_service.cleanup, temp_dir)
    background_tasks.add_task(_delete_file, docx_path)
    return FileResponse(
        path=pdf_path,
        filename=f"{Path(docx_path).stem}.pdf",
        media_type="application/pdf",
        background=background_tasks,
    )


def _prepare_report_payload(payload: DocxReportRequest, current_user: User, db: Session) -> None:
    if payload.template_id:
        template = (
            db.query(TemplateProfile)
            .filter(TemplateProfile.id == payload.template_id, TemplateProfile.owner_id == current_user.id)
            .first()
        )
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template profile not found")
        payload.formatting = formatting_options_from_profile(template.profile)

    if payload.image_ids:
        images = (
            db.query(ImageAsset)
            .filter(ImageAsset.owner_id == current_user.id, ImageAsset.id.in_(payload.image_ids))
            .all()
        )
        if len(images) != len(set(payload.image_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more uploaded images were not found")
        _attach_images_to_sections(payload, images)


def _delete_file(path: str | Path) -> None:
    Path(path).unlink(missing_ok=True)


def _attach_images_to_sections(payload: DocxReportRequest, images: list[ImageAsset]) -> None:
    for image in images:
        target_section = _find_target_section(payload, image.section_heading)
        width_inches = _recommended_docx_width(image.width_px, image.height_px)
        target_section.images.append(
            ReportImage(
                path=image.file_path,
                caption=image.caption or image.original_filename,
                width_inches=width_inches,
                alignment=TextAlignment(image.alignment),
                section_heading=image.section_heading,
            )
        )


def _find_target_section(payload: DocxReportRequest, section_heading: str | None):
    if section_heading:
        normalized_hint = _normalize(section_heading)
        for section in payload.sections:
            normalized_heading = _normalize(section.heading)
            if normalized_hint == normalized_heading or normalized_hint in normalized_heading:
                return section
    return payload.sections[-1]


def _recommended_docx_width(width_px: int, height_px: int) -> float:
    if height_px > width_px:
        return 4.0
    if width_px / max(height_px, 1) > 1.8:
        return 6.2
    return 5.8


def _normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())

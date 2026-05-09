import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import HTTPException, status

from app.core.config import settings


class PDFExportService:
    def __init__(self, output_dir: str | Path | None = None) -> None:
        self.output_dir = Path(output_dir or settings.STORAGE_DIR) / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_docx_to_pdf(self, docx_path: str | Path) -> tuple[Path, Path]:
        source = Path(docx_path)
        if not source.exists() or source.suffix.lower() != ".docx":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid DOCX file is required for PDF export")

        temp_dir = Path(tempfile.mkdtemp(prefix="docugen-pdf-"))
        temp_docx = temp_dir / source.name
        shutil.copy2(source, temp_docx)
        temp_pdf = temp_dir / f"{source.stem}.pdf"

        try:
            self._convert_with_libreoffice(temp_docx, temp_dir)
            generated_pdf = temp_dir / f"{temp_docx.stem}.pdf"
            if generated_pdf.exists():
                return generated_pdf, temp_dir

            self._convert_with_docx2pdf(temp_docx, temp_pdf)
            if temp_pdf.exists():
                return temp_pdf, temp_dir

            self._convert_with_pypandoc(temp_docx, temp_pdf)
            if temp_pdf.exists():
                return temp_pdf, temp_dir
        except HTTPException:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PDF conversion failed") from exc

        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No DOCX to PDF converter is available. Install LibreOffice, Microsoft Word/docx2pdf, or Pandoc with a PDF engine.",
        )

    def cleanup(self, temp_dir: str | Path) -> None:
        shutil.rmtree(temp_dir, ignore_errors=True)

    def _convert_with_libreoffice(self, docx_path: Path, output_dir: Path) -> None:
        executable = shutil.which("libreoffice") or shutil.which("soffice")
        if not executable:
            return

        result = subprocess.run(
            [
                executable,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(docx_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LibreOffice failed to convert DOCX to PDF")

    def _convert_with_docx2pdf(self, docx_path: Path, pdf_path: Path) -> None:
        try:
            from docx2pdf import convert
        except ImportError:
            return

        convert(str(docx_path), str(pdf_path))

    def _convert_with_pypandoc(self, docx_path: Path, pdf_path: Path) -> None:
        try:
            import pypandoc
        except ImportError:
            return

        try:
            pypandoc.convert_file(str(docx_path), "pdf", outputfile=str(pdf_path))
        except OSError:
            return


pdf_export_service = PDFExportService()

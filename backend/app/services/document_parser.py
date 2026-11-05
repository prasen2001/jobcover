import os
from pathlib import Path


def parse_document(path: Path, requested_mode: str | None = None) -> tuple[str, str]:
    """Parse a resume with Docling. Plain text avoids loading document models."""
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace"), "standard"

    mode = (requested_mode or os.getenv("DOCLING_PIPELINE", "standard")).lower()
    if mode not in {"standard", "ocr", "vlm"}:
        raise ValueError("Parser mode must be standard, ocr, or vlm.")

    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, PdfFormatOption

    format_options = {}
    if path.suffix.lower() == ".pdf":
        if mode in {"standard", "ocr"}:
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                TesseractCliOcrOptions,
            )

            options = PdfPipelineOptions()
            options.do_ocr = mode == "ocr"
            if mode == "ocr":
                languages = [
                    value.strip()
                    for value in os.getenv("DOCLING_OCR_LANGUAGES", "en").split(",")
                    if value.strip()
                ]
                options.ocr_options = TesseractCliOcrOptions(lang=languages, force_full_page_ocr=True)
            format_options[InputFormat.PDF] = PdfFormatOption(pipeline_options=options)
        else:
            from docling.datamodel.pipeline_options import VlmPipelineOptions
            from docling.pipeline.vlm_pipeline import VlmPipeline

            # Docling's default VLM preset is IBM Granite Docling (non-Chinese).
            format_options[InputFormat.PDF] = PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=VlmPipelineOptions(),
            )

    converter = DocumentConverter(format_options=format_options)
    result = converter.convert(str(path))
    return result.document.export_to_markdown(), mode


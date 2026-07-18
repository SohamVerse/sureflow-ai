"""
Industrial Temporal Activities — SureFlow AI Phase 3.

Non-deterministic work (LLM calls, DB writes, file I/O) for the industrial
intelligence workflows. Temporal Workflow code itself must stay deterministic
since it gets replayed.

Activities:
  - ocr_extract_activity: Load/parse a document file → raw text
  - doc_intelligence_activity: Run Document Intelligence Agent
  - embed_and_store_activity: Embed chunks into pgvector
  - update_industrial_graph_activity: Run KG Agent → write to Neo4j
  - maintenance_analysis_activity: Run Maintenance Agent on equipment
  - lessons_learned_activity: Run Lessons Learned Agent
  - compliance_audit_activity: Run Compliance Agent
  - copilot_query_activity: Run Search Agent (Copilot)
"""
import json
import logging
from pathlib import Path
from temporalio import activity

from core.config import settings

from agents.document_intelligence import doc_intelligence_analyze
from agents.knowledge_graph_agent import kg_agent_process
from agents.search_agent import search_copilot_query
from agents.maintenance import maintenance_analyze
from agents.lessons_learned import lessons_learned_analyze
from agents.compliance import compliance_analyze
from rag.embeddings import ingest_document
from knowledge_graph.industrial_store import industrial_graph
from core.memory import MemoryStore

logger = logging.getLogger("companyos.industrial_activities")

# Below this average chars/page, a "text" PDF extraction is treated as a scan
# (image-only pages) and routed through the OCR fallback instead.
_SCANNED_PDF_CHAR_THRESHOLD = 50


def _configure_tesseract():
    """Import pytesseract and point it at a configured binary path, if set."""
    import pytesseract
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    return pytesseract


def _ocr_image_file(path: Path) -> str:
    """OCR a single image file (png/jpg/tiff/bmp) via Tesseract."""
    from PIL import Image
    pytesseract = _configure_tesseract()
    with Image.open(path) as img:
        return pytesseract.image_to_string(img)


def _ocr_scanned_pdf(file_path: str) -> tuple[str, int]:
    """Rasterize each PDF page and OCR it. Returns (text, page_count)."""
    from pdf2image import convert_from_path
    pytesseract = _configure_tesseract()
    convert_kwargs = {"poppler_path": settings.POPPLER_PATH} if settings.POPPLER_PATH else {}
    page_images = convert_from_path(file_path, **convert_kwargs)
    page_texts = [pytesseract.image_to_string(img) for img in page_images]
    return "\n\n".join(page_texts), len(page_images)


def _extract_docx_text(path: Path) -> str:
    """Extract paragraph text from a .docx file via python-docx."""
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text)


@activity.defn
async def ocr_extract_activity(file_path: str, file_name: str = "") -> dict:
    """
    Load a document file and extract raw text.

    For PDFs: uses PyPDFLoader; if the extracted text looks like an image-only
    scan (very low chars/page), falls back to rasterizing pages and running
    Tesseract OCR on each one.
    For text/markdown: reads directly.
    For images: Tesseract OCR via pytesseract.
    For DOCX: real paragraph extraction via python-docx.

    All OCR/DOCX paths degrade gracefully (with a logged warning) to the prior
    placeholder text if the optional dependency or system binary isn't
    installed, so ingestion never hard-fails on a missing local OCR setup.

    Returns dict with raw_text and metadata.
    """
    activity.logger.info(f"OCR/Extract: Processing {file_name or file_path}")

    path = Path(file_path)
    if not path.exists():
        return {"raw_text": "", "error": f"File not found: {file_path}", "pages": 0}

    raw_text = ""
    pages = 0

    try:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            raw_text = "\n\n".join(doc.page_content for doc in documents)
            pages = len(documents)

            avg_chars_per_page = len(raw_text) / pages if pages else 0
            if avg_chars_per_page < _SCANNED_PDF_CHAR_THRESHOLD:
                try:
                    activity.logger.info(
                        f"OCR/Extract: '{file_name or path.name}' looks scan-only "
                        f"({avg_chars_per_page:.0f} chars/page) — falling back to OCR"
                    )
                    ocr_text, ocr_pages = _ocr_scanned_pdf(file_path)
                    if len(ocr_text.strip()) > len(raw_text.strip()):
                        raw_text, pages = ocr_text, ocr_pages
                except Exception as e:
                    activity.logger.warning(
                        f"OCR/Extract: scanned-PDF OCR fallback unavailable ({e}). "
                        f"Install Tesseract-OCR + Poppler for scanned-PDF support. "
                        f"Keeping raw PyPDFLoader text."
                    )
        elif suffix in (".txt", ".md", ".csv", ".log"):
            raw_text = path.read_text(encoding="utf-8", errors="replace")
            pages = 1
        elif suffix in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
            try:
                raw_text = _ocr_image_file(path)
                pages = 1
            except Exception as e:
                activity.logger.warning(
                    f"OCR/Extract: Tesseract unavailable ({e}). Install Tesseract-OCR "
                    f"and/or set TESSERACT_CMD in .env. Returning placeholder text."
                )
                raw_text = f"[Image file: {file_name or path.name}. OCR extraction unavailable — Tesseract not installed/configured.]"
                pages = 1
        elif suffix in (".docx",):
            try:
                raw_text = _extract_docx_text(path)
                pages = 1
            except Exception as e:
                activity.logger.warning(
                    f"OCR/Extract: python-docx unavailable ({e}). Returning placeholder text."
                )
                raw_text = f"[DOCX file: {file_name or path.name}. DOCX parsing unavailable — python-docx not installed.]"
                pages = 1
        else:
            # Try as text
            raw_text = path.read_text(encoding="utf-8", errors="replace")
            pages = 1
    except Exception as e:
        activity.logger.error(f"OCR/Extract failed: {e}")
        return {"raw_text": "", "error": str(e), "pages": 0}

    activity.logger.info(f"OCR/Extract: Got {len(raw_text)} chars from {pages} page(s)")
    return {
        "raw_text": raw_text,
        "file_name": file_name or path.name,
        "file_path": file_path,
        "pages": pages,
        "char_count": len(raw_text),
    }


@activity.defn
async def doc_intelligence_activity(raw_text: str, file_name: str, run_id: str = "") -> dict:
    """
    Run the Document Intelligence Agent on extracted text.
    Returns structured entities, relationships, chunks, and metadata.
    """
    activity.logger.info(f"Doc Intelligence: Analyzing {file_name} ({len(raw_text)} chars)")
    result = doc_intelligence_analyze(raw_text, file_name=file_name, run_id=run_id or None)
    activity.logger.info(
        f"Doc Intelligence: Found {len(result.get('entities', []))} entities, "
        f"{len(result.get('chunks', []))} chunks, type={result.get('doc_type', '?')}"
    )
    return result


@activity.defn
async def embed_and_store_activity(raw_text: str, file_path: str, collection: str, file_name: str = "") -> dict:
    """
    Embed document text and store in pgvector.
    Uses the existing ingest_document pipeline from rag/embeddings.py.
    """
    activity.logger.info(f"Embed & Store: Ingesting into collection '{collection}'")

    # Write raw text to a temp file if the original is no longer available
    path = Path(file_path)
    if not path.exists():
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write(raw_text)
            file_path = tmp.name

    try:
        result = ingest_document(
            file_path,
            collection,
            metadata={"original_name": file_name, "source": "industrial_ingestion"},
        )
        activity.logger.info(f"Embed & Store: Ingested {result.get('chunks_ingested', 0)} chunks")
        return result
    except Exception as e:
        activity.logger.error(f"Embed & Store failed: {e}")
        return {"error": str(e), "chunks_ingested": 0}


@activity.defn
async def update_industrial_graph_activity(
    entities: list, relationships: list, doc_metadata: dict, run_id: str = ""
) -> dict:
    """
    Run the Knowledge Graph Agent to resolve entities and update Neo4j.
    """
    activity.logger.info(
        f"Graph Update: Processing {len(entities)} entities, {len(relationships)} relationships"
    )
    result = kg_agent_process(
        entities=entities,
        relationships=relationships,
        doc_metadata=doc_metadata,
        run_id=run_id or None,
    )
    activity.logger.info(
        f"Graph Update: Created {result.get('nodes_created', 0)} nodes, "
        f"{result.get('edges_created', 0)} edges"
    )
    return result


# ── Maintenance Lifecycle Activities ──────────────────────────────────────────

@activity.defn
async def maintenance_analysis_activity(
    equipment_tag: str, analysis_type: str = "full", incident_context: str = "", run_id: str = ""
) -> dict:
    """
    Run the Maintenance Intelligence Agent on a specific equipment.
    """
    activity.logger.info(f"Maintenance: Analyzing {equipment_tag} ({analysis_type})")
    result = maintenance_analyze(
        equipment_tag=equipment_tag,
        analysis_type=analysis_type,
        incident_context=incident_context,
        run_id=run_id or None,
    )
    activity.logger.info(
        f"Maintenance: Risk={result.get('risk_level', '?')}, "
        f"Predictions={len(result.get('predictions', []))}, "
        f"Recommendations={len(result.get('recommendations', []))}"
    )
    return result


@activity.defn
async def record_work_order_activity(work_order_data: dict) -> dict:
    """
    Record a work order in the Industrial Knowledge Graph and Episodic Memory.
    """
    activity.logger.info(f"Recording work order: {work_order_data.get('wo_id', '?')}")

    # Write to graph
    industrial_graph.record_work_order(
        wo_id=work_order_data.get("wo_id", ""),
        title=work_order_data.get("title", ""),
        description=work_order_data.get("description", ""),
        equipment_tag=work_order_data.get("equipment_tag", ""),
        wo_type=work_order_data.get("type", "corrective"),
        assigned_to=work_order_data.get("assigned_to", ""),
        status=work_order_data.get("status", "open"),
        incident_id=work_order_data.get("incident_id"),
    )

    # Save to episodic memory
    memory = MemoryStore()
    memory.save_episodic_industrial(
        agent_id="MAINTENANCE",
        task=f"Work order {work_order_data.get('wo_id', '')} on {work_order_data.get('equipment_tag', '')}",
        output=work_order_data,
        equipment_tag=work_order_data.get("equipment_tag", ""),
        context_type="work_order",
    )

    return {"status": "recorded", "wo_id": work_order_data.get("wo_id", "")}


# ── Lessons Learned Pipeline Activities ───────────────────────────────────────

@activity.defn
async def lessons_learned_activity(
    incident_text: str = "",
    equipment_tag: str = "",
    incident_id: str = "",
    analysis_scope: str = "single",
    run_id: str = "",
) -> dict:
    """Run the Lessons Learned Agent."""
    activity.logger.info(f"Lessons Learned: scope={analysis_scope}, equipment={equipment_tag or 'all'}")
    result = lessons_learned_analyze(
        incident_text=incident_text,
        equipment_tag=equipment_tag,
        incident_id=incident_id,
        analysis_scope=analysis_scope,
        run_id=run_id or None,
    )
    activity.logger.info(
        f"Lessons Learned: {len(result.get('lessons', []))} lessons, "
        f"{len(result.get('warnings', []))} warnings, "
        f"{len(result.get('patterns', []))} patterns"
    )
    return result


# ── Compliance Activities ─────────────────────────────────────────────────────

@activity.defn
async def compliance_audit_activity(
    scope: str = "facility",
    area_id: str = "",
    equipment_tag: str = "",
    regulation_focus: str = "",
    run_id: str = "",
) -> dict:
    """Run the Compliance Agent."""
    activity.logger.info(f"Compliance: scope={scope}")
    result = compliance_analyze(
        scope=scope,
        area_id=area_id,
        equipment_tag=equipment_tag,
        regulation_focus=regulation_focus,
        run_id=run_id or None,
    )
    activity.logger.info(
        f"Compliance: status={result.get('overall_compliance_status', '?')}, "
        f"gaps={len(result.get('gaps', []))}"
    )
    return result


# ── Copilot Activity ──────────────────────────────────────────────────────────

@activity.defn
async def copilot_query_activity(
    query: str,
    conversation_history: list | None = None,
    run_id: str = "",
) -> dict:
    """Run the Industrial Copilot (Search Agent)."""
    activity.logger.info(f"Copilot: {query[:80]}...")
    result = search_copilot_query(
        query=query,
        conversation_history=conversation_history,
        run_id=run_id or None,
    )
    activity.logger.info(f"Copilot: intent={result.get('intent', '?')}, confidence={result.get('confidence', '?')}")
    return result

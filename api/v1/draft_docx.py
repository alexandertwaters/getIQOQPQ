# api/v1/draft_docx.py - POST /api/v1/draft-docx - convert markdown to DOCX
import io
import json
from http.server import BaseHTTPRequestHandler
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _markdown_to_docx(markdown_text):
    """Convert markdown to a simple docx. Handles # ## ### headers and paragraphs."""
    doc = Document()
    lines = (markdown_text or "").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("### "):
            p = doc.add_paragraph(stripped[4:].strip())
            p.style = "Heading 3"
        elif stripped.startswith("## "):
            p = doc.add_paragraph(stripped[3:].strip())
            p.style = "Heading 2"
        elif stripped.startswith("# "):
            p = doc.add_paragraph(stripped[2:].strip())
            p.style = "Heading 1"
        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(stripped[2:].strip(), style="List Bullet")
        elif stripped.startswith("---"):
            pass  # skip horizontal rules
        else:
            doc.add_paragraph(stripped)
        i += 1
    return doc


def _handle_post(body):
    markdown = body.get("markdownContent", "")
    if not markdown:
        return 400, None, "application/json", json.dumps({"error": "markdownContent required"}).encode()
    try:
        doc = _markdown_to_docx(markdown)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return 200, buffer.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", None
    except Exception as e:
        return 500, None, "application/json", json.dumps({"error": str(e)}).encode()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            body = json.loads(raw) if raw.strip() else {}
        except (ValueError, json.JSONDecodeError):
            body = {}
        status, data, content_type, err_body = _handle_post(body)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if data:
            self.send_header("Content-Disposition", 'attachment; filename="qualification-draft.docx"')
            self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)
        elif err_body:
            self.wfile.write(err_body)

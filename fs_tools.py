import datetime
import os
import re
from typing import Any

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None


def _file_metadata(filepath: str) -> dict:
    stat = os.stat(filepath)
    return {
        "name": os.path.basename(filepath),
        "path": filepath,
        "size": stat.st_size,
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat(),
        "extension": os.path.splitext(filepath)[1].lower(),
    }


def _extract_text_from_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as file:
        return file.read()


def _extract_text_from_pdf(filepath: str) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf is required to read PDF files. Install it with: pip install pypdf")

    reader = PdfReader(filepath)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def _extract_text_from_docx(filepath: str) -> str:
    if Document is None:
        raise RuntimeError("python-docx is required to read DOCX files. Install it with: pip install python-docx")

    document = Document(filepath)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs)


def read_file(filepath: str) -> dict:
    """
    Return text content from a resume file while preserving metadata.
    Supported: .txt, .pdf, .docx
    """
    if not os.path.exists(filepath):
        return {
            "status": "error",
            "filepath": filepath,
            "content": "",
            "metadata": {},
            "error": "File does not exist.",
        }

    if not os.path.isfile(filepath):
        return {
            "status": "error",
            "filepath": filepath,
            "content": "",
            "metadata": {},
            "error": "Path points to a directory, not a file.",
        }

    extension = os.path.splitext(filepath)[1].lower()
    try:
        if extension == ".txt":
            text = _extract_text_from_txt(filepath)
        elif extension == ".pdf":
            text = _extract_text_from_pdf(filepath)
        elif extension == ".docx":
            text = _extract_text_from_docx(filepath)
        else:
            text = _extract_text_from_txt(filepath)

        metadata = _file_metadata(filepath)
        return {
            "status": "success",
            "filepath": filepath,
            "content": text,
            "metadata": metadata,
        }
    except Exception as exc:  # pragma: no cover - runtime safety
        return {
            "status": "error",
            "filepath": filepath,
            "content": "",
            "metadata": _file_metadata(filepath) if os.path.exists(filepath) else {},
            "error": str(exc),
        }


def list_files(directory: str, extension: str = None) -> list:
    """
    Return a list of file metadata dictionaries for files in the directory.
    """
    if not os.path.exists(directory):
        return []

    if not os.path.isdir(directory):
        return []

    target_extension = (extension or "").lower()
    files = []

    for entry in os.scandir(directory):
        if entry.is_dir():
            continue

        file_extension = os.path.splitext(entry.name)[1].lower()
        if target_extension and file_extension != target_extension:
            continue

        files.append({
            "name": entry.name,
            "path": entry.path,
            "size": entry.stat().st_size,
            "modified": datetime.datetime.fromtimestamp(entry.stat().st_mtime, tz=datetime.timezone.utc).isoformat(),
            "extension": file_extension,
        })

    return sorted(files, key=lambda item: item["name"].lower())


def write_file(filepath: str, content: str) -> dict:
    """Write text content to a file, creating directories as needed."""
    try:
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(str(content))

        return {
            "status": "success",
            "filepath": filepath,
            "bytes_written": os.path.getsize(filepath),
            "message": "File written successfully.",
        }
    except Exception as exc:  # pragma: no cover - runtime safety
        return {
            "status": "error",
            "filepath": filepath,
            "error": str(exc),
            "message": "File write failed.",
        }


def search_in_file(filepath: str, keyword: str) -> dict:
    """Search a file for a case-insensitive keyword and include nearby context."""
    if not keyword:
        return {
            "status": "error",
            "filepath": filepath,
            "keyword": keyword,
            "match_count": 0,
            "matches": [],
            "error": "Keyword cannot be empty.",
        }

    read_result = read_file(filepath)
    if read_result.get("status") != "success":
        return {
            "status": "error",
            "filepath": filepath,
            "keyword": keyword,
            "match_count": 0,
            "matches": [],
            "error": read_result.get("error", "Could not read file."),
        }

    text = read_result["content"]
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches = []

    for match in pattern.finditer(text):
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        snippet = text[start:end].replace("\n", " ").strip()
        matches.append({
            "match_index": len(matches) + 1,
            "start": start,
            "end": end,
            "context": snippet,
        })

    return {
        "status": "success",
        "filepath": filepath,
        "keyword": keyword,
        "match_count": len(matches),
        "matches": matches,
    }


if __name__ == "__main__":
    print("fs_tools.py loaded successfully.")

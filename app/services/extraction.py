import io
import fitz
from PIL import Image
import pytesseract
from fastapi import HTTPException

ALLOWED = {"application/pdf", "image/png", "image/jpeg", "image/webp"}

def extract(data: bytes, mime: str) -> str:
    try:
        if mime == "application/pdf":
            with fitz.open(stream=data, filetype="pdf") as doc:
                if len(doc) > 100: raise HTTPException(413, "Maximum 100 pages")
                parts = []
                for page in doc:
                    text = page.get_text().strip()
                    if not text:
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        text = pytesseract.image_to_string(Image.open(io.BytesIO(pix.tobytes("png"))))
                    parts.append(f"[Page {page.number+1}]\n{text}")
                return "\n\n".join(parts)
        im = Image.open(io.BytesIO(data))
        im.verify()
        return pytesseract.image_to_string(Image.open(io.BytesIO(data)))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, "Could not read document or OCR is unavailable")

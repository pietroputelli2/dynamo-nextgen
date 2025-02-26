import json
import base64
import io
from PyPDF2 import PdfReader


def lambda_handler(event, _):
    try:
        if "body" not in event or not event["body"]:
            return {"statusCode": 400, "body": json.dumps({"error": "No file found in the request"})}

        # Decode base64-encoded file and convert it into a file-like object
        file_content = base64.b64decode(event["body"])
        # ✅ Convert bytes to file-like object
        file_like_obj = io.BytesIO(file_content)

        # Extract text from PDF
        pdf_text = extract_text_from_pdf(file_like_obj)

        return {"statusCode": 200, "body": json.dumps({"extracted_text": pdf_text})}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def extract_text_from_pdf(file_content):
    """Extracts text from a PDF file (file_content is a file-like object)."""
    reader = PdfReader(file_content)  # ✅ PyPDF2 expects a file-like object
    text = ""

    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"

    return text.strip()

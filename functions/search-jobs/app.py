import json
import base64
from PyPDF2 import PdfReader


def lambda_handler(event, _):
    try:
        # Extract the file from the FormData request
        if "body" not in event or not event["body"]:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No file found in the request"})
            }

        # Decode base64-encoded file from API Gateway event
        file_content = base64.b64decode(event["body"])

        # Read PDF content
        pdf_text = extract_text_from_pdf(file_content)

        return {
            "statusCode": 200,
            "body": json.dumps({"extracted_text": pdf_text})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def extract_text_from_pdf(file_content):
    """Extracts text from a PDF file (file_content is a file-like object)."""
    reader = PdfReader(file_content)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text.strip()

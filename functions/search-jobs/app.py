import json
import base64
import io
from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


def lambda_handler(event, _):
    try:
        if "body" not in event or not event["body"]:
            return {"statusCode": 400, "body": json.dumps({"error": "No file or categories found in the request"})}

        # Parse the incoming JSON payload
        body = json.loads(event["body"])

        # Ensure "file" (base64-encoded) and "categories" (array) exist
        if "file" not in body or "categories" not in body:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing 'file' or 'categories' in request body"})}

        # Decode base64-encoded file and convert it into a file-like object
        file_content = base64.b64decode(body["file"])
        file_like_obj = io.BytesIO(file_content)

        pdf_text = extract_text_from_pdf(file_like_obj)
        categories = body["categories"]

        resume_summary = summarise_resume(pdf_text)
        print(resume_summary)
        resume_summary["categories"] = categories

        query = format_resume_for_similarity_search(resume_summary)

        return {
            "statusCode": 200,
            "body": query
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def extract_text_from_pdf(file_content):
    """Extracts text from a PDF file (file_content is a file-like object)."""
    reader = PdfReader(file_content)
    text = ""

    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"

    return text.strip()


def summarise_resume(text):
    prompt = ChatPromptTemplate.from_template(
        """
            Extract the following details from the resume:

            - Programming Languages, Frameworks, and Technologies: Identify all mentioned programming languages, frameworks, libraries, tools, and technologies.
            - Total Years of Experience: Calculate the total years of experience by summing the durations of listed job positions.
            - Certifications: Extract the names of any certifications or relevant credentials.
            - Education: Identify the highest degree obtained and the field of study.
            - Skills: List all explicitly mentioned skills.
            - Ignore: Job descriptions, company names, and non-relevant details.

            Resume:
            {resume_text}

            Provide the response in a structured format:

            - technologies: <comma-separated list>
            - years_of_experience: <integer>
            - certifications: <comma-separated list>
            - education: <degree, field of study>
            - skills: <comma-separated list>

            MUST RETURN A JSON WITH KEY 'summary' and the values as the above fields as a dictionary.
        """
    )

    llm = ChatOpenAI(model="gpt-4o")

    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"resume_text": text})

    return result


def format_resume_for_similarity_search(resume):
    formatted_resume = "\n".join([
        f"{key.replace('_', ' ').title()}: {value if value else 'None'}."
        for key, value in resume.items()
    ])
    return formatted_resume

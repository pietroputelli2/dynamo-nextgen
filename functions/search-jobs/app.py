import json
import base64
import io
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from opensearchpy import OpenSearch
import openai

client = openai.OpenAI()


def generate_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


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
        resume_summary["categories"] = categories

        query = format_resume_for_similarity_search(resume_summary)

        documents = similarity_search(query)

        return {
            "statusCode": 200,
            "body": documents
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


## OpenSearch Logic ##
OPENSEARCH_HOST = "search-dynamo-next-gen-opensearch-6ac5oloug2ysx4lqt72mbdvv5e.eu-central-1.es.amazonaws.com"
OPEN_SEARCH_URL = f"https://{OPENSEARCH_HOST}"

INDEX_NAME = "resume-jobs-data-index"

HTTP_AUTH = ("user", "StrongPassword123!")

MAPPING = {
    "settings": {
        "index": {
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "vector_field": {
                "type": "knn_vector",
                "dimension": 1536,
                "method": {
                    "name": "hnsw",
                    "engine": "faiss",
                    "space_type": "l2",
                }
            }
        }
    }
}


def get_opensearch_client():
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": 443}],
        http_auth=HTTP_AUTH,
        use_ssl=True,
        verify_certs=True
    )

    return client


def create_index(client: OpenSearch):
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=MAPPING)


def similarity_search(query: str, score_threshold: float = 0.7):
    client = get_opensearch_client()
    create_index(client)

    embedded_query = generate_embedding(query)

    search_body = {
        "query": {
            "knn": {
                "vector_field": {
                    "vector": embedded_query,
                    "k": 8,
                }
            }
        }
    }

    response = client.search(index=INDEX_NAME, body=search_body)
    hits = response["hits"]["hits"]

    documents = []

    for hit in hits:
        if hit["_score"] < score_threshold:
            continue

        document = {
            "id": hit["_id"],
            "score": hit["_score"],
            "text": hit["_source"]["text"],
            "metadata": hit["_source"]["metadata"]
        }
        documents.append(document)

    return documents

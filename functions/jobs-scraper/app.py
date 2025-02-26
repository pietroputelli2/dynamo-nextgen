import os
from jobspy import scrape_jobs
import openai
from langchain.vectorstores import OpenSearchVectorSearch
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from langchain_openai import OpenAIEmbeddings

# AWS authentication
session = boto3.Session()
credentials = session.get_credentials()
region = os.getenv("AWS_REGION", "eu-central-1")
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, "es", session_token=credentials.token)

# OpenSearch setup
OPENSEARCH_HOST = os.getenv("OPENSEARCH_URL")
INDEX_NAME = "embeddings"

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


def lambda_handler(event, context):
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin",
                   "zip_recruiter", "glassdoor", "google"],
        search_term="software engineer",
        google_search_term="software engineer jobs in italy since yesterday",
        results_wanted=1,
        location="Italy",
        hours_old=72,
        country_indeed="Italy",
        is_remote=True
    )

    selected_columns = [
        "site", "job_url", "title", "company", "location",
        "date_posted", "min_amount", "max_amount", "currency",
        "is_remote", "description"
    ]

    df_selected = jobs[selected_columns]
    job_entries = df_selected.to_dict(orient="records")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    for job in job_entries:
        for key, value in job.items():
            data_to_embed = f"{key}: {value}"
            embeddings.embed_query(data_to_embed)

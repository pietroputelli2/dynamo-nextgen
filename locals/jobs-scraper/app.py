import datetime
from jobspy import scrape_jobs
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

selected_columns = [
    "site", "job_url", "title", "company", "location",
    "date_posted", "min_amount", "max_amount", "currency",
    "is_remote", "description"
]


def get_jobs_from_web():
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

    df_selected = jobs[selected_columns]
    job_entries = df_selected.to_dict(orient="records")

    return job_entries


def create_langchain_documents(jobs):
    """
    Converts a list of job dictionaries (from a Pandas DataFrame) into LangChain Document objects dynamically.
    Includes all job details inside `page_content`.
    """
    selected_columns = [
        "site", "job_url", "title", "company", "location",
        "date_posted", "min_amount", "max_amount", "currency",
        "is_remote", "description"
    ]

    documents = []

    for job in jobs:
        metadata = {}
        content_parts = []  # List to store all text data for `page_content`

        for field in selected_columns:
            # Avoid missing or NaN values
            if field in job and job[field] is not None:
                metadata[field] = job[field]

                # Convert date to string format
                if isinstance(job[field], datetime.date):
                    metadata[field] = job[field].isoformat()
                # Add to page_content string
                content_parts.append(
                    f"**{field.replace('_', ' ').title()}**: {metadata[field]}")

        # Join all parts into a single text block for `page_content`
        page_content = "\n".join(content_parts)

        # Create LangChain Document
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)

    return documents


jobs = get_jobs_from_web()
documents = create_langchain_documents(jobs)

print(documents)

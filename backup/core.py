from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_openai import OpenAIEmbeddings
from opensearchpy import OpenSearch


OPENSEARCH_HOST = "search-dynamo-next-gen-opensearch-6ac5oloug2ysx4lqt72mbdvv5e.eu-central-1.es.amazonaws.com"

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
            "text": {
                "type": "text"
            },
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


def get_store():
    create_index()

    embeddings = OpenAIEmbeddings()

    vector_store = OpenSearchVectorSearch(
        opensearch_url=OPENSEARCH_HOST,
        index_name=INDEX_NAME,
        embedding_function=embeddings,
        http_auth=HTTP_AUTH,
        vector_field="vector_field"
    )

    return vector_store


def _get_opensearch_client():
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": 443}],
        http_auth=HTTP_AUTH,
        use_ssl=True,
        verify_certs=True
    )

    return client


def create_index():
    client = _get_opensearch_client()

    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=MAPPING)

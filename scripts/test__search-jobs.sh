#!/bin/bash

# Encode the file to base64 using the correct command
base64 -i resume.pdf -o resume.b64
BASE64_FILE=$(cat resume.b64)

URL="https://cp7ol0ctf0.execute-api.eu-central-1.amazonaws.com/dev/search-jobs"

# JSON payload with base64-encoded file and categories
JSON_PAYLOAD=$(jq -n --arg file "$BASE64_FILE" --argjson categories '["Software Engineer", "Data Science"]' \
    '{file: $file, categories: $categories}')

# Send request using curl
curl -X POST "$URL" \
     -H "Content-Type: application/json" \
     -d "$JSON_PAYLOAD"

# API Gateway URL
# URL="https://cp7ol0ctf0.execute-api.eu-central-1.amazonaws.com/dev/search-jobs"

# # JSON payload with base64-encoded file and categories
# JSON_PAYLOAD=$(jq -n --arg file "$BASE64_FILE" --argjson categories '["Software Engineer", "Data Science"]' \
#     '{file: $file, categories: $categories}')

# # Send the request using curl
# curl -X POST "$URL" \
#      -H "Content-Type: application/json" \
#      -d "$JSON_PAYLOAD"
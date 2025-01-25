import os
import requests
import openai
from io import BytesIO

# Azure Computer Vision
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import (
    VisualFeatureTypes,
    OperationStatusCodes,
)
from msrest.authentication import CognitiveServicesCredentials

################################################################################
# 1. Configuration
################################################################################

# === Azure OpenAI Configuration ===
openai.api_type = "azure"
openai.api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")   # e.g. "https://<your-resource>.openai.azure.com/"
openai.api_version = os.environ.get("AZURE_OPENAI_API_VERSION")  # e.g. "2023-05-15"
openai.api_key = os.environ.get("AZURE_OPENAI_API_KEY")     # your Azure OpenAI API key

# The name of your Azure OpenAI deployment (e.g. "gpt-4" or "gpt-35-turbo" or custom).
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")  

# === Azure Computer Vision Configuration ===
AZURE_CV_ENDPOINT = os.environ.get("AZURE_CV_ENDPOINT")  # e.g. "https://<your-cv-resource>.cognitiveservices.azure.com/"
AZURE_CV_KEY = os.environ.get("AZURE_CV_KEY")            # your Computer Vision key

# === Confluence Configuration ===
CONFLUENCE_BASE_URL = "https://your-company.atlassian.net/wiki"  # or on-prem URL
CONFLUENCE_USERNAME = os.environ.get("CONFLUENCE_USERNAME")
CONFLUENCE_TOKEN = os.environ.get("CONFLUENCE_TOKEN")  # Atlassian Cloud token or password

################################################################################
# 2. Initialize Clients
################################################################################

# Azure Computer Vision client
cv_client = ComputerVisionClient(AZURE_CV_ENDPOINT, CognitiveServicesCredentials(AZURE_CV_KEY))

################################################################################
# 3. Helper: Search Confluence for pages matching a software/tool name
################################################################################

def search_confluence(software_name):
    """
    Return a list of Confluence pages that match the given software or tool name.
    This uses a simple CQL: text ~ "<software_name>" for demonstration purposes.
    Adjust as needed if you have structured data in Confluence.
    """
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/search"
    cql_query = f'text ~ "{software_name}"'
    params = {
        "cql": cql_query,
        "limit": 10,  # adjust as needed
        "expand": "body.view,metadata,version"
    }

    resp = requests.get(
        url,
        params=params,
        auth=(CONFLUENCE_USERNAME, CONFLUENCE_TOKEN),
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()

    return data.get("results", [])

################################################################################
# 4. Helper: Retrieve attachments from a Confluence page
################################################################################

def get_page_attachments(page_id):
    """
    Return a list of attachments from the specified Confluence page.
    """
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment"
    resp = requests.get(
        url,
        auth=(CONFLUENCE_USERNAME, CONFLUENCE_TOKEN),
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])

################################################################################
# 5. Helper: Analyze an image with Azure Computer Vision
################################################################################

def analyze_image(image_bytes: bytes) -> str:
    """
    Use Azure Computer Vision to extract textual description or do OCR.
    Here we'll do a 'describe_image' plus we can optionally do 'read text'.
    """
    # Describe the image
    description_result = cv_client.describe_image_in_stream(BytesIO(image_bytes))
    description_text = ""
    if description_result.captions:
        description_text = description_result.captions[0].text
    
    # Optionally, read text for OCR (a separate call in ComputerVision):
    # read_response = cv_client.read_in_stream(BytesIO(image_bytes), raw=True)
    # [poll for results, parse them, etc.]

    return description_text

################################################################################
# 6. Summarize combined text with Azure OpenAI
################################################################################

def summarize_with_azure_openai(text_content: str) -> str:
    """
    Use Azure OpenAI (Chat Completion) to produce a comprehensive summary.
    """
    if not text_content.strip():
        return "No content available to summarize."

    response = openai.ChatCompletion.create(
        engine=AZURE_OPENAI_DEPLOYMENT_NAME,  # Your Azure OpenAI deployment name
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are an AI assistant that provides comprehensive summaries "
                    "of Confluence content and extracted data from images."
                )
            },
            {
                "role": "user", 
                "content": (
                    "Here is the collected information about the software/tool. "
                    "Please write a detailed summary:\n" + text_content
                )
            }
        ],
        temperature=0.0
    )
    return response["choices"][0]["message"]["content"].strip()

################################################################################
# 7. Main "summarize software/tool" function
################################################################################

def summarize_software(software_name):
    """
    Steps:
      1. Search Confluence for pages matching the software/tool name
      2. Collect text (body.view HTML or parse it if needed)
      3. For each page, fetch attachments (images). For each image, do CV analysis.
      4. Combine text + image description
      5. Summarize with Azure OpenAI
    """
    pages = search_confluence(software_name)

    if not pages:
        return f"No Confluence pages found for '{software_name}'."

    combined_text = []

    for page in pages:
        page_id = page["id"]
        page_title = page["title"]
        page_body_html = page.get("body", {}).get("view", {}).get("value", "")

        # Basic snippet of text. For better results, parse HTML into plain text.
        text_snippet = f"Page Title: {page_title}\n\nHTML Body:\n{page_body_html}\n"
        combined_text.append(text_snippet)

        # Retrieve attachments
        attachments = get_page_attachments(page_id)
        for att in attachments:
            filename = att["title"].lower()
            if filename.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".svg")):
                # Download image
                download_link = att["_links"]["download"]
                if not download_link.startswith("http"):
                    download_link = f"{CONFLUENCE_BASE_URL}{download_link}"
                
                resp = requests.get(
                    download_link,
                    auth=(CONFLUENCE_USERNAME, CONFLUENCE_TOKEN),
                    timeout=30
                )
                resp.raise_for_status()

                # Analyze via CV
                image_description = analyze_image(resp.content)
                if image_description:
                    combined_text.append(
                        f"Image '{att['title']}' described as: {image_description}"
                    )

    # Combine everything into a single string for summarization
    big_content = "\n\n".join(combined_text)
    final_summary = summarize_with_azure_openai(big_content)
    return final_summary

################################################################################
# 8. CLI or driver code
################################################################################

if __name__ == "__main__":
    # Example usage: pass the software or tool name here
    software_tool_name = "MyCoolSoftware"
    print(f"Summarizing data for '{software_tool_name}' from Confluence...\n")
    summary = summarize_software(software_tool_name)
    print("----- COMPREHENSIVE SUMMARY -----")
    print(summary)
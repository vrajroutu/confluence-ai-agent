import os
import logging
import requests
import openai
from io import BytesIO
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Azure Computer Vision
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

################################################################################
# 1. Configuration and Environment Variable Validation
################################################################################

def get_env_var(var_name: str) -> str:
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Environment variable '{var_name}' is not set.")
    return value

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Azure OpenAI Configuration ===
openai.api_type = "azure"
openai.api_base = get_env_var("AZURE_OPENAI_ENDPOINT")        # e.g. "https://<your-resource>.openai.azure.com/"
openai.api_version = get_env_var("AZURE_OPENAI_API_VERSION")    # e.g. "2023-05-15"
openai.api_key = get_env_var("AZURE_OPENAI_API_KEY")            # your Azure OpenAI API key
AZURE_OPENAI_DEPLOYMENT_NAME = get_env_var("AZURE_OPENAI_DEPLOYMENT_NAME")

# === Azure Computer Vision Configuration ===
AZURE_CV_ENDPOINT = get_env_var("AZURE_CV_ENDPOINT")            # e.g. "https://<your-cv-resource>.cognitiveservices.azure.com/"
AZURE_CV_KEY = get_env_var("AZURE_CV_KEY")                      # your Computer Vision key

# === Confluence Configuration ===
CONFLUENCE_BASE_URL = "https://your-company.atlassian.net/wiki"  # Update if necessary
CONFLUENCE_USERNAME = get_env_var("CONFLUENCE_USERNAME")
CONFLUENCE_TOKEN = get_env_var("CONFLUENCE_TOKEN")  # Atlassian Cloud token or password

################################################################################
# 2. Initialize Clients and Sessions
################################################################################

# Initialize Azure Computer Vision client
cv_client = ComputerVisionClient(AZURE_CV_ENDPOINT, CognitiveServicesCredentials(AZURE_CV_KEY))

# Create a persistent requests session for Confluence calls
session = requests.Session()
session.auth = (CONFLUENCE_USERNAME, CONFLUENCE_TOKEN)
session.headers.update({"Content-Type": "application/json"})
DEFAULT_TIMEOUT = 30  # seconds

################################################################################
# 3. Helper Functions
################################################################################

def html_to_text(html_content: str) -> str:
    """
    Convert HTML content to plain text using BeautifulSoup.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)

def search_confluence(software_name: str) -> list:
    """
    Search Confluence for pages matching the given software/tool name using CQL.
    """
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/search"
    cql_query = f'text ~ "{software_name}"'
    params = {
        "cql": cql_query,
        "limit": 10,
        "expand": "body.view,metadata,version"
    }
    try:
        logger.info("Searching Confluence for '%s'", software_name)
        resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.error("Error searching Confluence: %s", e)
        return []

def get_page_attachments(page_id: str) -> list:
    """
    Retrieve attachments from a Confluence page.
    """
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment"
    try:
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.error("Error retrieving attachments for page %s: %s", page_id, e)
        return []

def analyze_image(image_bytes: bytes) -> str:
    """
    Analyze an image using Azure Computer Vision to extract a description.
    """
    try:
        description_result = cv_client.describe_image_in_stream(BytesIO(image_bytes))
        if description_result.captions:
            return description_result.captions[0].text
        else:
            return "No description available."
    except Exception as e:
        logger.error("Error analyzing image: %s", e)
        return "Image analysis failed."

def summarize_with_azure_openai(text_content: str) -> str:
    """
    Use Azure OpenAI (Chat Completion) to generate a summary of the provided text.
    """
    if not text_content.strip():
        return "No content available to summarize."
    
    try:
        response = openai.ChatCompletion.create(
            engine=AZURE_OPENAI_DEPLOYMENT_NAME,
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
    except Exception as e:
        logger.error("Error during summarization with OpenAI: %s", e)
        return "An error occurred while generating the summary."

################################################################################
# 4. Main Summarization Function
################################################################################

def summarize_software(software_name: str) -> str:
    """
    Search for Confluence pages, extract their text and images, and summarize the combined content.
    """
    pages = search_confluence(software_name)
    if not pages:
        return f"No Confluence pages found for '{software_name}'."
    
    combined_text_parts = []

    # Process each page
    for page in pages:
        page_id = page.get("id")
        page_title = page.get("title", "Untitled")
        page_body_html = page.get("body", {}).get("view", {}).get("value", "")
        plain_text = html_to_text(page_body_html)
        combined_text_parts.append(f"Page Title: {page_title}\n\nContent:\n{plain_text}\n")
        
        attachments = get_page_attachments(page_id)
        # Process image attachments concurrently
        image_tasks = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            for att in attachments:
                filename = att.get("title", "").lower()
                if filename.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".svg")):
                    download_link = att.get("_links", {}).get("download", "")
                    if download_link and not download_link.startswith("http"):
                        download_link = f"{CONFLUENCE_BASE_URL}{download_link}"
                    # Submit a task to download and analyze the image
                    future = executor.submit(download_and_analyze_image, download_link, att.get("title"))
                    image_tasks[future] = att.get("title")
            
            # Collect image analysis results
            for future in as_completed(image_tasks):
                image_title = image_tasks[future]
                try:
                    image_description = future.result()
                    if image_description:
                        combined_text_parts.append(
                            f"Image '{image_title}' described as: {image_description}"
                        )
                except Exception as e:
                    logger.error("Error processing image '%s': %s", image_title, e)
    
    # Combine all text for summarization
    big_content = "\n\n".join(combined_text_parts)
    logger.info("Sending combined content to Azure OpenAI for summarization...")
    final_summary = summarize_with_azure_openai(big_content)
    return final_summary

def download_and_analyze_image(download_link: str, image_title: str) -> str:
    """
    Download an image from the provided link and return its description using CV analysis.
    """
    try:
        response = session.get(download_link, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return analyze_image(response.content)
    except Exception as e:
        logger.error("Error downloading image '%s': %s", image_title, e)
        return f"Failed to analyze image '{image_title}'."

################################################################################
# 5. CLI / Driver Code
################################################################################

if __name__ == "__main__":
    # Example usage: replace "MyCoolSoftware" with your search term
    software_tool_name = "MyCoolSoftware"
    logger.info("Summarizing data for '%s' from Confluence...", software_tool_name)
    summary = summarize_software(software_tool_name)
    print("----- COMPREHENSIVE SUMMARY -----")
    print(summary)

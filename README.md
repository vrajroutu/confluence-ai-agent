Confluence Summarization Agent

This repository contains a Python script, conf.py, that performs the following steps:
	1.	Searches Confluence for pages related to a specified software or tool name.
	2.	Collects text from those pages (HTML content).
	3.	Finds images attached to these pages and analyzes them with Azure Computer Vision (to generate descriptions).
	4.	Combines all text (page text + image descriptions).
	5.	Summarizes the combined text with Azure OpenAI (ChatCompletion API).

The end result is a detailed summary of the software/tool based on the content found in Confluence (including text and relevant images).

Table of Contents
	•	Features
	•	Prerequisites
	•	Installation
	•	Environment Variables
	•	Usage
	•	Example Output
	•	How It Works
	•	Troubleshooting
	•	License
	•	Contributing

Features
	•	Search Confluence pages by software/tool name (using a simple CQL query).
	•	Parse Confluence page text (HTML) and retrieve attachments.
	•	Analyze images with Azure Computer Vision to get descriptive captions.
	•	Combine textual and image-based information.
	•	Summarize all the data using Azure OpenAI (ChatCompletion API).

Prerequisites
	1.	Python 3.7+
	2.	Azure OpenAI resource with a deployed model (e.g., GPT-3.5-Turbo or GPT-4).
	3.	Azure Computer Vision resource.
	4.	Confluence instance (Atlassian Cloud or on-prem) with valid credentials to read pages.
	5.	A software/tool name to search for in Confluence (e.g. “MyCoolSoftware”).

Installation
	1.	Clone this repository or download the files:

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>


	2.	(Optional) Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # for Linux/macOS
# or
venv\Scripts\activate     # for Windows


	3.	Install dependencies:

pip install -r requirements.txt

If you don’t have a requirements.txt, install manually:

pip install requests openai azure-cognitiveservices-vision-computervision msrest

Environment Variables

The script relies on the following environment variables to authenticate with Azure OpenAI, Azure Computer Vision, and Confluence:

Variable	Description
AZURE_OPENAI_ENDPOINT	Your Azure OpenAI endpoint, e.g. https://<resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION	Azure OpenAI API version, e.g. 2023-05-15
AZURE_OPENAI_API_KEY	Your Azure OpenAI resource key
AZURE_OPENAI_DEPLOYMENT_NAME	Deployed Azure OpenAI model name, e.g. gpt-35-turbo or gpt-4
AZURE_CV_ENDPOINT	Azure Computer Vision endpoint, e.g. https://<cv-resource>.cognitiveservices.azure.com/
AZURE_CV_KEY	Azure Computer Vision key
CONFLUENCE_BASE_URL	Base URL for your Confluence instance, e.g. https://<your-domain>.atlassian.net/wiki
CONFLUENCE_USERNAME	Confluence username or email address (for authentication)
CONFLUENCE_TOKEN	Confluence API token (Cloud) or password (on-prem)

Set these in your shell or .env file, for example:

export AZURE_OPENAI_ENDPOINT="https://my-openai-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2023-05-15"
export AZURE_OPENAI_API_KEY="YOUR_OPENAI_KEY"
export AZURE_OPENAI_DEPLOYMENT_NAME="my-gpt-deployment"

export AZURE_CV_ENDPOINT="https://my-cv-resource.cognitiveservices.azure.com/"
export AZURE_CV_KEY="YOUR_CV_KEY"

export CONFLUENCE_BASE_URL="https://my-company.atlassian.net/wiki"
export CONFLUENCE_USERNAME="my-email@company.com"
export CONFLUENCE_TOKEN="MY-CONFLUENCE-TOKEN"

Usage
	1.	Edit the conf.py file if needed (especially the default software_tool_name in the if __name__ == "__main__": block).
	2.	Run the script:

python conf.py


	3.	The script will:
	•	Prompt you (or use a hardcoded name) for the software/tool to search in Confluence.
	•	Query Confluence for matching pages.
	•	Gather page text and attachments.
	•	Use Azure Computer Vision to analyze attached images.
	•	Summarize the combined content (text + image descriptions) with Azure OpenAI.
	•	Print the summary to the console.

Passing a Different Software/Tool Name

By default, software_tool_name is set to "MyCoolSoftware". You can change this in the __main__ block of conf.py:

if __name__ == "__main__":
    software_tool_name = "MyCoolSoftware"  # Modify here
    ...

If you prefer using command-line arguments, you could modify conf.py to parse them (e.g. using sys.argv or argparse).

Example Output

$ python conf.py
Summarizing data for 'MyCoolSoftware' from Confluence...

----- COMPREHENSIVE SUMMARY -----
Below is the summarized Confluence content for MyCoolSoftware:

1. Page Title: "MyCoolSoftware Architecture"
   Text covers major components, dependencies, usage guidelines.
   Images: "diagram.png" described as: "A diagram showing three major modules..."

2. Page Title: "Setup & Installation"
   Includes step-by-step instructions, environment variables needed...

[... Further details ...]

How It Works
	1.	Search Confluence
Calls Confluence’s /rest/api/content/search with a CQL query (text ~ "<software_name>") to find relevant pages.
	2.	Gather Page Text
Retrieves each page’s HTML (body.view.value). You can parse HTML further if needed.
	3.	Fetch & Analyze Attachments
Gets attachments for each page, filtering for image file extensions. Downloads images and uses Azure Computer Vision to generate a short description or caption.
	4.	Combine & Summarize
Collects both textual content and image descriptions into one large string. Sends that to Azure OpenAI (ChatCompletion) to generate a detailed summary.
	5.	Output
Finally, prints the summary to the console for review or logging.

Troubleshooting
	•	Access/Permissions: Ensure your Confluence account/token can read the pages you expect.
	•	Empty Results: If no pages are found, verify your software_tool_name or CQL query.
	•	Rate Limits: If you see rate-limit errors from Azure or Confluence, consider throttling requests.
	•	Token Limits: Large amounts of text/images can exceed ChatCompletion token limits. If that happens, consider chunking or partial summarization.
	•	HTML Parsing: If you need more precise text extraction from Confluence (e.g., ignoring macros), integrate an HTML parser like BeautifulSoup.

License

(Optional) Provide your preferred license, for example:

MIT License

Copyright (c) 2025 ...

Permission is hereby granted, free of charge, to any person obtaining a copy
...

Contributing
	1.	Fork the repository.
	2.	Create your feature branch (git checkout -b feature/my-feature).
	3.	Commit changes (git commit -m 'Add some feature').
	4.	Push to the branch (git push origin feature/my-feature).
	5.	Open a pull request.

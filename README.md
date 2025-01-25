# Confluence Summarization Agent

This repository contains a Python script, **`conf.py`**, that performs the following steps:

1. **Searches Confluence** for pages related to a specified software or tool name.  
2. **Collects text** from those pages (HTML content).  
3. **Finds images** attached to these pages and **analyzes** them with **Azure Computer Vision** (to generate descriptions).  
4. **Combines** all text (page text + image descriptions).  
5. **Summarizes** the combined text with **Azure OpenAI** (ChatCompletion API).

The end result is a **detailed summary** of the software/tool based on the content found in Confluence (including text and relevant images).

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Passing a Different Software/Tool Name](#passing-a-different-softwaretool-name)
- [Example Output](#example-output)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)

---

## Features

- **Search Confluence pages** by software/tool name (using a simple CQL query).
- **Parse Confluence page text** (HTML) and retrieve attachments.
- **Analyze images** with Azure Computer Vision to get descriptive captions.
- **Combine** textual and image-based information.
- **Summarize** all the data using Azure OpenAI (ChatCompletion API).

---

## Prerequisites

1. **Python 3.7+**  
2. **Azure OpenAI** resource with a deployed model (e.g., GPT-3.5-Turbo or GPT-4).  
3. **Azure Computer Vision** resource.  
4. **Confluence** instance (Atlassian Cloud or on-prem) with valid credentials to read pages.  
5. A **software/tool name** to search for in Confluence (e.g. `MyCoolSoftware`).

---

## Installation

1. **Clone** this repository or download the files:
   ```bash
   git clone https://github.com/vrajroutu/confluence-ai-agent.git
   cd confluence-ai-agent

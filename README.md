---
title: OfficialURLFinder
app_file: main.py
sdk: gradio
sdk_version: 5.22.0
---
# Project Name

## Description
This project is designed to validate and verify the authenticity of official websites for various events, particularly sports events. It uses a combination of web scraping, search engine results, and various verification techniques to ensure the legitimacy of the provided URLs.

## Table of Contents
- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features
- **URL Validation**: Validates the authenticity of URLs using multiple verification techniques.
- **Web Scraping**: Extracts data from web pages to assist in verification.
- **Search Engine Integration**: Uses search engines like Google and DuckDuckGo to find and verify URLs.
- **WHOIS Lookup**: Checks domain registration information to verify authenticity.
- **SSL Certificate Check**: Verifies the SSL certificate organization to ensure the website's legitimacy.
- **Backlink Analysis**: Analyzes backlinks to determine the credibility of the website.
- **Wikipedia Integration**: Checks Wikipedia for references to the URL.

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/nantawat23308/your-repo-name.git
    cd your-repo-name
    ```

2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    Create a `.env` file in the root directory and add your environment variables:
    ```env
    SERPAPI_API_KEY=your_serpapi_key
    SERPER_API_KEY=your_serper_api_key
    ```

## Usage
To run the main script and start the URL validation process, use the following command:
```bash
python main.py
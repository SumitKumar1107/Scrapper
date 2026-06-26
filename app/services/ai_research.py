import os
import json
import logging
import socket
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import requests
from urllib3.util.connection import allowed_gai_family

# Force IPv4 to avoid Render IPv6 being misidentified by Google
import urllib3.util.connection
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

load_dotenv()

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "research_prompt.txt"
QUARTERLY_PROMPT_TEMPLATE_PATH = (
    Path(__file__).parent.parent.parent / "quarterly_research_prompt.txt"
)
GEMINI_MODEL = "gemini-3.1-pro-preview"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def load_prompt_template(path: Path = PROMPT_TEMPLATE_PATH) -> str:
    """
    Read the research prompt template from research_prompt.txt.

    Returns:
        The prompt template string with {company_name} placeholder.

    Raises:
        FileNotFoundError: If research_prompt.txt is missing.
    """
    if not path.exists():
        logger.error(f"Prompt template not found at {path}")
        raise FileNotFoundError(
            f"Research prompt template not found: {path}"
        )

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _generate_content(prompt: str, use_google_search: bool = True) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Please set it in your .env file."
        )

    tools = [{"codeExecution": {}}]
    if use_google_search:
        tools.append({"googleSearch": {}})

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 65536,
        },
        "tools": tools
    }

    resp = requests.post(
        f"{GEMINI_API_URL}?key={api_key}",
        json=payload,
        timeout=120
    )

    if resp.status_code != 200:
        error_msg = resp.text
        logger.error(f"Gemini API error {resp.status_code}: {error_msg}")
        raise Exception(f"Gemini API error: {resp.status_code} - {error_msg}")

    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]

    if not text:
        raise Exception("Gemini API returned an empty response")

    return text


def generate_research(company_name: str) -> str:
    """Generate broad AI research for a company."""
    template = load_prompt_template()
    prompt = template.replace("{company_name}", company_name)

    logger.info(f"Generating AI research for: {company_name}")
    text = _generate_content(prompt)
    logger.info(f"AI research generated successfully for: {company_name}")
    return text


def _quarter_record(
    quarterly_data: Dict[str, Any],
    index: int
) -> Optional[Dict[str, Any]]:
    periods = quarterly_data.get("periods", [])
    if not periods:
        return None

    actual_index = index if index >= 0 else len(periods) + index
    if actual_index < 0 or actual_index >= len(periods):
        return None

    record = {"period": periods[actual_index]}
    metrics = (
        "sales",
        "expenses",
        "operating_profit",
        "opm_percent",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percent",
        "net_profit",
        "eps",
    )

    for metric in metrics:
        values = quarterly_data.get(metric, [])
        record[metric] = (
            values[actual_index] if actual_index < len(values) else None
        )

    return record


def generate_quarterly_research(
    ticker: str,
    company_name: str,
    quarterly_data: Dict[str, Any]
) -> str:
    """Analyze the latest available quarter using structured scraped data."""
    latest = _quarter_record(quarterly_data, -1)
    if not latest:
        raise ValueError("No quarterly result data is available for this company.")

    previous = _quarter_record(quarterly_data, -2)
    year_ago = _quarter_record(quarterly_data, -5)
    history = []
    start = max(0, len(quarterly_data.get("periods", [])) - 8)
    for index in range(start, len(quarterly_data.get("periods", []))):
        record = _quarter_record(quarterly_data, index)
        if record:
            history.append(record)

    template = load_prompt_template(QUARTERLY_PROMPT_TEMPLATE_PATH)
    replacements = {
        "{company_name}": company_name,
        "{ticker}": ticker,
        "{latest_quarter}": json.dumps(latest, indent=2),
        "{previous_quarter}": json.dumps(previous, indent=2),
        "{year_ago_quarter}": json.dumps(year_ago, indent=2),
        "{quarterly_history}": json.dumps(history, indent=2),
    }
    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    logger.info(
        f"Generating quarterly AI research for: {ticker} ({latest['period']})"
    )
    text = _generate_content(prompt, use_google_search=True)
    logger.info(f"Quarterly AI research generated successfully for: {ticker}")
    return text

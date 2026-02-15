import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "research_prompt.txt"
GEMINI_MODEL = "gemini-3-pro-preview"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def load_prompt_template() -> str:
    """
    Read the research prompt template from research_prompt.txt.

    Returns:
        The prompt template string with {company_name} placeholder.

    Raises:
        FileNotFoundError: If research_prompt.txt is missing.
    """
    if not PROMPT_TEMPLATE_PATH.exists():
        logger.error(f"Prompt template not found at {PROMPT_TEMPLATE_PATH}")
        raise FileNotFoundError(
            f"Research prompt template not found: {PROMPT_TEMPLATE_PATH}"
        )

    with open(PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def generate_research(company_name: str) -> str:
    """
    Generate AI research analysis for a company using Google Gemini REST API.

    Args:
        company_name: Full company name (e.g., "Reliance Industries")

    Returns:
        Markdown-formatted research analysis string.

    Raises:
        ValueError: If GEMINI_API_KEY is not configured.
        Exception: If Gemini API call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Please set it in your .env file."
        )

    template = load_prompt_template()
    prompt = template.replace("{company_name}", company_name)

    logger.info(f"Generating AI research for: {company_name}")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 65536,
        }
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

    logger.info(f"AI research generated successfully for: {company_name}")
    return text

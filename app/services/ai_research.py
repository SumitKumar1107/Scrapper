import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "research_prompt.txt"


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
    Generate AI research analysis for a company using Google Gemini.

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

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    logger.info(f"Generating AI research for: {company_name}")

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=4096,
        )
    )

    if not response or not response.text:
        raise Exception("Gemini API returned an empty response")

    logger.info(f"AI research generated successfully for: {company_name}")
    return response.text

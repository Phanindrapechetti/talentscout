"""
data_handler.py
---------------
Handles secure saving and loading of candidate information.
Data is stored locally in a JSON file (simulated database).
Follows GDPR-friendly practices: no unnecessary data, clear purpose.
"""

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = Path("candidate_data")
DATA_FILE = DATA_DIR / "candidates.json"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_data_dir():
    """Creates the data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    gitignore = DATA_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# Candidate data - do not commit\n*\n!.gitignore\n")


# ---------------------------------------------------------------------------
# Privacy helpers
# ---------------------------------------------------------------------------

def mask_email(email: str) -> str:
    """Returns a masked version of the email for display purposes."""
    if not email or "@" not in email:
        return "****"
    local, domain = email.split("@", 1)
    masked_local = local[0] + "***" if len(local) > 1 else "***"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Returns a masked phone number showing only last 4 digits."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 4:
        return "****" + digits[-4:]
    return "****"


def anonymize_id(name: str, email: str) -> str:
    """Generates an anonymized candidate ID using a hash."""
    raw = f"{name.lower().strip()}{email.lower().strip()}"
    return "CAND-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()


# ---------------------------------------------------------------------------
# LLM-based candidate info extraction
# ---------------------------------------------------------------------------

def extract_candidate_info_via_llm(chat_history: list) -> dict:
    """
    Uses the Groq LLM to extract all candidate info from the full conversation.
    This is much more accurate than regex-based extraction.
    """
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    fallback = {
        "full_name": "not provided",
        "email": "not provided",
        "phone": "not provided",
        "years_of_experience": "not provided",
        "desired_positions": "not provided",
        "current_location": "not provided",
        "tech_stack": "not provided",
    }

    if not chat_history:
        return fallback

    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return fallback

        client = Groq(api_key=api_key)

        # Build plain text transcript
        transcript = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in chat_history
        )

        extraction_prompt = f"""
You are a data extraction assistant. Read the following job interview chatbot transcript 
and extract the candidate's information.

TRANSCRIPT:
{transcript}

Extract ONLY what the candidate explicitly stated. If a field was not mentioned, use "not provided".

Respond with ONLY a valid JSON object in this exact format (no extra text, no markdown):
{{
  "full_name": "candidate's full name",
  "email": "candidate's email address",
  "phone": "candidate's phone number",
  "years_of_experience": "number of years",
  "desired_positions": "position(s) they want",
  "current_location": "city and country",
  "tech_stack": "comma-separated list of all technologies mentioned"
}}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.0,
            max_tokens=400,
        )

        raw = response.choices[0].message.content.strip()

        # Clean markdown if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.split("```")[0]

        result = json.loads(raw.strip())

        # Fill missing keys with fallback
        for key in fallback:
            if key not in result or not result[key]:
                result[key] = "not provided"

        return result

    except Exception as e:
        print(f"[data_handler] LLM extraction failed: {e}")
        return fallback


# ---------------------------------------------------------------------------
# Simple regex-based extraction for real-time sidebar updates
# ---------------------------------------------------------------------------

def extract_candidate_info(chat_history: list) -> dict:
    """
    Lightweight real-time extraction for sidebar display during conversation.
    Only catches email and phone via regex — fast for live updates.
    Full accurate extraction happens via LLM at save time.
    """
    info = {}

    for msg in chat_history:
        if msg["role"] == "user":
            content = msg["content"].strip()

            # Email detection
            email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content)
            if email_match and "email" not in info:
                info["email"] = email_match.group()

            # Phone detection
            phone_match = re.search(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{4,6}", content)
            if phone_match and "phone" not in info:
                info["phone"] = phone_match.group()

    return info


# ---------------------------------------------------------------------------
# Save candidate
# ---------------------------------------------------------------------------

def save_candidate(candidate_info: dict, chat_history: list = None) -> str:
    """
    Saves candidate information to the local JSON database.
    Uses LLM to extract complete info from chat_history if provided.

    Args:
        candidate_info: Partial dict from real-time extraction.
        chat_history: Full conversation for accurate LLM extraction.

    Returns:
        The anonymized candidate ID string.
    """
    ensure_data_dir()

    # Use LLM extraction for complete, accurate data
    if chat_history:
        print("[data_handler] Running LLM extraction for complete candidate data...")
        extracted = extract_candidate_info_via_llm(chat_history)
        candidate_info = {**candidate_info, **extracted}

    # Load existing records
    existing = []
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []

    name = candidate_info.get("full_name", "Unknown")
    email = candidate_info.get("email", "")
    phone = candidate_info.get("phone", "")

    record = {
        "candidate_id": anonymize_id(name, email),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "full_name": name,
        "email_masked": mask_email(email) if email and email != "not provided" else "not provided",
        "phone_masked": mask_phone(phone) if phone and phone != "not provided" else "not provided",
        "years_of_experience": candidate_info.get("years_of_experience", "not provided"),
        "desired_positions": candidate_info.get("desired_positions", "not provided"),
        "current_location": candidate_info.get("current_location", "not provided"),
        "tech_stack": candidate_info.get("tech_stack", "not provided"),
        "data_consent": True,
        "gdpr_note": "Data stored for recruitment purposes only. Retained for 90 days."
    }

    existing.append(record)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"[data_handler] Saved: {record['candidate_id']}")
    return record["candidate_id"]


# ---------------------------------------------------------------------------
# Load all candidates
# ---------------------------------------------------------------------------

def load_all_candidates() -> list:
    """Returns all saved candidate records."""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
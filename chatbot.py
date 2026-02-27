import os
import json
from groq import Groq
from dotenv import load_dotenv
from prompts import build_messages, SENTIMENT_PROMPT

# Load environment variables from .env file
load_dotenv()


# Initialize Groq client


def get_client() -> Groq:
    """
    Creates and returns a Groq client using the API key from environment.
    Raises a clear error if the key is missing.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found! Please add it to your .env file.\n"
            "Example: GROQ_API_KEY=your_key_here"
        )
    return Groq(api_key=api_key)



# Main chat function


def get_chat_response(chat_history: list) -> str:
    """
    Sends the full conversation history to Groq and returns the assistant's reply.
    
    Args:
        chat_history: List of {"role": "user"/"assistant", "content": str} dicts
                      representing the entire conversation so far.
    
    Returns:
        The assistant's response as a plain string.
    """
    try:
        client = get_client()
        
        messages = build_messages(chat_history)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Best free model on Groq
            messages=messages,
            temperature=0.7,                    # Balanced creativity vs consistency
            max_tokens=1024,                    # Enough for detailed tech questions
            top_p=0.9,
        )
        
        return response.choices[0].message.content
    
    except ValueError as e:
        # Missing API key
        return f"⚠️ Configuration Error: {str(e)}"
    
    except Exception as e:
        # Network issues, rate limits, etc.
        error_msg = str(e)
        if "rate_limit" in error_msg.lower():
            return "⚠️ I'm receiving too many requests right now. Please wait a moment and try again."
        elif "authentication" in error_msg.lower():
            return "⚠️ Invalid API key. Please check your GROQ_API_KEY in the .env file."
        else:
            return f"⚠️ Something went wrong: {error_msg}. Please try again."



# Sentiment Analysis function 


def analyze_sentiment(message: str) -> dict:
    """
    Analyzes the emotional tone of a candidate's message.
    
    Args:
        message: The candidate's raw text input.
    
    Returns:
        A dict with keys: sentiment, confidence, note
        Falls back to neutral on any error.
    """
    fallback = {
        "sentiment": "neutral",
        "confidence": 0.5,
        "note": "Unable to analyze sentiment."
    }
    
    if not message or len(message.strip()) < 3:
        return fallback
    
    try:
        client = get_client()
        
        prompt = SENTIMENT_PROMPT.format(message=message)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,    # Low temperature for consistent classification
            max_tokens=150,
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        result = json.loads(raw)
        
        # Validate required keys
        if all(k in result for k in ["sentiment", "confidence", "note"]):
            return result
        return fallback
    
    except Exception:
        return fallback


# Exit keyword detection


EXIT_KEYWORDS = {
    "bye", "goodbye", "exit", "quit", "stop", "end",
    "done", "finish", "finished", "that's all", "thats all",
    "see you", "ciao", "adios", "farewell"
}

def is_exit_intent(message: str) -> bool:
    """
    Checks if the user's message contains an exit/farewell intent.
    
    Args:
        message: Raw user input string.
    
    Returns:
        True if the message signals conversation end, False otherwise.
    """
    cleaned = message.lower().strip().rstrip("!.,")
    
    # Direct match
    if cleaned in EXIT_KEYWORDS:
        return True
    
    # Phrase match
    for keyword in EXIT_KEYWORDS:
        if keyword in cleaned:
            return True
    
    return False

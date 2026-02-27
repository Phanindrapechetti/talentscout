# 🤖 TalentScout Hiring Assistant

An AI-powered hiring assistant chatbot built for **TalentScout**, a fictional recruitment agency specializing in technology placements. Built with Streamlit + LLaMA 3.3 via Groq API.

---

## 📌 Project Overview

TalentScout Hiring Assistant automates the initial screening of tech candidates by:
- Greeting candidates and explaining the process
- Collecting essential personal and professional information
- Generating tailored technical questions based on the candidate's tech stack
- Analyzing candidate sentiment in real-time (bonus feature)
- Storing candidate data securely in compliance with GDPR

---

## 🗂️ Project Structure

```
talentscout/
│
├── app.py              # Main Streamlit UI and chat logic
├── chatbot.py          # Groq LLM integration + sentiment analysis
├── prompts.py          # System prompts and prompt engineering
├── data_handler.py     # Candidate data storage (GDPR-friendly)
├── requirements.txt    # Python dependencies
├── .env.example        # Template for environment variables
├── .env                # YOUR actual API key (never commit this)
├── .gitignore          # Protects sensitive files
└── README.md           # This file
```

---

## ⚙️ Installation Instructions

### Step 1: Clone or download the project
```bash
git clone https://github.com/Phanindrapechetti/talentscout.git
cd talentscout
```

### Step 2: Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set up your API key
1. Go to [https://console.groq.com](https://console.groq.com) and sign up (free)
2. Create an API key under **API Keys**
3. Copy `.env.example` and rename it to `.env`
4. Open `.env` and replace `your_groq_api_key_here` with your actual key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 5: Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## 🚀 Usage Guide

1. **Start**: Open the app — Scout greets you automatically.
2. **Info Gathering**: Answer Scout's questions one by one (name, email, phone, experience, position, location, tech stack).
3. **Technical Questions**: Scout generates 3–5 questions per technology in your stack.
4. **Answer**: Respond to the technical questions at your own pace.
5. **End**: Say "bye", "done", or "exit" to end the session gracefully.
6. **Sidebar**: Watch your info and sentiment be tracked in real-time on the left panel.
7. **New Session**: Click "🔄 New Session" to restart.

---

## 🛠️ Technical Details

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit 1.32+ |
| LLM | LLaMA 3.3 70B (via Groq API) |
| Language | Python 3.9+ |
| Data Storage | Local JSON file |
| Sentiment Analysis | LLaMA 3.3 (same model, separate prompt) |
| Auth / Secrets | python-dotenv |

### Why Groq + LLaMA 3.3?
- **Free tier** with generous limits (14,400 req/day)
- **Extremely fast** inference (Groq's custom hardware)
- **LLaMA 3.3 70B** is highly capable for multi-turn conversation
- No credit card required to start

---

## 🧠 Prompt Design

### System Prompt Strategy
The system prompt in `prompts.py` uses a **staged conversation** approach:

1. **Stage 1 — Greeting**: Sets warm, professional tone
2. **Stage 2 — Info Gathering**: Enforces one-question-at-a-time rule to avoid overwhelming candidates
3. **Stage 3 — Tech Questions**: Instructs the model to group questions by technology and vary difficulty
4. **Stage 4 — Wrap Up**: Provides exact closing message with next steps

### Key Prompt Engineering Decisions
- **Explicit stage labels** prevent the LLM from jumping ahead or skipping info
- **Negative constraints** ("NEVER ask multiple questions at once", "ONLY discuss hiring topics") reduce off-topic drift
- **Example questions** in the prompt guide the model toward the right difficulty level
- **Exit keyword handling** injects a stage hint `[CANDIDATE IS ENDING THE CONVERSATION]` so the LLM knows to wrap up immediately
- **Sentiment prompt** uses temperature=0.1 and asks for strict JSON to ensure parseable output

### Fallback Mechanism
- If user input is unclear, the system prompt instructs Scout to ask for clarification and repeat the current question
- The `is_exit_intent()` function catches common farewell phrases before the LLM processes them

---

## 🔒 Data Privacy & GDPR Compliance

- **Minimal data collection**: Only collects what's needed for recruitment screening
- **Masking**: Emails and phone numbers are masked in storage and the UI (e.g., `j***@gmail.com`)
- **Anonymized IDs**: Candidates get a SHA-256 hashed ID — no raw PII in identifiers
- **Local storage**: Data stays on your machine in `candidate_data/candidates.json`
- **Git protection**: `candidate_data/` is in `.gitignore` and has its own nested `.gitignore`
- **Retention note**: Each record includes a GDPR note: "Retained for 90 days"
- **Consent**: Proceeding with the interview implies consent (noted in the record)

---

## ⚡ Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Keeping LLM on topic | Explicit "STRICT RULES" section in system prompt with redirect instruction |
| One-question-at-a-time | System prompt rule + tested across multiple LLM responses |
| Detecting conversation end | Two-layer: `is_exit_intent()` keyword check + farewell signal detection in LLM response |
| Sentiment JSON parsing | Low temperature + cleanup for markdown code blocks before `json.loads()` |
| Context across turns | Full chat history passed on every API call (Groq handles this efficiently) |
| Sensitive data display | Masking functions in `data_handler.py`, never display raw email/phone |

---


## 📄 License

This project is for educational/assignment purposes. Feel free to use and modify.

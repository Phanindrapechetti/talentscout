"""
app.py
------
Main Streamlit application for the TalentScout Hiring Assistant chatbot.
Run with: streamlit run app.py
"""

import streamlit as st
from chatbot import get_chat_response, analyze_sentiment, is_exit_intent
from data_handler import save_candidate, extract_candidate_info, mask_email, mask_phone

# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TalentScout Hiring Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — consistent in BOTH light and dark mode
# We force a dark background always so the app looks identical on all devices
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Force dark background on ALL devices and modes */
    .stApp,
    .stApp > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMain"],
    [data-testid="block-container"] {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed !important;
    }

    /* Force ALL text white so it's always readable on dark bg */
    .stApp, .stApp p, .stApp span, .stApp div,
    .stApp label, .stApp li, .stApp small,
    .stApp strong, .stApp em, .stMarkdown p,
    .stMarkdown li, .stMarkdown span {
        color: #f0f0f0 !important;
    }

    /* Chat message content */
    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessageContent"] div,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] strong,
    [data-testid="stChatMessageContent"] em,
    [data-testid="stChatMessageContent"] code {
        color: #ffffff !important;
        font-size: 15px !important;
        line-height: 1.75 !important;
    }

    /* Chat bubbles */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stChatMessageUser"] {
        background: rgba(99, 102, 241, 0.25) !important;
        border-left: 3px solid #6366f1 !important;
    }
    [data-testid="stChatMessageAssistant"] {
        background: rgba(16, 185, 129, 0.15) !important;
        border-left: 3px solid #10b981 !important;
    }

    /* Headings */
    h1 {
        background: linear-gradient(90deg, #6366f1, #10b981) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 2rem !important;
    }
    h2, h3, h4, h5, h6 {
        color: #e0e0e0 !important;
        -webkit-text-fill-color: #e0e0e0 !important;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background: rgba(10, 8, 40, 0.97) !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] small,
    section[data-testid="stSidebar"] strong {
        color: #e0e0e0 !important;
        -webkit-text-fill-color: #e0e0e0 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Caption text */
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span {
        color: #aaaaaa !important;
        -webkit-text-fill-color: #aaaaaa !important;
    }

    /* Metric widget */
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Info card */
    .info-card {
        background: rgba(255,255,255,0.08) !important;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.15);
    }

    /* Chat input box */
    [data-testid="stChatInput"] textarea,
    .stChatInputContainer textarea {
        background: rgba(255,255,255,0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important;
    }
    .stChatInputContainer textarea::placeholder {
        color: #aaaaaa !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }

    /* Alert boxes text */
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.12) !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
    ::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.5); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def init_session_state():
    """Initialize all session state variables on first load."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False
    if "candidate_info" not in st.session_state:
        st.session_state.candidate_info = {}
    if "sentiment_history" not in st.session_state:
        st.session_state.sentiment_history = []
    if "candidate_saved" not in st.session_state:
        st.session_state.candidate_saved = False
    if "greeted" not in st.session_state:
        st.session_state.greeted = False


init_session_state()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-2.png", width=70)
    st.title("TalentScout")
    st.caption("AI-Powered Hiring Assistant")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col2:
        msg_count = len(st.session_state.chat_history)
        st.metric("Messages", msg_count)

    st.divider()

    st.subheader("📋 Candidate Info")
    info = st.session_state.candidate_info

    if not info:
        st.caption("_Information will appear here as the conversation progresses..._")
    else:
        fields_display = {
            "full_name": ("👤 Name", lambda v: v),
            "email": ("📧 Email", mask_email),
            "phone": ("📱 Phone", mask_phone),
            "years_of_experience": ("💼 Experience", lambda v: f"{v} years"),
            "desired_positions": ("🎯 Position", lambda v: v),
            "current_location": ("📍 Location", lambda v: v),
            "tech_stack": ("🛠️ Tech Stack", lambda v: v),
        }
        for field, (label, formatter) in fields_display.items():
            if field in info and info[field]:
                st.markdown(f"""
                <div class="info-card">
                    <small style="color: #aaaaaa;">{label}</small><br>
                    <strong style="color: #ffffff;">{formatter(str(info[field]))}</strong>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    st.subheader("💬 Sentiment Analysis")

    if not st.session_state.sentiment_history:
        st.caption("_Sentiment will be tracked as you chat..._")
    else:
        latest = st.session_state.sentiment_history[-1]

        sentiment_colors = {
            "positive": "#10b981", "confident": "#6366f1",
            "neutral": "#94a3b8", "anxious": "#f59e0b", "negative": "#ef4444",
        }
        sentiment_emojis = {
            "positive": "😊", "confident": "💪",
            "neutral": "😐", "anxious": "😟", "negative": "😔",
        }

        s = latest["sentiment"]
        color = sentiment_colors.get(s, "#94a3b8")
        emoji = sentiment_emojis.get(s, "🤔")
        confidence_pct = int(latest["confidence"] * 100)

        st.markdown(f"""
        <div class="info-card">
            <div style="font-size: 1.5rem">{emoji}</div>
            <div style="color: {color}; font-weight: bold; text-transform: capitalize; font-size: 1.1rem">
                {s}
            </div>
            <div style="color: #bbbbbb; font-size: 0.8rem">Confidence: {confidence_pct}%</div>
            <div style="color: #dddddd; font-size: 0.8rem; margin-top: 4px; font-style: italic">
                {latest["note"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if len(st.session_state.sentiment_history) > 1:
            st.caption("Recent trend:")
            trend_line = " → ".join(
                sentiment_emojis.get(s["sentiment"], "🤔")
                for s in st.session_state.sentiment_history[-5:]
            )
            st.markdown(
                f"<div style='font-size: 1.2rem; letter-spacing: 4px; color: #ffffff;'>{trend_line}</div>",
                unsafe_allow_html=True
            )

    st.divider()
    st.caption("🔒 Data handled per GDPR guidelines")
    st.caption("Built with ❤️ using Streamlit + LLaMA 3.3")

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

st.title("🤖 TalentScout Hiring Assistant")
st.caption("Welcome! I'm Scout, your AI-powered hiring assistant. Let's get started.")
st.divider()

# ---------------------------------------------------------------------------
# Auto-greet on first load
# ---------------------------------------------------------------------------

if not st.session_state.greeted:
    with st.spinner("Scout is warming up..."):
        greeting = get_chat_response([])
    st.session_state.chat_history.append({"role": "assistant", "content": greeting})
    st.session_state.greeted = True

# ---------------------------------------------------------------------------
# Display chat history
# ---------------------------------------------------------------------------

for message in st.session_state.chat_history:
    role = message["role"]
    with st.chat_message(role, avatar="🤖" if role == "assistant" else "🧑"):
        st.markdown(message["content"])

# ---------------------------------------------------------------------------
# Conversation ended state
# ---------------------------------------------------------------------------

if st.session_state.conversation_ended:
    st.success("✅ Interview session complete! Thank you for your time.")
    if not st.session_state.candidate_saved:
        candidate_id = save_candidate(
            st.session_state.candidate_info,
            chat_history=st.session_state.chat_history
        )
        st.session_state.candidate_saved = True
        st.info(f"📁 Your application has been recorded. Reference ID: `{candidate_id}`")
    if st.button("🔄 Start New Session", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

user_input = st.chat_input(
    "Type your response here...",
    disabled=st.session_state.conversation_ended
)

if user_input:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    st.session_state.chat_history.append({"role": "user", "content": user_input})

    sentiment = analyze_sentiment(user_input)
    st.session_state.sentiment_history.append(sentiment)

    extracted = extract_candidate_info(st.session_state.chat_history)
    st.session_state.candidate_info.update(extracted)

    if is_exit_intent(user_input):
        st.session_state.chat_history[-1]["content"] = (
            user_input + " [CANDIDATE IS ENDING THE CONVERSATION - PROCEED TO STAGE 4 WRAP UP]"
        )

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Scout is thinking..."):
            response = get_chat_response(st.session_state.chat_history)
        st.markdown(response)

    st.session_state.chat_history.append({"role": "assistant", "content": response})

    farewell_signals = [
        "good luck", "best of luck", "our team will review",
        "reach out within", "thank you for your time",
        "we'll be in touch", "goodbye", "take care"
    ]
    if any(signal in response.lower() for signal in farewell_signals):
        if st.session_state.candidate_info and not st.session_state.candidate_saved:
            save_candidate(
                st.session_state.candidate_info,
                chat_history=st.session_state.chat_history
            )
            st.session_state.candidate_saved = True
        st.session_state.conversation_ended = True

    st.rerun()
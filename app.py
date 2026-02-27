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
# Custom CSS styling
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    }
    
    /* Chat message bubbles */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }
    
    /* User message */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background: rgba(99, 102, 241, 0.15);
        border-left: 3px solid #6366f1;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background: rgba(16, 185, 129, 0.1);
        border-left: 3px solid #10b981;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(15, 12, 41, 0.9);
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(90deg, #6366f1, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem !important;
    }
    
    /* Sentiment badge */
    .sentiment-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 4px;
    }
    
    /* Info card in sidebar */
    .info-card {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Input box */
    .stChatInputContainer {
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 10px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.85;
    }
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
    
    # Session controls
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
    
    # Candidate info collected so far
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
                    <small style="color: #aaa;">{label}</small><br>
                    <strong>{formatter(str(info[field]))}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    # Sentiment Analysis Panel
    st.subheader("💬 Sentiment Analysis")
    
    if not st.session_state.sentiment_history:
        st.caption("_Sentiment will be tracked as you chat..._")
    else:
        latest = st.session_state.sentiment_history[-1]
        
        sentiment_colors = {
            "positive": "#10b981",
            "confident": "#6366f1",
            "neutral": "#94a3b8",
            "anxious": "#f59e0b",
            "negative": "#ef4444",
        }
        
        sentiment_emojis = {
            "positive": "😊",
            "confident": "💪",
            "neutral": "😐",
            "anxious": "😟",
            "negative": "😔",
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
            <div style="color: #aaa; font-size: 0.8rem">Confidence: {confidence_pct}%</div>
            <div style="color: #ccc; font-size: 0.8rem; margin-top: 4px; font-style: italic">
                {latest["note"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Sentiment trend over last 5 messages
        if len(st.session_state.sentiment_history) > 1:
            st.caption("Recent trend:")
            trend_line = " → ".join(
                sentiment_emojis.get(s["sentiment"], "🤔")
                for s in st.session_state.sentiment_history[-5:]
            )
            st.markdown(f"<div style='font-size: 1.2rem; letter-spacing: 4px'>{trend_line}</div>",
                        unsafe_allow_html=True)
    
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
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": greeting
    })
    st.session_state.greeted = True

# ---------------------------------------------------------------------------
# Display chat history
# ---------------------------------------------------------------------------

for i, message in enumerate(st.session_state.chat_history):
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role, avatar="🤖" if role == "assistant" else "🧑"):
        st.markdown(content)

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
    # --- Display user message immediately ---
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    
    # --- Add to history ---
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # --- Sentiment analysis (bonus feature) ---
    sentiment = analyze_sentiment(user_input)
    st.session_state.sentiment_history.append(sentiment)
    
    # --- Update candidate info from message ---
    extracted = extract_candidate_info(st.session_state.chat_history)
    st.session_state.candidate_info.update(extracted)
    
    # --- Check for exit intent ---
    if is_exit_intent(user_input):
        # Add farewell to history so LLM wraps up properly
        st.session_state.chat_history[-1]["content"] = (
            user_input + " [CANDIDATE IS ENDING THE CONVERSATION - PROCEED TO STAGE 4 WRAP UP]"
        )
    
    # --- Get LLM response ---
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Scout is thinking..."):
            response = get_chat_response(st.session_state.chat_history)
        st.markdown(response)
    
    # --- Add assistant response to history ---
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response
    })
    
    # --- Check if conversation should end ---
    farewell_signals = [
        "good luck", "best of luck", "our team will review",
        "reach out within", "thank you for your time",
        "we'll be in touch", "goodbye", "take care"
    ]
    
    response_lower = response.lower()
    if any(signal in response_lower for signal in farewell_signals):
        # Save candidate data before marking ended
        if st.session_state.candidate_info and not st.session_state.candidate_saved:
            save_candidate(
                st.session_state.candidate_info,
                chat_history=st.session_state.chat_history
            )
            st.session_state.candidate_saved = True
        st.session_state.conversation_ended = True
    
    # --- Rerun to refresh sidebar with new info ---
    st.rerun()
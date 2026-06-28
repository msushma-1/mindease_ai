import streamlit as st
from groq import Groq
from datetime import datetime
import json
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MindEase — Mental Wellness Companion",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap');

:root {
    --sage:      #7a9e87;
    --sage-soft: #7a9e8722;
    --dusk:      #1a1f2e;
    --surface:   #222736;
    --border:    #2e3447;
    --lavender:  #b8a9d9;
    --sand:      #e8e0d0;
    --muted:     #6b7280;
    --text:      #e8e4dc;
    --warm:      #d4a373;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--dusk);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

.hero { padding: 2.5rem 0 1rem; text-align: center; }
.hero-title {
    font-family: 'Fraunces', serif;
    font-weight: 300; font-size: 3rem;
    color: var(--sand); letter-spacing: -0.5px;
    line-height: 1.1; margin-bottom: 0.3rem;
}
.hero-title span { font-style: italic; color: var(--sage); }
.hero-sub { color: var(--muted); font-size: 1rem; }

.bubble-user {
    background: var(--sage-soft); border: 1px solid var(--sage);
    border-radius: 18px 18px 4px 18px;
    padding: 0.85rem 1.1rem; margin: 0.6rem 0 0.6rem 4rem;
    color: var(--text); line-height: 1.6;
}
.bubble-ai {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 18px 18px 18px 4px;
    padding: 0.85rem 1.1rem; margin: 0.6rem 4rem 0.6rem 0;
    color: var(--text); line-height: 1.7;
}
.bubble-label {
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.3rem;
}

.crisis-banner {
    background: #2d1f1f; border: 1px solid #7f3333;
    border-radius: 12px; padding: 1rem 1.2rem;
    margin: 1rem 0; font-size: 0.9rem; color: #f0a0a0;
}
.resource-card {
    background: var(--surface); border: 1px solid var(--border);
    border-left: 3px solid var(--lavender); border-radius: 10px;
    padding: 0.8rem 1rem; margin: 0.4rem 0; font-size: 0.88rem;
}
.resource-card b { color: var(--lavender); }

.mood-dot {
    display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; margin: 2px;
}

/* Feature badge */
.badge {
    display: inline-block;
    background: var(--sage-soft); color: var(--sage);
    border: 1px solid var(--sage); border-radius: 20px;
    padding: 2px 10px; font-size: 0.72rem; font-weight: 600;
    margin: 2px;
}

.stTextInput > div > div > input {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button {
    background: var(--sage) !important; color: white !important;
    border: none !important; border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; padding: 0.5rem 1.4rem !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stSelectbox > div > div {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
}
hr { border-color: var(--border) !important; }

/* Fix audio player to full width */
audio {
    width: 100% !important;
    border-radius: 10px !important;
}
[data-testid="stAudio"] {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)


# ── Constants ─────────────────────────────────────────────────────────────────
MOODS = {"😔 Sad": 1, "😟 Anxious": 2, "😐 Okay": 3, "🙂 Good": 4, "😊 Great": 5}
MOOD_COLORS = {1: "#7f3333", 2: "#7f5533", 3: "#5a5a3a", 4: "#3a6644", 5: "#2d7a5a"}

LANGUAGES = {
    "🇺🇸 English": "English",
    "🇮🇳 Hindi": "Hindi",
    "🇮🇳 Telugu": "Telugu",
    "🇮🇳 Tamil": "Tamil",
    "🇪🇸 Spanish": "Spanish",
    "🇫🇷 French": "French",
    "🇸🇦 Arabic": "Arabic",
    "🇨🇳 Mandarin": "Mandarin Chinese",
    "🇧🇷 Portuguese": "Portuguese",
    "🇩🇪 German": "German",
    "🇯🇵 Japanese": "Japanese",
    "🇰🇷 Korean": "Korean",
}

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "don't want to live",
    "self harm", "hurt myself", "no reason to live", "want to die",
]

MEDITATION_TRACKS = [
    {"title": "🌊 Ocean Breathing", "duration": "3.28 min",
     "desc": "Gentle waves to calm your nervous system",
     "file": "audio/ocean-breath.mp3"},
    {"title": "🌧 Soft Rain", "duration": "1.03 min",
     "desc": "Steady rain for deep focus and relaxation",
     "file": "audio/soft-rain.mp3"},
    {"title": "🌲 Forest Sounds", "duration": "3 min",
     "desc": "Birds and breeze for grounding",
     "file": "audio/forest-sound.mp3"}
]

SENIOR_FONT_CSS = """
<style>
.hero-title { font-size: 2.2rem !important; }
.hero-sub { font-size: 1.2rem !important; }
.bubble-user, .bubble-ai { font-size: 1.15rem !important; line-height: 1.9 !important; padding: 1.2rem 1.4rem !important; }
.stButton > button { font-size: 1.1rem !important; padding: 0.8rem 1.8rem !important; }
.stTextInput > div > div > input { font-size: 1.1rem !important; }
</style>
"""


# ── Session state ─────────────────────────────────────────────────────────────
def init():
    defaults = {
        "messages": [],
        "mood_log": [],
        "current_mood": None,
        "mode": "💬 Just Talk",
        "language": "🇺🇸 English",
        "senior_mode": False,
        "session_start": datetime.now().strftime("%I:%M %p"),
        "weekly_moods": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init()


def has_crisis_signal(text: str) -> bool:
    return any(kw in text.lower() for kw in CRISIS_KEYWORDS)


# ── Groq API ──────────────────────────────────────────────────────────────────
def ask_mindease(user_msg: str, mood: str, mode: str, language: str, history: list, senior: bool) -> str:
    client = Groq()

    mode_instructions = {
        "💬 Just Talk":     "Listen with empathy and respond warmly. Validate feelings. Ask gentle follow-up questions.",
        "🧘 Calm Me Down":  "Guide the user through a calming technique — breathing exercise or grounding (5-4-3-2-1 senses). Be soothing and slow-paced.",
        "📓 Journal Prompt":"Offer a thoughtful journaling prompt based on what they shared. Then give them space to reflect.",
        "💡 Coping Tips":   "Suggest 3 practical, evidence-based coping strategies relevant to what the user described. Keep them actionable.",
        "🌙 Sleep Help":    "Help the user wind down. Offer a simple bedtime routine or relaxation technique.",
    }

    senior_note = "Use very simple words. Short sentences. A warm, slow, patient tone — like talking to a dear friend." if senior else ""

    system = f"""You are MindEase, a compassionate AI mental wellness companion for people of all ages.

Current user mood: {mood or 'not specified'}
Conversation mode: {mode}
Respond in: {language}

Your approach: {mode_instructions.get(mode, mode_instructions['💬 Just Talk'])}
{senior_note}

Core values:
- Respond with warmth, patience, and zero judgment
- Never diagnose or replace professional help
- Keep responses conversational — not clinical
- Use simple, human language
- 2-4 paragraphs max, concise and warm
- End with a gentle question or small actionable suggestion
- ALWAYS respond in {language}, even if the user writes in English

You are NOT a therapist. You are a caring companion."""

    api_messages = [{"role": "system", "content": system}]
    for m in history[-6:]:
        api_messages.append({"role": m["role"], "content": m["content"]})
    api_messages.append({"role": "user", "content": user_msg})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=600,
        messages=api_messages,
    )
    return response.choices[0].message.content


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 MindEase")
    st.markdown(f"<small style='color:#6b7280'>Session started {st.session_state.session_start}</small>", unsafe_allow_html=True)

    # Feature badges
    st.markdown("""
    <div style='margin:0.5rem 0'>
        <span class='badge'>🌍 12 Languages</span>
        <span class='badge'>🧘 5 Modes</span>
        <span class='badge'>🎵 Meditation</span>
        <span class='badge'>👴 Senior Mode</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Mode
    st.markdown("### How can I help?")
    st.session_state.mode = st.selectbox(
        "Mode", ["💬 Just Talk", "🧘 Calm Me Down", "📓 Journal Prompt", "💡 Coping Tips", "🌙 Sleep Help"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # 🌍 Language selector
    st.markdown("### 🌍 Language")
    st.session_state.language = st.selectbox(
        "Language", list(LANGUAGES.keys()), label_visibility="collapsed"
    )

    st.markdown("---")

    # 👴 Senior Mode
    st.markdown("### ♿ Accessibility")
    st.session_state.senior_mode = st.toggle("👴 Senior Mode", value=st.session_state.senior_mode,
        help="Larger text, simpler words, slower pace")

    st.markdown("---")

    # 📊 Mood tracker
    if st.session_state.mood_log:
        st.markdown("### 📊 Your Mood Today")
        dots_html = ""
        for _, mood_label, score in st.session_state.mood_log[-10:]:
            color = MOOD_COLORS.get(score, "#555")
            dots_html += f'<span class="mood-dot" style="background:{color}" title="{mood_label}"></span>'
        st.markdown(f'<div style="margin:0.5rem 0">{dots_html}</div>', unsafe_allow_html=True)

        trend = "📈 Improving" if len(st.session_state.mood_log) > 1 and st.session_state.mood_log[-1][2] >= st.session_state.mood_log[0][2] else "💙 Hang in there"
        st.markdown(f"<small style='color:#6b7280'>{trend} · {len(st.session_state.mood_log)} check-ins</small>", unsafe_allow_html=True)

        # Mini mood chart
        if len(st.session_state.mood_log) >= 2:
            scores = [s for _, _, s in st.session_state.mood_log]
            st.line_chart(scores, height=80, use_container_width=True)

    st.markdown("---")

    # 🆘 Crisis resources
    st.markdown("### 🆘 Crisis Resources")
    st.markdown("""
    <div class="resource-card"><b>988 Suicide & Crisis Lifeline</b><br>Call or text <b>988</b> (US, 24/7)</div>
    <div class="resource-card"><b>Crisis Text Line</b><br>Text <b>HOME</b> to <b>741741</b></div>
    <div class="resource-card"><b>International</b><br>findahelpline.com</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# ── Senior mode CSS injection ─────────────────────────────────────────────────
if st.session_state.senior_mode:
    st.markdown(SENIOR_FONT_CSS, unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-title">You don't have to <span>carry this alone.</span></div>
    <div class="hero-sub">MindEase is here — anytime you need to talk, breathe, or just feel heard.</div>
</div>
""", unsafe_allow_html=True)

# Mood check-in
st.markdown("<div style='text-align:center;color:#6b7280;font-size:0.85rem;margin-bottom:0.5rem'>How are you feeling right now?</div>", unsafe_allow_html=True)
mood_cols = st.columns(len(MOODS))
for i, (mood_label, score) in enumerate(MOODS.items()):
    with mood_cols[i]:
        if st.button(mood_label, key=f"mood_{i}", use_container_width=True):
            st.session_state.current_mood = mood_label
            st.session_state.mood_log.append((datetime.now().strftime("%H:%M"), mood_label, score))
            st.rerun()

if st.session_state.current_mood:
    lang_display = LANGUAGES[st.session_state.language]
    st.markdown(f"<div style='text-align:center;color:#7a9e87;font-size:0.85rem;margin:0.3rem 0 1rem'>Feeling <b>{st.session_state.current_mood}</b> · Mode: <b>{st.session_state.mode}</b> · 🌍 <b>{lang_display}</b></div>", unsafe_allow_html=True)

st.markdown("---")

# 🎵 Meditation tab + Chat tab
tab1, tab2 = st.tabs(["💬 Chat", "🎵 Guided Meditation"])

with tab2:
    st.markdown("<div style='padding:1rem 0'><b style='color:#b8a9d9'>🎵 Guided Meditation Audio</b><br><small style='color:#6b7280'>Choose a track to help you relax and ground yourself</small></div>", unsafe_allow_html=True)
    for track in MEDITATION_TRACKS:
        with st.expander(f"{track['title']} · {track['duration']}"):
            st.markdown(f"<small style='color:#6b7280'>{track['desc']}</small>", unsafe_allow_html=True)
            st.audio(track["file"])

with tab1:
    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center;padding:1.5rem 0;color:#6b7280'>
            <div style='font-size:2rem;margin-bottom:0.5rem'>🌿</div>
            <div style='font-size:0.95rem'>This is your safe space. Share what's on your mind.<br>
            No judgment. No pressure. Just support.</div>
        </div>
        """, unsafe_allow_html=True)

        starters = [
            "I'm feeling really overwhelmed",
            "I can't stop worrying about everything",
            "I haven't been sleeping well lately",
            "I just need someone to talk to",
        ]
        st.markdown("<div style='text-align:center;color:#6b7280;font-size:0.8rem;margin:1rem 0 0.5rem'>Start with one of these:</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for i, s in enumerate(starters):
            col = c1 if i % 2 == 0 else c2
            with col:
                if st.button(s, key=f"starter_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": s})
                    with st.spinner("MindEase is here..."):
                        reply = ask_mindease(s, st.session_state.current_mood, st.session_state.mode,
                                             LANGUAGES[st.session_state.language], [], st.session_state.senior_mode)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.rerun()

    # Chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="bubble-user"><div class="bubble-label">You</div>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bubble-ai"><div class="bubble-label">🌿 MindEase</div>{msg["content"]}</div>', unsafe_allow_html=True)

    # Crisis banner
    if st.session_state.messages:
        last_user = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        if has_crisis_signal(last_user):
            st.markdown("""
            <div class="crisis-banner">
                💙 <b>You matter, and help is available right now.</b><br>
                Call or text <b>988</b> · Text HOME to <b>741741</b> · findahelpline.com
            </div>
            """, unsafe_allow_html=True)

    # Input
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Message", placeholder="Share what's on your mind...",
                                   label_visibility="collapsed", key="user_input")
    with col2:
        send = st.button("Send →", use_container_width=True)

    if send and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("MindEase is here..."):
            reply = ask_mindease(
                user_input, st.session_state.current_mood, st.session_state.mode,
                LANGUAGES[st.session_state.language],
                st.session_state.messages[:-1], st.session_state.senior_mode
            )
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# Footer
st.markdown("""
<div style='text-align:center;color:#3a3f52;font-size:0.75rem;margin-top:2rem;padding:1rem 0;border-top:1px solid #2e3447'>
    MindEase is an AI companion, not a licensed therapist. If you're in crisis, please contact a professional. 💙
</div>
""", unsafe_allow_html=True)
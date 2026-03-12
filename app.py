import streamlit as st
import requests
import json
from typing import Optional
import time
import html

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="ContextCore — RAG Document Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    :root {
        --bg: #0A0A0F;
        --surface: #111118;
        --surface2: #16161F;
        --border: #1E1E2E;
        --border-bright: #2A2A3E;
        --accent: #6C63FF;
        --accent2: #FF6B6B;
        --accent3: #4ECDC4;
        --text: #E8E8F0;
        --text-dim: #7A7A9A;
        --text-faint: #3A3A5A;
        --glow: rgba(108, 99, 255, 0.15);
    }

    /* ── Reset & Base ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background: var(--bg) !important;
        color: var(--text) !important;
    }
    .stApp { background: var(--bg) !important; }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] > div { padding: 1.5rem 1.2rem; }

    /* ── Wordmark / Logo ── */
    .wordmark {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.35rem;
        letter-spacing: -0.5px;
        color: var(--text);
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 0.25rem;
    }
    .wordmark-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 10px var(--accent);
        flex-shrink: 0;
    }
    .wordmark-tag {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        font-weight: 400;
        color: var(--text-dim);
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1.8rem;
        padding-left: 16px;
    }

    /* ── Section labels ── */
    .section-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.65rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-faint);
        margin-bottom: 0.75rem;
        margin-top: 1.5rem;
    }

    /* ── Upload zone ── */
    [data-testid="stFileUploader"] {
        background: var(--surface2) !important;
        border: 1.5px dashed var(--border-bright) !important;
        border-radius: 10px !important;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
    }
    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzone"] {
        color: var(--text-dim) !important;
        font-size: 0.82rem !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border-bright) !important;
        color: var(--text-dim) !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.2s !important;
        letter-spacing: 0.01em !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--text) !important;
        background: var(--glow) !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        color: white !important;
        font-weight: 500 !important;
        box-shadow: 0 0 20px rgba(108,99,255,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #7B74FF !important;
        border-color: #7B74FF !important;
        box-shadow: 0 0 30px rgba(108,99,255,0.5) !important;
    }

    /* ── Text input ── */
    .stTextInput > div > div > input {
        background: var(--surface2) !important;
        border: 1px solid var(--border-bright) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 0.65rem 1rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
    }
    .stTextInput > div > div > input::placeholder { color: var(--text-faint) !important; }
    .stTextInput > label { color: var(--text-dim) !important; font-size: 0.8rem !important; }

    /* ── Divider ── */
    hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

    /* ── Status badges ── */
    .status-ok {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 0.75rem; color: var(--accent3);
        font-family: 'DM Sans', sans-serif;
    }
    .status-ok::before {
        content: ''; display: block;
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent3);
        box-shadow: 0 0 6px var(--accent3);
    }
    .status-err {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 0.75rem; color: var(--accent2);
        font-family: 'DM Sans', sans-serif;
    }
    .status-err::before {
        content: ''; display: block;
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent2);
    }

    /* ── Upload success card ── */
    .doc-card {
        background: var(--surface2);
        border: 1px solid var(--border-bright);
        border-left: 3px solid var(--accent3);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        font-size: 0.8rem;
        color: var(--text-dim);
        line-height: 1.6;
        margin-top: 0.75rem;
    }
    .doc-card b { color: var(--text); font-weight: 500; }

    /* ── Page header ── */
    .page-header {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    .page-title {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin-bottom: 0.4rem;
    }
    .page-subtitle {
        font-size: 0.88rem;
        color: var(--text-dim);
        font-weight: 300;
    }

    /* ── Chat area ── */
    .chat-wrap {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        padding: 1.5rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        margin-bottom: 1rem;
    }
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2.5rem 1rem;
        gap: 0.6rem;
        color: var(--text-faint);
        font-size: 0.85rem;
        text-align: center;
    }
    .empty-icon {
        font-size: 2rem;
        margin-bottom: 0.3rem;
        opacity: 0.4;
    }

    /* ── Message bubbles ── */
    .msg-row-user {
        display: flex;
        justify-content: flex-end;
    }
    .msg-row-ai {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 10px;
    }
    .msg-avatar {
        width: 28px; height: 28px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--accent), #9B93FF);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem;
        flex-shrink: 0;
        box-shadow: 0 0 12px rgba(108,99,255,0.3);
    }
    .bubble-user {
        background: var(--accent);
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 0.7rem 1.1rem;
        max-width: 72%;
        font-size: 0.875rem;
        line-height: 1.55;
        box-shadow: 0 4px 20px rgba(108,99,255,0.25);
    }
    .bubble-ai {
        background: var(--surface2);
        border: 1px solid var(--border-bright);
        color: var(--text);
        border-radius: 4px 18px 18px 18px;
        padding: 0.85rem 1.1rem;
        max-width: 72%;
        font-size: 0.875rem;
        line-height: 1.6;
    }
    .msg-meta {
        font-size: 0.68rem;
        color: var(--text-faint);
        margin-top: 0.35rem;
        display: flex; gap: 0.8rem;
    }

    /* ── Stat cards ── */
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.1rem;
    }
    .stat-value {
        font-family: 'Syne', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.5px;
        line-height: 1;
    }
    .stat-label {
        font-size: 0.7rem;
        color: var(--text-dim);
        margin-top: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* ── Sample question pills ── */
    .pill-grid { display: flex; flex-direction: column; gap: 0.5rem; }
    .pill-btn {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-dim) !important;
        border-radius: 8px !important;
        font-size: 0.78rem !important;
        padding: 0.5rem 0.85rem !important;
        text-align: left !important;
        cursor: pointer;
        transition: all 0.18s !important;
        display: block;
    }
    .pill-btn:hover {
        border-color: var(--accent) !important;
        color: var(--text) !important;
        background: var(--glow) !important;
    }

    /* ── Panel heading ── */
    .panel-heading {
        font-family: 'Syne', sans-serif;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text);
        letter-spacing: 0.01em;
        margin-bottom: 1rem;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--accent) !important; }

    /* ── Alerts ── */
    .stAlert { background: var(--surface2) !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# Session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_pdf' not in st.session_state:
    st.session_state.current_pdf = None
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = {'total_questions': 0, 'avg_latency': 0}

# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark"><div class="wordmark-dot"></div> ContextCore</div>', unsafe_allow_html=True)
    st.markdown('<div class="wordmark-tag">RAG Context Intelligence</div>', unsafe_allow_html=True)

    # System status
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if health.status_code == 200 and health.json().get('status') == 'healthy':
            st.markdown('<span class="status-ok">API connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-err">API error</span>', unsafe_allow_html=True)
    except:
        st.markdown('<span class="status-err">API disconnected</span>', unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="section-label">Document</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=['pdf'],
        label_visibility="collapsed",
        help="Upload a PDF to begin analysis"
    )

    if uploaded_file:
        if st.button("Process Document", type="primary", use_container_width=True):
            with st.spinner("Indexing document..."):
                try:
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')}
                    response = requests.post(f"{API_BASE_URL}/api/upload", files=files)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.current_pdf = uploaded_file.name
                        st.session_state.upload_status = {'success': True, 'chunks': result['chunks'], 'filename': result['filename']}
                    else:
                        st.session_state.upload_status = {'success': False, 'message': response.text}
                except Exception as e:
                    st.session_state.upload_status = {'success': False, 'message': str(e)}
            st.rerun()

    if st.session_state.upload_status:
        s = st.session_state.upload_status
        if s['success']:
            st.markdown(f"""
            <div class="doc-card">
                <b>{s['filename']}</b><br>
                {s['chunks']} chunks indexed · ready to query
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="doc-card" style="border-left-color:var(--accent2)">Error: {s["message"]}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-label">Session</div>', unsafe_allow_html=True)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ─── Main ───────────────────────────────────────────────────────────────────
left, right = st.columns([3, 1], gap="large")

with left:
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Context Intelligence</div>
        <div class="page-subtitle">Query your documents with hybrid semantic + keyword retrieval.</div>
    </div>
    """, unsafe_allow_html=True)

    # Chat window — open wrapper
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">◈</div>
            <div><b style="color:#7A7A9A">No conversation yet</b></div>
            <div>Upload a PDF and start asking questions</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
            # Escape content so HTML/angle-brackets in answers never break layout
            safe_content = html.escape(msg['content'])
            if msg['role'] == 'user':
                st.markdown(f"""
                <div class="msg-row-user">
                    <div><div class="bubble-user">{safe_content}</div></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-row-ai">
                    <div class="msg-avatar">◈</div>
                    <div>
                        <div class="bubble-ai">{safe_content}</div>
                        <div class="msg-meta">
                            <span>⚡ {msg.get('latency', 0)} ms</span>
                            <span>📄 {html.escape(msg.get('sources', ''))}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Close wrapper
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle suggested prompt click
    if 'pending_question' not in st.session_state:
        st.session_state.pending_question = None

    pending = st.session_state.pending_question
    if pending:
        st.session_state.pending_question = None  # clear before widget renders

    q_col, btn_col = st.columns([5, 1])
    with q_col:
        question = st.text_input(
            "Question",
            placeholder="Ask a question about your document...",
            label_visibility="collapsed",
            key="question_input",
            value=pending or "",
            disabled=st.session_state.current_pdf is None
        )
    with btn_col:
        ask = st.button("Send →", type="primary", use_container_width=True,
                        disabled=st.session_state.current_pdf is None)

    # Fire if Send clicked OR if a suggested prompt was just selected
    active_question = pending if pending else question
    if (ask and question) or pending:
        st.session_state.chat_history.append({'role': 'user', 'content': active_question})
        with st.spinner("Analyzing..."):
            try:
                t0 = time.time()
                r = requests.post(f"{API_BASE_URL}/api/ask", json={"question": active_question})
                latency = int((time.time() - t0) * 1000)
                if r.status_code == 200:
                    res = r.json()
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': res['answer'],
                        'latency': latency,
                        'sources': ', '.join(res.get('sources', ['doc']))[:40]
                    })
                    n = st.session_state.metrics['total_questions']
                    st.session_state.metrics['avg_latency'] = (st.session_state.metrics['avg_latency'] * n + latency) / (n + 1)
                    st.session_state.metrics['total_questions'] += 1
                else:
                    st.error(r.text)
            except Exception as e:
                st.error(str(e))
        st.rerun()

# ─── Right panel ────────────────────────────────────────────────────────────
with right:
    # Stats
    n_q = st.session_state.metrics['total_questions']
    avg_l = int(st.session_state.metrics['avg_latency'])
    n_conv = len(st.session_state.chat_history) // 2

    st.markdown(f"""
    <div style="margin-top:4.5rem">
        <div class="panel-heading">Session stats</div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{n_q}</div>
                <div class="stat-label">Queries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_l}<span style="font-size:0.9rem;color:var(--text-dim)">ms</span></div>
                <div class="stat-label">Avg latency</div>
            </div>
            <div class="stat-card" style="grid-column: 1 / -1;">
                <div class="stat-value">{n_conv}</div>
                <div class="stat-label">Exchanges</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.current_pdf:
        st.markdown(f"""
        <div class="doc-card" style="margin-bottom:1.5rem">
            <b>Active document</b><br>
            {st.session_state.current_pdf}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="panel-heading">Suggested prompts</div>', unsafe_allow_html=True)

    samples = [
        "What is this document about?",
        "Summarize the key findings",
        "What conclusions are drawn?",
        "Describe the methodology",
        "List the main recommendations",
    ]
    for q in samples:
        if st.button(q, use_container_width=True, key=f"s_{q}"):
            st.session_state["pending_question"] = q
            st.rerun()

    st.markdown("""
    <div style="margin-top:2rem; font-size:0.68rem; color:var(--text-faint); line-height:1.6;">
        ContextCore v1.0<br>FastAPI · LangChain · FAISS · Redis
    </div>
    """, unsafe_allow_html=True)
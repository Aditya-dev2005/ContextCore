import streamlit as st
import requests
import time
import html
import os
import json
import sys

sys.path.insert(0, os.path.dirname(__file__))
from services.history_service import save_session, load_all_sessions, load_session, delete_session

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

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

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background: var(--bg) !important;
        color: var(--text) !important;
    }
    .stApp { background: var(--bg) !important; }

    #MainMenu, footer, .stDeployButton { display: none !important; }
    header { background: transparent !important; }

    .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }

    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] > div { padding: 1.5rem 1.2rem; }

    [data-testid="collapsedControl"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
    }
    [data-testid="stSidebarCollapseButton"] { color: var(--text-dim) !important; }

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

    [data-testid="stFileUploader"] {
        background: var(--surface2) !important;
        border: 1.5px dashed var(--border-bright) !important;
        border-radius: 10px !important;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzone"] {
        color: var(--text-dim) !important;
        font-size: 0.82rem !important;
    }

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

    hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

    .status-ok {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 0.75rem; color: var(--accent3);
        font-family: 'DM Sans', sans-serif;
    }
    .status-ok::before {
        content: ''; display: block; width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent3); box-shadow: 0 0 6px var(--accent3);
    }
    .status-err {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 0.75rem; color: var(--accent2);
        font-family: 'DM Sans', sans-serif;
    }
    .status-err::before {
        content: ''; display: block; width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent2);
    }

    .doc-card {
        background: var(--surface2);
        border: 1px solid var(--border-bright);
        border-left: 3px solid var(--accent3);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        font-size: 0.8rem;
        color: var(--text-dim);
        line-height: 1.6;
        margin-top: 0.5rem;
    }
    .doc-card b { color: var(--text); font-weight: 500; }

    .pdf-list {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        margin-top: 0.5rem;
    }
    .pdf-item {
        display: flex;
        align-items: center;
        gap: 8px;
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        font-size: 0.75rem;
        color: var(--text-dim);
    }
    .pdf-item-dot {
        width: 5px; height: 5px; border-radius: 50%;
        background: var(--accent3); flex-shrink: 0;
    }
    .pdf-item-name {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--text);
    }
    .pdf-count-badge {
        background: var(--accent);
        color: white;
        border-radius: 20px;
        padding: 0.15rem 0.6rem;
        font-size: 0.65rem;
        font-weight: 600;
        font-family: 'Syne', sans-serif;
    }

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
    .empty-icon { font-size: 2rem; margin-bottom: 0.3rem; opacity: 0.4; }

    .msg-row-user { display: flex; justify-content: flex-end; }
    .msg-row-ai {
        display: flex; justify-content: flex-start;
        align-items: flex-start; gap: 10px;
    }
    .msg-avatar {
        width: 28px; height: 28px; border-radius: 50%;
        background: linear-gradient(135deg, var(--accent), #9B93FF);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; flex-shrink: 0;
        box-shadow: 0 0 12px rgba(108,99,255,0.3);
    }
    .bubble-user {
        background: var(--accent); color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 0.7rem 1.1rem; max-width: 72%;
        font-size: 0.875rem; line-height: 1.55;
        box-shadow: 0 4px 20px rgba(108,99,255,0.25);
    }
    .bubble-ai {
        background: var(--surface2);
        border: 1px solid var(--border-bright);
        color: var(--text);
        border-radius: 4px 18px 18px 18px;
        padding: 0.85rem 1.1rem; max-width: 72%;
        font-size: 0.875rem; line-height: 1.6;
        white-space: pre-wrap;
    }
    .msg-meta {
        font-size: 0.68rem; color: var(--text-faint);
        margin-top: 0.35rem; display: flex; gap: 0.8rem;
    }

    .streaming-cursor::after {
        content: '▋';
        animation: blink 0.7s infinite;
        color: var(--accent);
        margin-left: 2px;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }

    /* History cards */
    .hist-card {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .hist-card:hover { border-color: var(--accent); }
    .hist-title {
        font-size: 0.78rem;
        color: var(--text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 0.2rem;
    }
    .hist-meta {
        font-size: 0.65rem;
        color: var(--text-faint);
    }

    .stats-grid {
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 0.75rem; margin-bottom: 1.5rem;
    }
    .stat-card {
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 10px; padding: 1rem 1.1rem;
    }
    .stat-value {
        font-family: 'Syne', sans-serif; font-size: 1.6rem;
        font-weight: 700; color: var(--text);
        letter-spacing: -0.5px; line-height: 1;
    }
    .stat-label {
        font-size: 0.7rem; color: var(--text-dim);
        margin-top: 0.25rem; text-transform: uppercase; letter-spacing: 0.06em;
    }

    .panel-heading {
        font-family: 'Syne', sans-serif; font-size: 0.88rem;
        font-weight: 600; color: var(--text);
        letter-spacing: 0.01em; margin-bottom: 1rem;
    }
    .stSpinner > div { border-top-color: var(--accent) !important; }
    .stAlert { background: var(--surface2) !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_pdfs' not in st.session_state:
    st.session_state.uploaded_pdfs = []
if 'upload_error' not in st.session_state:
    st.session_state.upload_error = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = {'total_questions': 0, 'avg_latency': 0}
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark"><div class="wordmark-dot"></div> ContextCore</div>', unsafe_allow_html=True)
    st.markdown('<div class="wordmark-tag">RAG Document Intelligence</div>', unsafe_allow_html=True)

    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if health.status_code == 200 and health.json().get('status') == 'healthy':
            st.markdown('<span class="status-ok">API connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-err">API error</span>', unsafe_allow_html=True)
    except:
        st.markdown('<span class="status-err">API disconnected</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-label">Documents</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=['pdf'],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Upload one or more PDFs to begin analysis"
    )

    if uploaded_files:
        if st.button("Process Documents", type="primary", use_container_width=True):
            st.session_state.upload_error = None
            already = [p['filename'] for p in st.session_state.uploaded_pdfs]
            to_upload = [f for f in uploaded_files if f.name not in already]

            if not to_upload:
                st.session_state.upload_error = "All selected files are already indexed."
            else:
                progress = st.progress(0, text="Indexing documents...")
                for i, pdf_file in enumerate(to_upload):
                    progress.progress(
                        int((i / len(to_upload)) * 100),
                        text=f"Indexing {pdf_file.name}..."
                    )
                    try:
                        files = {'file': (pdf_file.name, pdf_file.getvalue(), 'application/pdf')}
                        response = requests.post(f"{API_BASE_URL}/api/upload", files=files)
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.uploaded_pdfs.append({
                                'filename': result['filename'],
                                'chunks': result['chunks']
                            })
                        else:
                            st.session_state.upload_error = f"Failed: {pdf_file.name}"
                    except Exception as e:
                        st.session_state.upload_error = str(e)
                progress.progress(100, text="Done!")
                time.sleep(0.5)
            st.rerun()

    if st.session_state.upload_error:
        st.markdown(
            f'<div class="doc-card" style="border-left-color:var(--accent2)">{st.session_state.upload_error}</div>',
            unsafe_allow_html=True
        )

    if st.session_state.uploaded_pdfs:
        total_chunks = sum(p['chunks'] for p in st.session_state.uploaded_pdfs)
        n = len(st.session_state.uploaded_pdfs)

        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-top:0.75rem; margin-bottom:0.4rem;">
            <span style="font-size:0.7rem; color:var(--text-faint); text-transform:uppercase; letter-spacing:0.1em;">Indexed</span>
            <span class="pdf-count-badge">{n} PDF{'s' if n > 1 else ''}</span>
        </div>
        <div class="pdf-list">
        """, unsafe_allow_html=True)

        for pdf in st.session_state.uploaded_pdfs:
            safe_name = html.escape(pdf['filename'])
            st.markdown(f"""
            <div class="pdf-item">
                <div class="pdf-item-dot"></div>
                <div class="pdf-item-name">{safe_name}</div>
                <span style="font-size:0.65rem; color:var(--text-faint);">{pdf['chunks']}c</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        </div>
        <div style="font-size:0.68rem; color:var(--text-faint); margin-top:0.4rem; padding-left:2px;">
            {total_chunks} total chunks indexed
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-label">Session</div>', unsafe_allow_html=True)

    col_clear_chat, col_clear_docs = st.columns(2)
    with col_clear_chat:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    with col_clear_docs:
        if st.button("Clear docs", use_container_width=True):
            st.session_state.uploaded_pdfs = []
            st.session_state.upload_error = None
            try:
                requests.post(f"{API_BASE_URL}/api/clear", timeout=3)
            except:
                pass
            st.rerun()

    # ── NEW: Save & History section ───────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-label">History</div>', unsafe_allow_html=True)

    if st.session_state.chat_history:
        if st.button("💾 Save Session", use_container_width=True):
            sid = save_session(st.session_state.chat_history, st.session_state.uploaded_pdfs)
            st.success(f"Saved! ID: {sid}")

    sessions = load_all_sessions()
    if not sessions:
        st.markdown('<div style="font-size:0.75rem; color:var(--text-faint); padding: 0.5rem 0;">No saved sessions yet.</div>', unsafe_allow_html=True)
    else:
        for s in sessions[:8]:  # Show last 8
            safe_title = html.escape(s["title"])
            pdfs_str = ", ".join(s.get("pdfs", []))[:40] or "No PDFs"
            msg_count = len([m for m in s["messages"] if m["role"] == "user"])

            col_load, col_del = st.columns([4, 1])
            with col_load:
                st.markdown(f"""
                <div class="hist-card">
                    <div class="hist-title">💬 {safe_title}</div>
                    <div class="hist-meta">{s['timestamp']} · {msg_count}Q · {html.escape(pdfs_str)}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Load", key=f"load_{s['id']}", use_container_width=True):
                    loaded = load_session(s["id"])
                    if loaded:
                        st.session_state.chat_history = loaded["messages"]
                        st.session_state.uploaded_pdfs = [
                            {"filename": f, "chunks": 0} for f in loaded.get("pdfs", [])
                        ]
                        st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{s['id']}"):
                    delete_session(s["id"])
                    st.rerun()

# ── Helper: streaming request ─────────────────────────────────────────────────
def stream_response(question: str, history: list):
    payload = {"question": question, "conversation_history": history}
    with requests.post(
        f"{API_BASE_URL}/api/stream",
        json=payload,
        stream=True,
        timeout=60
    ) as resp:
        for line in resp.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data = json.loads(decoded[6:])
                    yield data

# ── Main ──────────────────────────────────────────────────────────────────────
left, right = st.columns([3, 1], gap="large")
docs_ready = len(st.session_state.uploaded_pdfs) > 0

with left:
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Context Intelligence</div>
        <div class="page-subtitle">Query across multiple documents with hybrid semantic + keyword retrieval.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">◈</div>
            <div><b style="color:#7A7A9A">No conversation yet</b></div>
            <div>Upload PDFs and start asking questions</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
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

    st.markdown('</div>', unsafe_allow_html=True)

    pending = st.session_state.pending_question
    if pending:
        st.session_state.pending_question = None

    q_col, btn_col = st.columns([5, 1])
    with q_col:
        question = st.text_input(
            "Question",
            placeholder="Ask across all your documents..." if docs_ready else "Upload a PDF to begin...",
            label_visibility="collapsed",
            key="question_input",
            value=pending or "",
            disabled=not docs_ready
        )
    with btn_col:
        ask = st.button("Send →", type="primary", use_container_width=True, disabled=not docs_ready)

    active_question = pending if pending else question

    if (ask and question) or pending:
        st.session_state.chat_history.append({'role': 'user', 'content': active_question})

        history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.chat_history[:-1]
        ]

        stream_placeholder = st.empty()
        t0 = time.time()
        full_answer = ""
        sources = []

        try:
            for chunk in stream_response(active_question, history):
                if "error" in chunk:
                    st.error(chunk["error"])
                    break
                if "token" in chunk:
                    full_answer += chunk["token"]
                    safe_so_far = html.escape(full_answer)
                    stream_placeholder.markdown(f"""
                    <div class="msg-row-ai">
                        <div class="msg-avatar">◈</div>
                        <div>
                            <div class="bubble-ai streaming-cursor">{safe_so_far}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                if chunk.get("done"):
                    sources = chunk.get("sources", [])
                    break
        except Exception as e:
            st.error(str(e))

        latency = int((time.time() - t0) * 1000)

        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': full_answer,
            'latency': latency,
            'sources': ', '.join(sources)[:50] if sources else ''
        })

        n = st.session_state.metrics['total_questions']
        st.session_state.metrics['avg_latency'] = (
            st.session_state.metrics['avg_latency'] * n + latency
        ) / (n + 1)
        st.session_state.metrics['total_questions'] += 1

        st.rerun()

# ── Right panel ───────────────────────────────────────────────────────────────
with right:
    n_q = st.session_state.metrics['total_questions']
    avg_l = int(st.session_state.metrics['avg_latency'])
    n_docs = len(st.session_state.uploaded_pdfs)

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
                <div class="stat-value">{n_docs}</div>
                <div class="stat-label">Documents loaded</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="panel-heading">Suggested prompts</div>', unsafe_allow_html=True)

    samples = [
        "What is this document about?",
        "Summarize the key findings",
        "What conclusions are drawn?",
        "Compare the documents",
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
"""
Rosee — Instagram Automation Frontend UI/UX Premium
Streamlit app: 4 pages, dashboard, analytics, approval flow
"""

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone, timedelta, date, time
from collections import Counter

API_BASE = "http://localhost:8000"
BRASIL_TZ = timezone(timedelta(hours=-3))

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="Rosee | Automação Instagram",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS TECH MODERN ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Animações globais ── */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(12px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideUp {
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(139,92,246,0.15); }
        50% { box-shadow: 0 0 40px rgba(139,92,246,0.3); }
    }
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    @keyframes border-glow {
        0%, 100% { border-color: rgba(139,92,246,0.2); }
        50% { border-color: rgba(139,92,246,0.5); }
    }
    @keyframes spin-slow {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    * { font-family: 'Inter', -apple-system, sans-serif; }

    /* ── Background futurista ── */
    html, body, [data-testid="stAppViewContainer"] {
        background: #0a0a0f !important;
        color: #e4e4ed !important;
    }
    .stApp { background: #0a0a0f !important; }

    /* ── Sidebar tech ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15,15,25,0.98) 0%, rgba(20,10,40,0.98) 100%) !important;
        border-right: 1px solid rgba(139,92,246,0.12) !important;
        backdrop-filter: blur(20px);
        padding: 0 !important;
    }
    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(139,92,246,0.4), transparent);
    }
    section[data-testid="stSidebar"] .stApp { background: transparent !important; }

    /* Logo/marca na sidebar */
    section[data-testid="stSidebar"] .stButton button {
        background: transparent !important; border: none !important;
        color: rgba(255,255,255,0.6) !important; text-align: left !important;
        padding: 12px 20px !important; font-size: 14px !important;
        font-weight: 500 !important; border-radius: 10px !important;
        margin: 2px 8px !important; transition: all 0.3s cubic-bezier(0.4,0,0.2,1) !important;
        position: relative; overflow: hidden;
    }
    section[data-testid="stSidebar"] .stButton button::before {
        content: '';
        position: absolute; left: 0; top: 50%; width: 3px; height: 0;
        background: linear-gradient(180deg, #8B5CF6, #EC4899);
        border-radius: 0 2px 2px 0;
        transition: height 0.3s cubic-bezier(0.4,0,0.2,1);
        transform: translateY(-50%);
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(139,92,246,0.08) !important;
        color: #fff !important;
        transform: translateX(4px);
    }
    section[data-testid="stSidebar"] .stButton button:hover::before {
        height: 60%;
    }
    section[data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(236,72,153,0.2)) !important;
        color: #fff !important; font-weight: 600 !important;
        border: 1px solid rgba(139,92,246,0.2) !important;
    }
    section[data-testid="stSidebar"] .stButton button[kind="primary"]::before { display: none; }

    /* ── Cards glassmorphism ── */
    .card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px; padding: 24px;
        transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
        color: #d0d0e0;
        animation: fadeIn 0.5s ease both;
        position: relative; overflow: hidden;
    }
    .card::before {
        content: '';
        position: absolute; top: 0; left: -100%; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, rgba(139,92,246,0.6), transparent);
        transition: left 0.6s cubic-bezier(0.4,0,0.2,1);
    }
    .card:hover::before { left: 100%; }
    .card:hover {
        border-color: rgba(139,92,246,0.2);
        box-shadow: 0 8px 40px rgba(0,0,0,0.3), 0 0 30px rgba(139,92,246,0.05);
        transform: translateY(-4px);
    }
    .card h4 { color: #f0f0ff !important; }
    .card:nth-child(2) { animation-delay: 0.1s; }
    .card:nth-child(3) { animation-delay: 0.2s; }
    .card:nth-child(4) { animation-delay: 0.3s; }
    .card:nth-child(5) { animation-delay: 0.4s; }

    /* ── KPI cards ── */
    .kpi-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; padding: 20px 24px;
        transition: all 0.3s ease;
        animation: slideUp 0.5s ease both;
    }
    .kpi-card:hover {
        border-color: rgba(139,92,246,0.3);
        box-shadow: 0 0 30px rgba(139,92,246,0.08);
        transform: translateY(-2px);
    }
    .kpi-value {
        font-size: 32px; font-weight: 800;
        background: linear-gradient(135deg, #8B5CF6, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 12px; color: rgba(255,255,255,0.4);
        font-weight: 500; margin-top: 4px;
        text-transform: uppercase; letter-spacing: 1px;
    }

    /* ── Titles ── */
    .page-title {
        font-size: 28px; font-weight: 800;
        background: linear-gradient(135deg, #f0f0ff, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
        animation: fadeIn 0.4s ease;
    }
    .page-subtitle {
        font-size: 14px; color: rgba(255,255,255,0.4);
        font-weight: 400; margin-bottom: 24px;
        animation: fadeIn 0.4s ease 0.1s both;
    }

    /* ── Gradient divider ── */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(139,92,246,0.4), rgba(236,72,153,0.2), transparent);
        margin: 16px 0 24px 0;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.03);
        border-radius: 12px; padding: 4px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 20px; font-weight: 500;
        color: rgba(255,255,255,0.5);
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(236,72,153,0.2)) !important;
        color: #fff !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.1);
    }

    /* ── Inputs tech ── */
    .stTextArea textarea, .stTextInput input, .stSelectbox div {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        color: #e4e4ed !important;
        transition: all 0.3s ease !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #8B5CF6 !important;
        box-shadow: 0 0 0 3px rgba(139,92,246,0.1), 0 0 20px rgba(139,92,246,0.05) !important;
    }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: rgba(255,255,255,0.2) !important;
    }

    /* ── Status badges glow ── */
    .status-badge {
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .status-rascunho { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.5); }
    .status-revisao { background: rgba(251,146,60,0.12); color: #fb923c; box-shadow: 0 0 12px rgba(251,146,60,0.1); }
    .status-agendado { background: rgba(96,165,250,0.12); color: #60a5fa; box-shadow: 0 0 12px rgba(96,165,250,0.1); }
    .status-publicado { background: rgba(74,222,128,0.12); color: #4ade80; box-shadow: 0 0 12px rgba(74,222,128,0.1); }
    .status-falha { background: rgba(248,113,113,0.12); color: #f87171; box-shadow: 0 0 12px rgba(248,113,113,0.1); }

    /* ── Buttons com glow ── */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1) !important;
        position: relative; overflow: hidden;
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #8B5CF6, #EC4899) !important;
        background-size: 200% 200% !important;
        animation: gradient-shift 4s ease infinite !important;
        color: #fff !important;
        border: none !important;
    }
    .stButton button[kind="primary"]:hover {
        box-shadow: 0 4px 24px rgba(139,92,246,0.4) !important;
        transform: translateY(-2px);
    }
    .stButton button[kind="primary"]:active {
        transform: translateY(0px);
    }
    .stButton button[kind="secondary"] {
        background: rgba(255,255,255,0.04) !important;
        color: #a78bfa !important;
        border: 1px solid rgba(139,92,246,0.2) !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: rgba(139,92,246,0.5) !important;
        background: rgba(139,92,246,0.08) !important;
        box-shadow: 0 0 20px rgba(139,92,246,0.05);
    }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px; padding: 16px;
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(139,92,246,0.2);
    }
    div[data-testid="stMetric"] label { color: rgba(255,255,255,0.4) !important; }
    div[data-testid="stMetric"] div { color: #f0f0ff !important; }

    /* ── General text ── */
    p, li, .stMarkdown { color: rgba(255,255,255,0.7) !important; }
    h1, h2, h3 { color: #f0f0ff !important; }
    h4, h5, h6 { color: #e0e0f0 !important; }
    .stAlert {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-left: 3px solid #8B5CF6 !important;
        color: rgba(255,255,255,0.7) !important;
        border-radius: 10px !important;
    }

    /* ── Radio & checkbox ── */
    .stRadio label { color: rgba(255,255,255,0.7) !important; }
    .stCheckbox label { color: rgba(255,255,255,0.7) !important; }
    .st-bb { color: rgba(255,255,255,0.7) !important; }
    .st-cb { color: rgba(255,255,255,0.7) !important; }

    /* ── DataFrames ── */
    .stDataFrame { color: rgba(255,255,255,0.8) !important; }

    /* ── Select slider ── */
    .stSlider label { color: rgba(255,255,255,0.7) !important; }

    /* ── Progress bar ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #8B5CF6, #EC4899) !important;
    }

    /* ── Spinner ── */
    .stSpinner {
        border-color: rgba(139,92,246,0.2) !important;
        border-top-color: #8B5CF6 !important;
    }

    /* ── Expander ── */
    .stExpander {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
    }

    /* ── Chat ── */
    .stChatMessage {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
    }

    /* ── Mobile ── */
    @media (max-width: 768px) {
        .page-title { font-size: 22px !important; }
        .kpi-value { font-size: 24px !important; }
        .card { padding: 16px !important; border-radius: 14px !important; }
        .kpi-card { padding: 14px 16px !important; }
        section[data-testid="stSidebar"] { min-width: 200px !important; max-width: 240px !important; }
        section[data-testid="stSidebar"] .stButton button { padding: 10px 14px !important; font-size: 13px !important; }
        div[data-testid="column"] { min-width: auto !important; }
    }
    @media (max-width: 480px) {
        section[data-testid="stSidebar"] { min-width: 180px !important; max-width: 220px !important; }
        .st-emotion-cache-1lcbmhc { padding: 1rem 0.5rem !important; }
    }

    /* ── Scrollbar custom ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
    ::-webkit-scrollbar-thumb {
        background: rgba(139,92,246,0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.5); }

    /* ── Linha sutil decorativa no topo ── */
    [data-testid="stHeader"] {
        background: rgba(15,15,25,0.8);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(139,92,246,0.08);
    }
</style>
""", unsafe_allow_html=True)

# Show local IP for mobile access
import socket
_HOST_IP = socket.gethostbyname(socket.gethostname())

# ── SESSION STATE ──
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "current_post" not in st.session_state:
    st.session_state.current_post = None
if "last_action" not in st.session_state:
    st.session_state.last_action = None

# ── API HELPERS ──
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=60)
        return r.json() if r.status_code == 200 else {"error": r.text}
    except requests.ConnectionError:
        return {"error": "Backend offline"}

def api_post(path, data=None, files=None):
    use_json = files is None
    try:
        timeout = 600 if files else 30  # uploads take long on slow PCs
        if files:
            r = requests.post(f"{API_BASE}{path}", data=data, files=files, timeout=timeout)
        elif use_json:
            r = requests.post(f"{API_BASE}{path}", json=data, timeout=timeout)
        else:
            r = requests.post(f"{API_BASE}{path}", data=data, timeout=timeout)
        if r.status_code in (200, 201):
            return r.json()
        try:
            d = r.json()
            return {"error": d.get("detail", r.text) if isinstance(d, dict) else d}
        except Exception:
            return {"error": r.text}
    except requests.ConnectionError:
        return {"error": "Backend offline"}

def api_put(path, data=None):
    try:
        r = requests.put(f"{API_BASE}{path}", json=data, timeout=60)
        return r.json() if r.status_code == 200 else {"error": r.text}
    except requests.ConnectionError:
        return {"error": "Backend offline"}

def api_delete(path):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=15)
        return r.json() if r.status_code == 200 else {"error": r.text}
    except requests.ConnectionError:
        return {"error": "Backend offline"}

def status_badge(status):
    cls = {
        "rascunho": "status-rascunho",
        "revisao": "status-revisao",
        "agendado": "status-agendado",
        "publicado": "status-publicado",
        "falha_publicacao": "status-falha",
    }.get(status, "status-rascunho")
    label = {
        "rascunho": "Rascunho",
        "revisao": "Revisão",
        "agendado": "Agendado",
        "publicado": "Publicado",
        "falha_publicacao": "Falha",
    }.get(status, status)
    return f'<span class="status-badge {cls}">{label}</span>'

# ──────────────────────────────────────────────
# PAGE: SIDEBAR
# ──────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 24px 20px 12px 20px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 4px;">🌸</div>
            <div style="font-size: 22px; font-weight: 800; color: #fff; letter-spacing: -0.5px;">
                Rosee
            </div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.5); letter-spacing: 1px;
                        text-transform: uppercase; margin-bottom: 8px;">
                Instagram Automation
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        pages = [
            ("📊", "Dashboard", "dashboard"),
            ("📤", "Nova Postagem", "upload"),
            ("📂", "Processar Lote", "batch"),
            ("✅", "Revisão", "review"),
            ("📅", "Agenda", "schedule"),
            ("📈", "Analytics", "analytics"),
            ("⚙️", "Configurações", "settings"),
        ]

        for icon, label, key in pages:
            btn_type = "primary" if st.session_state.page == key else "secondary"
            if st.button(f"{icon}  {label}", key=f"nav_{key}", type=btn_type, use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.divider()
        health = api_get("/api/health")
        status_icon = "🟢" if health.get("status") == "ok" else "🔴"
        st.markdown(f"""
        <div style="padding: 4px 20px; font-size: 12px; color: rgba(255,255,255,0.5);">
            {status_icon}  {health.get("status", "offline")} · v1.0.0
        </div>
        <div style="padding: 0 20px 8px; font-size: 10px; color: rgba(255,255,255,0.3);">
            {_HOST_IP}:8501
        </div>
        """, unsafe_allow_html=True)

        pending = api_get("/api/posts/", params={"status": "revisao"})
        pc = len(pending.get("posts", []))
        if pc > 0:
            st.markdown(f"""
            <div style="padding: 8px 16px; margin: 8px 12px; background: rgba(255,107,107,0.15);
                        border-radius: 12px; border: 1px solid rgba(255,107,107,0.2);
                        font-size: 13px; color: #ff6b6b; text-align: center;">
                📋 {pc} post(s) aguardam revisão!
            </div>
            """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PAGE: DASHBOARD
# ──────────────────────────────────────────────
def render_dashboard():
    st.markdown('<div class="page-title">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Visão geral da sua estratégia editorial</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Fetch real data
    all_posts = api_get("/api/posts/", params={"limit": 200}).get("posts", [])

    counts = Counter(p.get("status", "") for p in all_posts)
    categories = Counter(
        p.get("final_category") or p.get("ai_category", "look") for p in all_posts
    )

    total = len(all_posts)
    published = counts.get("publicado", 0)
    scheduled = counts.get("agendado", 0)
    draft = counts.get("revisao", 0) + counts.get("rascunho", 0)
    failed = counts.get("falha_publicacao", 0)

    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">📸</div>
            <div class="kpi-value">{total}</div>
            <div class="kpi-label">Total de Posts</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">✅</div>
            <div class="kpi-value">{published}</div>
            <div class="kpi-label">Publicados</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">📅</div>
            <div class="kpi-value">{scheduled}</div>
            <div class="kpi-label">Agendados</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">✏️</div>
            <div class="kpi-value">{draft}</div>
            <div class="kpi-label">Em Revisão</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown('<div class="card"><h4 style="margin:0 0 16px 0; font-weight:600;">📊 Mix Editorial</h4>', unsafe_allow_html=True)
        # Pie chart: editorial mix
        target = {"look": 40, "dica": 20, "lifestyle": 15, "social": 15, "novidade": 10}
        cat_labels = {
            "look": "Looks da Loja",
            "dica": "Dicas de Moda",
            "lifestyle": "Lifestyle",
            "social": "Prova Social",
            "novidade": "Novidades",
        }
        cat_real = {k: categories.get(k, 0) for k in target}
        total_cat = sum(cat_real.values())
        df_pie = [{"Categoria": cat_labels.get(k, k), "Posts": v} for k, v in cat_real.items() if v > 0]

        if df_pie and total_cat > 0:
            fig = px.pie(
                df_pie, names="Categoria", values="Posts",
                color_discrete_sequence=["#e91e63", "#9c27b0", "#2196f3", "#4caf50", "#ff9800"],
                hole=0.5,
            )
            fig.update_layout(
                height=280, margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True, legend=dict(orientation="h", y=-0.1),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div style="text-align:center;padding:40px 0;color:#666688;">Nenhum dado ainda</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chart2:
        st.markdown('<div class="card"><h4 style="margin:0 0 16px 0; font-weight:600;">📈 Publicações (7 dias)</h4>', unsafe_allow_html=True)
        if all_posts:
            days_map = {}
            for p in all_posts:
                s = p.get("scheduled_at") or p.get("published_at") or p.get("created_at", "")
                try:
                    d = datetime.fromisoformat(s).strftime("%a")
                    days_map[d] = days_map.get(d, 0) + 1
                except Exception:
                    pass
            day_labels = [(datetime.now(BRASIL_TZ) - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
            vals = [days_map.get(d, 0) for d in day_labels]
            fig2 = px.bar(x=day_labels, y=vals, labels={"x": "", "y": "Posts"}, color_discrete_sequence=["#e91e63"])
            fig2.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#f0f0f0"))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown('<div style="text-align:center;padding:40px 0;color:#666688;">Nenhum dado ainda</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent activity
    st.markdown('<div class="card"><h4 style="margin:0 0 16px 0; font-weight:600;">🕐 Atividade Recente</h4>', unsafe_allow_html=True)

    recent = [p for p in all_posts if p.get("status") in ("publicado", "agendado", "revisao")][:6]

    if recent:
        for p in recent:
            cap = p.get("final_caption") or p.get("ai_caption", "") or "Sem legenda"
            cat = p.get("final_category") or p.get("ai_category", "-")
            s = p.get("scheduled_at", "") or p.get("published_at", "") or p.get("created_at", "")
            try:
                dt = datetime.fromisoformat(s).strftime("%d/%m/%Y %H:%M")
            except Exception:
                dt = s[:10] if s else "-"
            cols = st.columns([2, 1, 1, 1])
            with cols[0]:
                st.markdown(f"**{cap[:70]}...**" if len(cap) > 70 else f"**{cap}**")
            with cols[1]:
                st.markdown(f"`{cat}`")
            with cols[2]:
                st.markdown(status_badge(p["status"]), unsafe_allow_html=True)
            with cols[3]:
                st.caption(dt)
            st.markdown("<hr style='margin:6px 0; opacity:0.2;'>", unsafe_allow_html=True)
    else:
        st.caption("Nenhuma atividade ainda. Crie sua primeira postagem!")

    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PAGE: UPLOAD
# ──────────────────────────────────────────────
def render_upload():
    st.markdown('<div class="page-title">📤 Criar Postagem</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    mode = st.radio(
        "Modo de envio",
        ["💬 Conversa com IA", "📝 Clássico"],
        horizontal=True,
        label_visibility="collapsed",
        key="upload_mode_radio",
    )

    if mode == "💬 Conversa com IA":
        _render_upload_chat()
    else:
        _render_upload_classic()


def _render_upload_classic():
    """Classic form-based upload (non-chat)."""
    st.markdown("Envie as fotos e preencha os dados manualmente.", unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
        label_visibility="collapsed",
        key="classic_uploader",
    )

    if not uploaded_files:
        st.markdown("""
        <div style="border: 2px dashed rgba(255,255,255,0.15); border-radius: 20px; padding: 60px 20px;
                    text-align: center; background: rgba(255,255,255,0.03);">
            <div style="font-size: 56px; margin-bottom: 12px;">📸</div>
            <div style="font-size: 16px; color: #8888aa; font-weight: 500;">
                Selecione 1 a 15 fotos
            </div>
            <div style="font-size: 13px; color: #666688; margin-top: 4px;">
                Depois é só preencher os dados de cada uma
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    if len(uploaded_files) > 15:
        st.error("Máximo 15 fotos por vez.")
        return

    st.markdown(f'<div style="color:#8888aa;font-size:13px;margin-bottom:8px;">📸 {len(uploaded_files)} foto(s)</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(uploaded_files), 6))
    for i, f in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(f, width=100)

    st.markdown("---")

    # Per-photo fields
    form_data_list = []
    for idx, f in enumerate(uploaded_files):
        with st.container(border=True):
            st.markdown(f'<div style="font-size:13px;color:#8888aa;"><b>📷 Foto {idx+1}</b></div>', unsafe_allow_html=True)
            col_i, col_f = st.columns([1, 3])
            with col_i:
                st.image(f, width=80)
            with col_f:
                inp = st.text_area(
                    "Descrição",
                    key=f"classic_u_{idx}",
                    placeholder="Ex: Vestido floral, tecido leve...",
                    height=60,
                    label_visibility="collapsed",
                )
                c_p, c_s = st.columns(2)
                with c_p:
                    pr = st.number_input("💰 Preço (R$)", min_value=0.0, step=0.5, format="%.2f", key=f"classic_p_{idx}")
                with c_s:
                    sz = st.text_input("📏 Tamanhos", key=f"classic_s_{idx}", placeholder="P, M, G")
        form_data_list.append({"user_input": inp or "", "price": pr if pr and pr > 0 else None, "sizes": sz or ""})

    # Template selector
    st.markdown("---")
    templates_resp = api_get("/api/templates/")
    templates = templates_resp.get("templates", [])
    tpl_opts = {t["id"]: t["name"] for t in templates if t["type"] == "image"}
    selected_template = st.selectbox(
        "🎨 Template",
        options=list(tpl_opts.keys()),
        format_func=lambda x: tpl_opts.get(x, x),
        key="classic_template",
    )

    if st.button("🚀 ENVIAR PARA IA", type="primary", use_container_width=True):
        progress = st.progress(0, text="Enviando para a IA...")
        created = []
        for idx, f in enumerate(uploaded_files):
            progress.progress((idx + 1) / len(uploaded_files), text=f"📝 Processando foto {idx+1}/{len(uploaded_files)}...")
            data = form_data_list[idx]
            payload = {
                "user_input": data["user_input"],
                "sizes": data["sizes"],
                "template_id": selected_template or "tpl_feed_01",
            }
            if data["price"] is not None:
                payload["price"] = str(data["price"])
            files = {"file": (f.name, f.getvalue(), f.type)}
            r = api_post("/api/posts/upload", data=payload, files=files)
            if "error" not in r:
                created.append(r)
            else:
                st.error(f"Erro foto {idx+1}: {r['error']}")
        progress.empty()

        if created:
            st.success(f"✅ {len(created)} post(s) criados com sucesso!")
            for idx, p in enumerate(created):
                with st.container(border=True):
                    st.markdown(f"**📷 Post {idx+1}** — `{p.get('ai_category', 'look')}`")
                    st.markdown(f"📝 {p.get('ai_caption', '')[:200]}")
                    cta = p.get("ai_cta", "")
                    if cta:
                        st.markdown(f"🎯 CTA: {cta}")
                    ht = p.get("ai_hashtags", "")
                    if ht:
                        st.markdown(f"🏷️ {ht}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Ir para Revisão", use_container_width=True):
                    st.session_state.current_post = created[0]
                    st.session_state.page = "review"
                    st.rerun()
            with col2:
                if st.button("📅 Ver Agenda", use_container_width=True):
                    st.session_state.page = "schedule"
                    st.rerun()


def _render_upload_chat():
    uploaded_files = st.file_uploader(
        "", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
        label_visibility="collapsed",
        key="chat_uploader",
    )

    if not uploaded_files:
        st.markdown("""
        <div style="border: 2px dashed rgba(255,255,255,0.15); border-radius: 20px; padding: 60px 20px;
                    text-align: center; background: rgba(255,255,255,0.03);">
            <div style="font-size: 56px; margin-bottom: 12px;">📸</div>
            <div style="font-size: 16px; color: #8888aa; font-weight: 500;">
                Selecione 1 a 15 fotos
            </div>
            <div style="font-size: 13px; color: #666688; margin-top: 4px;">
                Depois é só conversar com a IA sobre cada uma!
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.pop("chat_flow", None)
        st.session_state.pop("chat_msgs", None)
        st.session_state.pop("chat_photos", None)
        st.session_state.pop("chat_photos_data", None)
        return

    if len(uploaded_files) > 15:
        st.error("Máximo 15 fotos por vez.")
        return

    upload_names = [f.name for f in uploaded_files]
    if st.session_state.get("chat_photos") != upload_names:
        st.session_state.chat_photos = upload_names
        st.session_state.chat_msgs = []
        st.session_state.chat_data = {}
        st.session_state.chat_flow = "greeting"
        st.session_state.chat_ai_analyzed = False
        st.session_state.chat_created_posts = None
        st.session_state.chat_photos_data = None
        st.session_state.pop("chat_pending_cmd", None)
        st.rerun()

    # Show photo thumbnails
    st.markdown(f'<div style="color:#8888aa;font-size:13px;margin-bottom:8px;">📸 {len(uploaded_files)} foto(s)</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(uploaded_files), 6))
    for i, f in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(f, width=100)

    # Greeting
    if st.session_state.chat_flow == "greeting":
        st.markdown("---")
        st.markdown("💬 **Rosee IA:** Pronta! Posso analisar as fotos e conversar com você sobre cada uma.")
        if st.button("🚀 Iniciar Conversa com a IA", type="primary", use_container_width=True):
            st.session_state.chat_flow = "analyzing"
            st.session_state.chat_msgs = []
            st.rerun()

    # Chat flow
    if st.session_state.chat_flow in ("analyzing", "asking", "done"):
        st.markdown("---")
        st.markdown("### 💬 Conversa com a IA")

        # Analyze photos once
        if st.session_state.chat_flow == "analyzing" and not st.session_state.chat_ai_analyzed:
            st.session_state.chat_ai_analyzed = True
            progress = st.progress(0, text="🧠 IA analisando as fotos...")
            photo_descriptions = []
            msgs = []
            msgs.append({"role": "ai", "content": f"📸 **{len(uploaded_files)} foto(s)** selecionadas! Vou analisar cada uma..."})
            for idx in range(len(uploaded_files)):
                st.session_state.chat_data[str(idx)] = {"price": None, "sizes": "", "user_input": ""}
                desc = f"Foto {idx+1}"
                photo_descriptions.append(desc)
                msgs.append({"role": "ai", "content": f"📷 **Foto {idx+1}:** {desc}"})
                progress.progress((idx + 1) / len(uploaded_files), text=f"🧠 Analisando foto {idx+1}/{len(uploaded_files)}...")
            msgs.append({"role": "ai", "content": "Ótimo! Diga o que quer fazer com cada foto.\n\n**Exemplos:**\n- *pública a foto 1 sexta às 14h com preço 89,90*\n- *foto 2 com tamanhos P,M,G*\n- *todas as fotos para amanhã às 10h*\n- *edita a legenda da foto 3*"})
            progress.empty()
            st.session_state.chat_photos_data = photo_descriptions  # Placeholder; real descriptions would need AI analysis here
            st.session_state.chat_msgs = msgs
            st.session_state.chat_flow = "asking"
            st.rerun()

        # Show chat messages
        for msg in st.session_state.chat_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Pending command confirmation
        if st.session_state.get("chat_pending_cmd"):
            pending = st.session_state.chat_pending_cmd
            with st.container(border=True):
                st.markdown(f"**{pending['preview']}**")

                # Show details
                interp = pending["interpretation"]
                details = []
                if interp.get("target_str"):
                    details.append(f"📷 Alvo: {interp['target_str']}")
                if interp.get("datetime"):
                    details.append(f"📅 Data: {interp['datetime']}")
                if interp.get("price"):
                    details.append(f"💰 Preço: R$ {interp['price']:.2f}")
                if interp.get("sizes"):
                    details.append(f"📏 Tamanhos: {interp['sizes']}")
                for d in details:
                    st.caption(d)

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("✅ Confirmar", type="primary", use_container_width=True, key="chat_confirm_btn"):
                        _execute_chat_command(uploaded_files)
                with col_c2:
                    if st.button("❌ Cancelar", use_container_width=True, key="chat_cancel_btn"):
                        st.session_state.chat_pending_cmd = None
                        st.session_state.chat_msgs.append({"role": "ai", "content": "Comando cancelado. Diga outro!"})
                        st.rerun()

        # Chat input
        if st.session_state.chat_flow == "asking" and not st.session_state.get("chat_pending_cmd"):
            user_text = st.chat_input("Digite um comando... Ex: pública foto 1 sexta 14h")
            if user_text:
                st.session_state.chat_msgs.append({"role": "user", "content": user_text})
                photo_descs = st.session_state.get("chat_photos_data") or [f"Foto {i+1}" for i in range(len(uploaded_files))]
                photos_payload = [
                    {"ai_description": desc}
                    for desc in photo_descs
                ]
                interp_resp = api_post("/api/chat/interpret", data={
                    "text": user_text,
                    "photos": photos_payload,
                })
                if "error" in interp_resp:
                    st.session_state.chat_msgs.append({"role": "ai", "content": f"❌ Erro ao interpretar: {interp_resp['error']}"})
                else:
                    interpretation = interp_resp.get("interpretation", {})
                    preview = interp_resp.get("preview", "Comando interpretado.")
                    st.session_state.chat_pending_cmd = {
                        "interpretation": interpretation,
                        "preview": preview,
                        "user_text": user_text,
                    }
                    st.session_state.chat_msgs.append({
                        "role": "ai",
                        "content": preview,
                    })
                st.rerun()

        # Asking phase: per-photo forms
        if st.session_state.chat_flow == "asking":
            total_photos = len(uploaded_files)
            st.markdown("---")
            st.markdown("#### 📝 Detalhes de cada foto")
            all_filled = True
            for idx in range(total_photos):
                data = st.session_state.chat_data[str(idx)]
                with st.container(border=True):
                    st.markdown(f'<div style="font-size:13px;color:#8888aa;"><b>📷 Foto {idx+1}</b></div>', unsafe_allow_html=True)
                    col_i, col_f = st.columns([1, 3])
                    with col_i:
                        st.image(uploaded_files[idx], width=80)
                    with col_f:
                        inp = st.text_area("Descrição", key=f"chat_u_{idx}", value=data.get("user_input", ""),
                                           placeholder="Ex: Vestido floral, tecido leve...", height=60, label_visibility="collapsed")
                        c_p, c_s = st.columns(2)
                        with c_p:
                            pr = st.number_input("💰 Preço (R$)", min_value=0.0, step=0.5, format="%.2f",
                                                 value=data.get("price"), key=f"chat_p_{idx}")
                        with c_s:
                            sz = st.text_input("📏 Tamanhos", key=f"chat_s_{idx}", value=data.get("sizes", ""),
                                               placeholder="P, M, G")
                        data["user_input"] = inp or ""
                        data["price"] = pr if pr and pr > 0 else None
                        data["sizes"] = sz or ""
                        if not inp and not pr and not sz:
                            all_filled = False

            st.markdown("---")

            templates_resp = api_get("/api/templates/")
            templates = templates_resp.get("templates", [])
            tpl_opts = {t["id"]: t["name"] for t in templates if t["type"] == "image"}
            selected_template = st.selectbox(
                "🎨 Template (igual para todas)",
                options=list(tpl_opts.keys()),
                format_func=lambda x: tpl_opts.get(x, x),
            )

            if st.button("✨ GERAR CONTEÚDO COM IA", type="primary", use_container_width=True):
                progress = st.progress(0, text="Gerando conteúdo...")
                created = []
                for idx, f in enumerate(uploaded_files):
                    progress.progress((idx + 1) / len(uploaded_files), text=f"📝 Gerando post {idx+1}/{len(uploaded_files)}...")
                    data = st.session_state.chat_data[str(idx)]
                    payload = {
                        "user_input": data["user_input"],
                        "sizes": data["sizes"],
                        "template_id": selected_template or "tpl_feed_01",
                    }
                    if data["price"] is not None:
                        payload["price"] = str(data["price"])
                    files = {"file": (f.name, f.getvalue(), f.type)}
                    r = api_post("/api/posts/upload", data=payload, files=files)
                    if "error" not in r:
                        created.append(r)
                    else:
                        st.error(f"Erro foto {idx+1}: {r['error']}")
                progress.empty()

                if created:
                    st.session_state.chat_created_posts = created
                    st.session_state.chat_flow = "done"
                    st.rerun()

        # Done phase
        if st.session_state.chat_flow == "done":
            created = st.session_state.chat_created_posts
            if created:
                st.success(f"✅ {len(created)} post(s) criados!")
                for idx, p in enumerate(created):
                    with st.container(border=True):
                        st.markdown(f"**📷 Post {idx+1}** — `{p.get('ai_category', 'look')}`")
                        st.markdown(f"📝 {p.get('ai_caption', '')[:200]}")
                        cta = p.get("ai_cta", "")
                        if cta:
                            st.markdown(f"🎯 CTA: {cta}")
                        ht = p.get("ai_hashtags", "")
                        if ht:
                            st.markdown(f"🏷️ {ht}")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("📋 Ir para Revisão", use_container_width=True):
                        st.session_state.current_post = created[0]
                        st.session_state.page = "review"
                        st.rerun()
                with col_r2:
                    if st.button("📅 Ver Agenda", use_container_width=True):
                        st.session_state.page = "schedule"
                        st.rerun()


def _execute_chat_command(uploaded_files):
    """Execute a confirmed chat command."""
    pending = st.session_state.get("chat_pending_cmd")
    if not pending:
        return

    interp = pending["interpretation"]
    action = interp.get("action", "gerar")
    target_idx = interp.get("target_index")
    dt_str = interp.get("datetime")
    price = interp.get("price")
    sizes = interp.get("sizes")

    if target_idx == -999:
        indices = list(range(len(uploaded_files)))
    elif target_idx is not None and 0 <= target_idx < len(uploaded_files):
        indices = [target_idx]
    else:
        st.session_state.chat_msgs.append({"role": "ai", "content": "❌ Não identifiquei qual foto. Tente: *foto 1*, *todas*, etc."})
        st.session_state.chat_pending_cmd = None
        return

    progress = st.progress(0, text="Executando...")
    created = []
    errors = []

    for i, idx in enumerate(indices):
        f = uploaded_files[idx]
        data = st.session_state.chat_data.get(str(idx), {})
        user_input = data.get("user_input", "")
        progress.progress((i + 1) / len(indices), text=f"📝 Processando foto {idx+1}...")

        payload = {
            "user_input": user_input or "",
            "sizes": sizes or data.get("sizes", ""),
            "template_id": "tpl_feed_01",
        }
        final_price = price if price is not None else data.get("price")
        if final_price is not None:
            payload["price"] = str(final_price)

        files_data = {"file": (f.name, f.getvalue(), f.type)}
        r = api_post("/api/posts/upload", data=payload, files=files_data)
        if "error" in r:
            errors.append({"index": idx, "error": r["error"]})
            continue

        post_id = r.get("id")
        if action == "agendar" and dt_str and post_id:
            try:
                schedule_payload = {
                    "final_caption": r.get("final_caption") or r.get("ai_caption", ""),
                    "final_cta": r.get("final_cta") or r.get("ai_cta", ""),
                    "final_hashtags": r.get("final_hashtags") or r.get("ai_hashtags", ""),
                    "final_category": r.get("final_category") or r.get("ai_category", "look"),
                    "scheduled_at": dt_str,
                }
                approve_resp = api_post(f"/api/posts/{post_id}/approve", data=schedule_payload)
                if "error" in approve_resp:
                    errors.append({"index": idx, "error": f"Aprovado mas erro ao agendar: {approve_resp['error']}"})
            except Exception as e:
                errors.append({"index": idx, "error": f"Erro ao agendar: {str(e)}"})

        created.append(r)

    progress.empty()
    st.session_state.chat_pending_cmd = None

    msg_parts = []
    if created:
        msg_parts.append(f"✅ {len(created)} post(s) criados")
        if action == "agendar" and dt_str:
            msg_parts.append("e agendados")
    if errors:
        msg_parts.append(f"⚠️ {len(errors)} erro(s)")
    msg = " — ".join(msg_parts) + "!"

    st.session_state.chat_msgs.append({"role": "ai", "content": msg})
    if errors:
        for e in errors:
            st.session_state.chat_msgs.append({"role": "ai", "content": f"❌ Foto {e['index']+1}: {e['error']}"})

    st.session_state.chat_created_posts = created
    st.rerun()

# ──────────────────────────────────────────────
# PAGE: REVIEW
# ──────────────────────────────────────────────
def render_review():
    post = st.session_state.get("current_post") or {}
    post_id = post.get("id", "")

    if not post_id:
        st.markdown('<div class="page-title">✅ Revisão</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Nenhum post selecionado</div>', unsafe_allow_html=True)

        pending = api_get("/api/posts/", params={"status": "revisao"})
        pp = pending.get("posts", [])
        if pp:
            st.markdown("### Posts aguardando revisão")
            for p in pp:
                cols = st.columns([1, 3, 1, 1])
                with cols[0]:
                    mpp = p.get("media_processed_path", "")
                    if mpp:
                        st.image(f"{API_BASE}/media/processed/{Path(mpp).name}", width=80)
                with cols[1]:
                    cap = p.get("final_caption") or p.get("ai_caption", "")
                    st.markdown(f"**{cap[:60]}...**" if len(cap) > 60 else f"**{cap}**")
                    st.caption(p.get("final_category") or p.get("ai_category", "-"))
                with cols[2]:
                    s = p.get("scheduled_at", "")
                    if s:
                        try:
                            st.caption(datetime.fromisoformat(s).strftime("%d/%m %H:%M"))
                        except Exception:
                            pass
                with cols[3]:
                    if st.button("📋 Revisar", key=f"rev_{p['id']}"):
                        st.session_state.current_post = p
                        st.rerun()
        else:
            st.info("Nenhum post aguardando revisão.")
            if st.button("← Criar nova postagem"):
                st.session_state.page = "upload"
                st.rerun()
        return

    st.markdown('<div class="page-title">✅ Revisão</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Confira, edite e aprove o conteúdo</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if st.button("← Voltar para lista", use_container_width=False):
        st.session_state.current_post = None
        st.rerun()

    action = st.session_state.pop("last_action", None)
    if action == "approved":
        st.success("✅ Post aprovado e agendado com sucesso!")
    elif action == "canceled":
        st.info("Agendamento cancelado.")
    elif action == "discarded":
        st.info("Post descartado.")

    fresh = api_get(f"/api/posts/{post_id}")
    if "error" not in fresh:
        post = fresh
        st.session_state.current_post = post

    col_preview, col_form = st.columns([1, 1])

    with col_preview:
        st.markdown('<div class="card"><h4 style="margin:0 0 12px 0; font-weight:600;">📸 Preview</h4>', unsafe_allow_html=True)
        processed = post.get("media_processed_path", "")
        if processed:
            media_url = f"{API_BASE}/media/processed/{Path(processed).name}"
            if post.get("media_type") == "video":
                st.video(media_url)
            else:
                st.image(media_url, width=400)
        else:
            st.caption("Preview indisponível")

        if post.get("price"):
            st.metric("💰 Preço", f"R$ {float(post['price']):.2f}".replace('.', ','))
        if post.get("sizes"):
            st.write(f"📏 Tamanhos: {post['sizes']}")

        st.write(f"📂 Categoria sugerida: **{post.get('ai_category', '-')}**")
        st.write(f"📝 Descrição IA: _{post.get('ai_description', '')[:120]}..._")

        if st.button("🔄 Refazer IA", use_container_width=True, help="Regenerar legenda, CTA e hashtags"):
            with st.spinner("🧠 IA regenerando..."):
                r = api_post(f"/api/posts/{post_id}/regenerate")
                if "error" in r:
                    st.error(f"Erro: {r['error']}")
                else:
                    st.success("Conteúdo regenerado!")
                    st.session_state.current_post = r.get("post", post)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_form:
        st.markdown('<div class="card"><h4 style="margin:0 0 12px 0; font-weight:600;">✏️ Conteúdo</h4>', unsafe_allow_html=True)

        categories = ["look", "dica", "lifestyle", "social", "novidade"]
        cat_labels = {
            "look": "👗 Look da Loja",
            "dica": "💡 Dica de Moda",
            "lifestyle": "🌿 Lifestyle",
            "social": "👥 Prova Social",
            "novidade": "✨ Novidade",
        }
        cat_idx = categories.index(post.get("ai_category", "look")) if post.get("ai_category") in categories else 0
        category = st.selectbox(
            "Categoria",
            categories,
            index=cat_idx,
            format_func=lambda x: cat_labels.get(x, x),
        )

        caption = st.text_area(
            "Legenda", value=post.get("ai_caption", ""), height=180,
            help="Edite a legenda gerada pela IA",
        )
        cta = st.text_input("CTA", value=post.get("ai_cta", ""),
                            help="Chamada para ação")

        ht_raw = post.get("ai_hashtags", "")
        ht_str = ht_raw.replace(",", " ") if isinstance(ht_raw, str) else ""
        hashtags = st.text_area("Hashtags", value=ht_str, height=70)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card" style="margin-top:12px;"><h4 style="margin:0 0 12px 0; font-weight:600;">📅 Agendamento</h4>', unsafe_allow_html=True)
        if "quick_sched_date" not in st.session_state:
            st.session_state.quick_sched_date = date.today() + timedelta(days=1)

        col_d, col_t = st.columns(2)
        with col_d:
            sched_date = st.date_input("Data", value=st.session_state.quick_sched_date, key="sched_date")
        with col_t:
            sched_time = st.time_input("Horário", value=time(10, 0), key="sched_time")

        st.markdown("**Agenda rápida:**")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            if st.button("📅 +1 Semana", use_container_width=True):
                st.session_state.quick_sched_date = date.today() + timedelta(days=7)
                st.rerun()
        with col_q2:
            if st.button("📅 +1 Mês", use_container_width=True):
                st.session_state.quick_sched_date = date.today() + timedelta(days=30)
                st.rerun()

        sched_dt = datetime.combine(sched_date, sched_time, tzinfo=BRASIL_TZ)
        st.caption(f"🕐 **{sched_dt.strftime('%d/%m/%Y às %H:%M')}**")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            if st.button("💾 Salvar", use_container_width=True):
                payload = {
                    "final_caption": caption, "final_cta": cta,
                    "final_hashtags": hashtags, "final_category": category,
                    "scheduled_at": sched_dt.isoformat(),
                }
                r = api_put(f"/api/posts/{post_id}/review", data=payload)
                if "error" in r:
                    st.error(f"Erro: {r['error']}")
                else:
                    st.success("Salvo!")
                    st.rerun()

        with col_b2:
            if st.button("❌ Descartar", use_container_width=True):
                r = api_delete(f"/api/posts/{post_id}")
                if "error" in r:
                    st.error(f"Erro: {r['error']}")
                else:
                    st.session_state.current_post = None
                    st.session_state.last_action = "discarded"
                    st.session_state.page = "schedule"
                    st.rerun()

        with col_b3:
            if st.button("✅ APROVAR", type="primary", use_container_width=True):
                payload = {
                    "final_caption": caption, "final_cta": cta,
                    "final_hashtags": hashtags, "final_category": category,
                    "scheduled_at": sched_dt.isoformat(),
                }
                r = api_post(f"/api/posts/{post_id}/approve", data=payload)
                if "error" in r:
                    err = r["error"]
                    if isinstance(err, dict):
                        st.error(err.get("message", str(err)))
                        for i in err.get("issues", []):
                            st.warning(f"⚠️ {i}")
                    else:
                        st.error(err)
                else:
                    st.session_state.last_action = "approved"
                    st.session_state.current_post = None
                    st.session_state.page = "schedule"
                    for w in r.get("warnings", []):
                        st.warning(f"⚠️ {w}")
                    st.rerun()

# ──────────────────────────────────────────────
# PAGE: SCHEDULE
# ──────────────────────────────────────────────
def render_schedule():
    st.markdown('<div class="page-title">📅 Agenda</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Veja todos os posts, edite ou cancele agendamentos</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(255,255,255,0.04); border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; font-size: 14px; color: #aaaacc;">
        <b>📌 Como funciona:</b><br>
        • <b>Agendados</b> → Posts já aprovados que serão publicados no horário marcado<br>
        • <b>Revisão</b> → Posts que a IA criou e aguardam sua aprovação<br>
        • <b>Publicados</b> → Posts que já foram enviados para o Instagram<br>
        • <b>Falhas</b> → Posts com erro na publicação<br><br>
        🔽 <b>Clique em "Ver detalhes"</b> em cada post para ver legenda completa, CTA, hashtags e mais.
    </div>
    """, unsafe_allow_html=True)

    # ⏰ Timeline: upcoming scheduled posts
    sched_result = api_get("/api/posts/", params={"status": "agendado"})
    sched_posts = sched_result.get("posts", [])
    if sched_posts:
        sched_posts.sort(key=lambda p: p.get("scheduled_at", ""))
        st.markdown("""
        <div style="background: rgba(233,30,99,0.06); border: 1px solid rgba(233,30,99,0.15);
                    border-radius: 16px; padding: 16px 20px; margin-bottom: 24px;">
            <div style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">⏰ PRÓXIMAS PUBLICAÇÕES</div>
        """, unsafe_allow_html=True)
        for p in sched_posts[:10]:
            dt_str = p.get("scheduled_at", "")
            try:
                dt = datetime.fromisoformat(dt_str)
                day_str = dt.strftime("%d/%m")
                time_str = dt.strftime("%H:%M")
            except Exception:
                day_str = "??"
                time_str = "??"
            cap = (p.get("final_caption") or p.get("ai_caption", ""))[:50]
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                <div style="min-width:60px; text-align:center;">
                    <div style="font-size:13px; font-weight:600;">{day_str}</div>
                    <div style="font-size:11px; color:#e91e63;">{time_str}</div>
                </div>
                <div style="flex:1; font-size:13px; color:#ccccee;">{cap}...</div>
                <div style="font-size:11px; color:#8888aa;">{p.get('final_category') or p.get('ai_category', '-')}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    tabs = st.tabs(["📅 Agendados", "✏️ Revisão", "✅ Publicados", "❌ Falhas"])

    status_map = [
        ("agendado", "Agendados"),
        ("revisao", "Revisão"),
        ("publicado", "Publicados"),
        ("falha_publicacao", "Falhas"),
    ]

    for tab, (status, _) in zip(tabs, status_map):
        with tab:
            result = api_get("/api/posts/", params={"status": status})
            posts = result.get("posts", [])
            if not posts:
                st.caption(f"Nenhum post com status '{status}'.")
                continue

            for p in posts:
                with st.container(border=True):
                    cols = st.columns([1, 3, 1, 1])

                    with cols[0]:
                        pp = p.get("media_processed_path", "")
                        if pp:
                            try:
                                st.image(f"{API_BASE}/media/processed/{Path(pp).name}", width=100)
                            except Exception:
                                st.caption("📷")

                    with cols[1]:
                        cap = p.get("final_caption") or p.get("ai_caption", "")
                        st.markdown(f"**{cap[:80]}...**" if len(cap) > 80 else f"**{cap}**")
                        cat = p.get("final_category") or p.get("ai_category", "-")
                        st.markdown(f"`{cat}`")

                        if p.get("scheduled_at"):
                            try:
                                dt = datetime.fromisoformat(p["scheduled_at"])
                                st.caption(f"🕐 {dt.strftime('%d/%m/%Y %H:%M')}")
                            except Exception:
                                pass
                        if p.get("published_at"):
                            try:
                                dt = datetime.fromisoformat(p["published_at"])
                                st.caption(f"✅ {dt.strftime('%d/%m/%Y %H:%M')}")
                            except Exception:
                                pass
                        if p.get("error_log"):
                            st.error(p["error_log"][:80])

                    with cols[2]:
                        st.markdown(status_badge(p["status"]), unsafe_allow_html=True)

                    with cols[3]:
                        if st.button("📋 Revisar", key=f"sch_rev_{p['id']}"):
                            st.session_state.current_post = p
                            st.session_state.page = "review"
                            st.rerun()

                    # Expandable details
                    expand_label = "🔽 Ver detalhes" if status == "agendado" else "🔽 Ver mais"
                    with st.expander(expand_label):
                        st.markdown(f"**📝 Legenda completa:**\n{cap}")
                        cta = p.get("final_cta") or p.get("ai_cta", "")
                        if cta:
                            st.markdown(f"**🎯 CTA:** {cta}")
                        ht = p.get("final_hashtags") or p.get("ai_hashtags", "")
                        if ht:
                            st.markdown(f"**🏷️ Hashtags:** {ht}")
                        if p.get("price"):
                            st.markdown(f"**💰 Preço:** R$ {float(p['price']):.2f}".replace('.', ','))
                        if p.get("sizes"):
                            st.markdown(f"**📏 Tamanhos:** {p['sizes']}")
                        if p.get("instagram_post_id"):
                            st.markdown(f"**🔗 Instagram ID:** `{p['instagram_post_id']}`")
                        if p.get("meta_response"):
                            st.code(p["meta_response"], language="json")
                        if status == "agendado":
                            col_e, col_c = st.columns(2)
                            with col_e:
                                if st.button("✏️ Editar", key=f"edit_exp_{p['id']}", use_container_width=True):
                                    st.session_state.current_post = p
                                    st.session_state.page = "review"
                                    st.rerun()
                            with col_c:
                                if st.button("↩️ Cancelar", key=f"cnl_exp_{p['id']}", use_container_width=True):
                                    api_post(f"/api/posts/{p['id']}/cancel")
                                    st.rerun()

# ──────────────────────────────────────────────
# PAGE: ANALYTICS
# ──────────────────────────────────────────────
def render_analytics():
    st.markdown('<div class="page-title">📈 Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Métricas reais baseadas no seu conteúdo</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    posts_data = api_get("/api/posts/", params={"limit": 200}).get("posts", [])
    total = len(posts_data)
    published = sum(1 for p in posts_data if p.get("status") == "publicado")
    scheduled = sum(1 for p in posts_data if p.get("status") == "agendado")
    reviewing = sum(1 for p in posts_data if p.get("status") == "revisao")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">📸</div>
            <div class="kpi-value">{total}</div>
            <div class="kpi-label">Total de Posts</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">✅</div>
            <div class="kpi-value">{published}</div>
            <div class="kpi-label">Publicados</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">📅</div>
            <div class="kpi-value">{scheduled}</div>
            <div class="kpi-label">Agendados</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size: 28px;">✏️</div>
            <div class="kpi-value">{reviewing}</div>
            <div class="kpi-label">Em Revisão</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown('<div class="card"><h4 style="margin:0 0 16px 0; font-weight:600;">📈 Publicações</h4>', unsafe_allow_html=True)
        if posts_data:
            days_map = {}
            for p in posts_data:
                s = p.get("published_at") or p.get("scheduled_at") or p.get("created_at", "")
                try:
                    d = datetime.fromisoformat(s).strftime("%d/%b")
                    days_map[d] = days_map.get(d, 0) + 1
                except Exception:
                    pass
            if days_map:
                fig = px.bar(x=list(days_map.keys()), y=list(days_map.values()),
                    labels={"x": "", "y": "Posts"}, color_discrete_sequence=["#e91e63"])
                fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter"), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown('<div style="text-align:center;padding:40px 0;color:#666688;">Nenhum dado ainda</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;padding:40px 0;color:#666688;">Nenhum dado ainda</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with col_a2:
            st.markdown('<div class="card"><h4 style="margin:0 0 16px 0; font-weight:600;">📊 Por Categoria</h4>', unsafe_allow_html=True)
            cats = Counter(p.get("final_category") or p.get("ai_category", "look") for p in posts_data)
        if cats:
            fig2 = px.pie(names=list(cats.keys()), values=list(cats.values()),
                color_discrete_sequence=["#e91e63", "#9c27b0", "#2196f3", "#4caf50", "#ff9800"], hole=0.5)
            fig2.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"), showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown('<div style="text-align:center;padding:40px 0;color:#666688;">Nenhum dado ainda</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PAGE: SETTINGS
# ──────────────────────────────────────────────
def render_settings():
    st.markdown('<div class="page-title">⚙️ Configurações</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Gerencie sua conta, templates e integrações</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    settings = api_get("/api/settings/")

    tabs = st.tabs(["🏪 Loja", "🤖 IA", "📱 Instagram", "🎨 Templates", "⏰ Horários"])

    with tabs[0]:
        store_name = st.text_input("Nome da Loja", value=settings.get("store_name", "Minha Loja"))
        brand_voice = st.selectbox(
            "Tom de Voz",
            ["amigavel", "sofisticado", "divertido", "formal"],
            index=["amigavel", "sofisticado", "divertido", "formal"].index(
                settings.get("brand_voice", "amigavel")
            ) if settings.get("brand_voice") in ["amigavel", "sofisticado", "divertido", "formal"] else 0,
        )
        if st.button("💾 Salvar Loja"):
            api_post("/api/settings/", data={"key": "store_name", "value": store_name})
            api_post("/api/settings/", data={"key": "brand_voice", "value": brand_voice})
            st.success("Dados da loja salvos!")
            st.rerun()

    with tabs[1]:
        st.markdown("#### 🤖 Inteligência Artificial")
        st.markdown(
            "Insira sua chave da OpenRouter para usar IA de visão nos servidores deles "
            "(grátis via Gemini Flash). <a href='https://openrouter.ai/keys' target='_blank'>Criar chave</a>",
            unsafe_allow_html=True,
        )
        openrouter_key = st.text_input(
            "OpenRouter API Key",
            value="****" if settings.get("openrouter_key") else "",
            type="password",
            placeholder="sk-or-v1-...",
        )
        if st.button("💾 Salvar Chave IA"):
            if openrouter_key and openrouter_key != "****":
                api_post("/api/settings/", data={"key": "openrouter_key", "value": openrouter_key})
                st.success("Chave OpenRouter salva! A IA vai usar os servidores deles.")
                st.rerun()

    with tabs[2]:
        meta_status = api_get("/api/meta/status")
        if meta_status.get("configured"):
            st.success(f"✅ Instagram configurado. Modo: {meta_status.get('mode', '?')}")
            expiry = meta_status.get("token_expiry_days")
            if expiry is not None:
                if expiry < 7:
                    st.error(f"⚠️ Token expira em {expiry} dias! Renove.")
                else:
                    st.info(f"Token válido por ~{expiry} dias.")
        else:
            st.warning("Instagram não configurado. Adicione suas credenciais abaixo.")

        st.markdown("#### Credenciais do Meta Business")
        meta_app_id = st.text_input("App ID", value=settings.get("meta_app_id", ""), type="password")
        meta_app_secret = st.text_input("App Secret", value=settings.get("meta_app_secret", ""), type="password")
        meta_access_token = st.text_input(
            "Access Token",
            value="****" if settings.get("meta_access_token") else "",
            type="password",
            placeholder="Token de acesso do Meta",
        )
        meta_ig_user_id = st.text_input("Instagram Business Account ID", value=settings.get("meta_ig_user_id", ""))

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Salvar Meta"):
                api_post("/api/settings/", data={"key": "meta_app_id", "value": meta_app_id})
                api_post("/api/settings/", data={"key": "meta_app_secret", "value": meta_app_secret})
                if meta_access_token and meta_access_token != "****":
                    api_post("/api/settings/", data={"key": "meta_access_token", "value": meta_access_token})
                api_post("/api/settings/", data={"key": "meta_ig_user_id", "value": meta_ig_user_id})
                st.success("Configurações Meta salvas!")
        with col_s2:
            if st.button("🔗 Testar Conexão"):
                r = api_post("/api/meta/test")
                if "error" in r:
                    st.error(f"Falha: {r['error']}")
                else:
                    st.success(f"Conectado! {r.get('message', '')}")

    with tabs[2]:
        st.markdown("#### Templates Disponíveis")
        templates_resp = api_get("/api/templates/")
        templates = templates_resp.get("templates", [])
        for t in templates:
            cols = st.columns([1, 2, 1])
            with cols[0]:
                st.markdown(f"**{t['name']}**")
            with cols[1]:
                st.caption(f"ID: {t['id']} · Tipo: {t['type']}")
            with cols[2]:
                st.caption("✅ Ativo")

    with tabs[3]:
        default_hour = st.number_input(
            "Horário padrão de postagem",
            min_value=0, max_value=23,
            value=int(settings.get("default_schedule_hour", "10")),
        )
        if st.button("Salvar Horário"):
            api_post("/api/settings/", data={"key": "default_schedule_hour", "value": str(default_hour)})
            st.success(f"Horário padrão: {default_hour}:00")
            st.rerun()

# ──────────────────────────────────────────────
# PAGE: BATCH UPLOAD
# ──────────────────────────────────────────────
def render_batch():
    st.markdown('<div class="page-title">📂 Processar Lote</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Analisar todas as fotos de uma pasta de uma vez</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    folder_path = st.text_input(
        "Caminho da pasta com as fotos",
        placeholder="Ex: C:\\Users\\...\\fotos_loja",
        help="Cole o caminho completo da pasta que contém as imagens",
    )
    st.caption("Formatos aceitos: JPG, JPEG, PNG")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        batch_price = st.number_input("Preço padrão (R$)", min_value=0.0, step=0.5, format="%.2f",
                                      help="Se todas as peças têm o mesmo preço")
    with col_b2:
        batch_sizes = st.text_input("Tamanhos padrão", placeholder="P, M, G",
                                    help="Se todas as peças têm os mesmos tamanhos")

    batch_input = st.text_area(
        "Descrição geral (opcional)",
        placeholder="Ex: Nova coleção verão 2026",
        height=60,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_start, col_status = st.columns([1, 2])

    with col_start:
        if st.button("🚀 INICIAR PROCESSAMENTO", type="primary", use_container_width=True):
            if not folder_path:
                st.error("Informe o caminho da pasta.")
                return

            import os
            if not os.path.isdir(folder_path):
                st.error("Pasta não encontrada. Verifique o caminho.")
                return

            payload = {
                "folder_path": folder_path,
                "user_input": batch_input or "",
                "sizes": batch_sizes or "",
                "template_id": "tpl_feed_01",
            }
            if batch_price > 0:
                payload["price"] = batch_price

            with st.spinner("🔍 Processando imagens... Isso pode levar alguns minutos."):
                result = api_post("/api/posts/batch", data=payload)

            if "error" in result:
                st.error(f"Erro: {result['error']}")
            else:
                st.session_state.batch_result = result
                st.rerun()

    with col_status:
        batch_result = st.session_state.get("batch_result")
        if batch_result:
            total = batch_result.get("processed", 0)
            errors = batch_result.get("errors", 0)
            st.success(f"✅ {total} fotos processadas" + (f" ({errors} erros)" if errors else ""))
            st.caption("As fotos foram salvas como rascunho. Revise cada uma na página de Revisão.")

    st.markdown("<br>", unsafe_allow_html=True)

    batch_result = st.session_state.get("batch_result")
    if batch_result and batch_result.get("posts"):
        total_p = batch_result.get("processed", 0)
        st.markdown(f"### Resultados ({total_p} fotos)")

        search = st.text_input("🔍 Buscar por nome do arquivo", placeholder="Filtrar...")

        posts_list = batch_result["posts"]
        if search:
            posts_list = [p for p in posts_list if search.lower() in p.get("file", "").lower()]

        for i, p in enumerate(posts_list):
            with st.container(border=True):
                cols = st.columns([2, 4, 1, 1])
                with cols[0]:
                    st.markdown(f"**📄 {p.get('file', '-')}**")
                with cols[1]:
                    cap = p.get("caption", "")
                    st.markdown(f"_{cap[:80]}..._" if cap else "_Sem legenda_")
                with cols[2]:
                    st.markdown(f"`{p.get('post_id', '')[:8]}`")
                with cols[3]:
                    if st.button("📋 Revisar", key=f"batch_rev_{p.get('post_id', i)}"):
                        fresh = api_get(f"/api/posts/{p['post_id']}")
                        if "error" not in fresh:
                            st.session_state.current_post = fresh
                            st.session_state.page = "review"
                            st.rerun()

        if batch_result.get("error_details"):
            with st.expander(f"❌ Erros ({len(batch_result['error_details'])})"):
                for e in batch_result["error_details"]:
                    st.error(f"{e.get('file', '?')}: {e.get('error', '?')}")

# ──────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────
def main():
    render_sidebar()

    if st.session_state.page == "dashboard":
        render_dashboard()
    elif st.session_state.page == "upload":
        render_upload()
    elif st.session_state.page == "review":
        render_review()
    elif st.session_state.page == "schedule":
        render_schedule()
    elif st.session_state.page == "analytics":
        render_analytics()
    elif st.session_state.page == "batch":
        render_batch()
    elif st.session_state.page == "settings":
        render_settings()

if __name__ == "__main__":
    main()
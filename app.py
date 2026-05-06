"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           AMR Guardian — Antimicrobial Resistance Surveillance              ║
║           Pakistan · WHO GLASS 2023 · Powered by Groq llama-3.3-70b        ║
╚══════════════════════════════════════════════════════════════════════════════╝

ARCHITECTURE:
  load_data()        → loads & cleans amr_data.csv
  get_groq_client()  → returns authenticated Groq client (free tier)
  build_sidebar()    → filter dropdowns + WHO reference panel
  render_kpis()      → 5 summary metric cards
  render_charts()    → bar, line, heatmap, antibiogram table
  render_map()       → Pakistan city bubble map
  render_uploader()  → CSV / text lab report parser (Groq)
  render_bulletin()  → AI weekly AMR bulletin (Groq) ← demo centrepiece
  render_chatbot()   → Lab report interpreter chatbot (Groq)
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os, io, json, random, logging, datetime

# ── Third-party ───────────────────────────────────────────────────────────────
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from groq import Groq

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("amr_guardian")

# ══════════════════════════════════════════════════════════════════════════════
# Page config — must be the FIRST Streamlit call
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="AMR Guardian", page_icon="🧬",
                   layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════════
DATA_PATH  = "amr_data.csv"
GROQ_MODEL = "llama-3.3-70b-versatile"   # free-tier model

PLOT_CFG = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=30, b=10), font=dict(color="#e2e8f0"))

CITY_COORDS = {
    "Karachi":    {"lat": 24.8607, "lon": 67.0011},
    "Lahore":     {"lat": 31.5497, "lon": 74.3436},
    "Islamabad":  {"lat": 33.6844, "lon": 73.0479},
    "Peshawar":   {"lat": 34.0151, "lon": 71.5249},
    "Quetta":     {"lat": 30.1798, "lon": 66.9750},
    "Rawalpindi": {"lat": 33.5651, "lon": 73.0169},
    "Faisalabad": {"lat": 31.4504, "lon": 73.1350},
    "Multan":     {"lat": 30.1575, "lon": 71.5249},
}

WHO_REFERENCE = [
    ("Klebsiella + Ceftriaxone",  84),
    ("Strep + Co-trimoxazole",    87),
    ("E. coli + Ceftriaxone",     83),
    ("Acinetobacter + Meropenem", 68),
    ("Klebsiella + Meropenem",    59),
    ("Salmonella + Ceftriaxone",  49),
]

# ══════════════════════════════════════════════════════════════════════════════
# CSS — dark biopunk theme
# ══════════════════════════════════════════════════════════════════════════════
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--bg:#0a0e1a;--surface:#111827;--border:#1e2d40;--accent:#00d4aa;
      --accent2:#ff6b6b;--accent3:#ffd166;--text:#e2e8f0;--muted:#64748b}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background-color:var(--bg);color:var(--text)}
.amr-header{display:flex;align-items:center;gap:20px;padding:24px 0 20px;
  border-bottom:1px solid var(--border);margin-bottom:28px;
  background:linear-gradient(90deg,rgba(0,212,170,.04) 0%,transparent 60%)}
.amr-title{font-family:'Space Mono',monospace;font-size:2rem;font-weight:700;
  color:var(--accent);letter-spacing:-1px;margin:0}
.amr-subtitle{font-size:.87rem;color:var(--muted);font-family:'Space Mono',monospace;margin:0}
.kpi-row{display:flex;gap:16px;margin-bottom:28px;flex-wrap:wrap}
.kpi-card{flex:1;min-width:160px;background:var(--surface);border:1px solid var(--border);
  border-radius:12px;padding:20px 24px}
.kpi-label{font-size:.74rem;text-transform:uppercase;letter-spacing:1.5px;
  color:var(--muted);font-family:'Space Mono',monospace;margin-bottom:8px}
.kpi-value{font-family:'Space Mono',monospace;font-size:2rem;font-weight:700;line-height:1}
.kpi-value.red{color:#ff6b6b}.kpi-value.green{color:#00d4aa}
.kpi-value.yellow{color:#ffd166}.kpi-value.white{color:var(--text)}
.section-title{font-family:'Space Mono',monospace;font-size:.82rem;letter-spacing:2px;
  text-transform:uppercase;color:var(--muted);margin-bottom:12px;padding-left:2px}
.chat-wrap{background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:20px;height:360px;overflow-y:auto;display:flex;flex-direction:column;
  gap:12px;margin-bottom:12px}
.msg{display:flex;gap:10px;align-items:flex-start}
.msg.user{flex-direction:row-reverse}
.msg-bubble{max-width:80%;padding:10px 14px;border-radius:12px;font-size:.9rem;
  line-height:1.55;white-space:pre-wrap}
.msg.assistant .msg-bubble{background:#1a2744;border:1px solid var(--border);
  color:var(--text);border-top-left-radius:4px}
.msg.user .msg-bubble{background:#004d3d;color:var(--text);
  border:1px solid #006655;border-top-right-radius:4px}
.avatar{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;
  justify-content:center;font-size:.85rem;flex-shrink:0}
.avatar.bot{background:#002a20;color:var(--accent);border:1px solid #006655}
.avatar.user-av{background:#1a2744;color:#7aa4f0;border:1px solid var(--border)}
.bulletin-box{background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:28px 32px;font-size:.92rem;line-height:1.7;white-space:pre-wrap;color:var(--text)}
.alert-box{background:#2d0a0a;border:1px solid #7a2020;border-left:4px solid #ff6b6b;
  border-radius:10px;padding:16px 20px;margin-top:16px;font-size:.9rem;color:#ffb3b3}
.upload-card{background:var(--surface);border:1px solid var(--border);
  border-radius:14px;padding:24px;margin-bottom:24px}
.parsed-card{background:#0d2e26;border:1px solid #006655;border-radius:12px;
  padding:20px 24px;margin-top:16px}
.parsed-key{font-family:'Space Mono',monospace;color:var(--accent);min-width:120px;
  font-size:.76rem;text-transform:uppercase;letter-spacing:.8px}
.parsed-val{color:var(--text);font-size:.88rem}
div[data-testid="stPlotlyChart"]{background:transparent!important}
.stTextArea textarea{background:var(--surface)!important;border-color:var(--border)!important;
  color:var(--text)!important;font-size:.9rem!important}
.stButton>button{background:var(--accent)!important;color:#000!important;border:none!important;
  font-family:'Space Mono',monospace!important;font-size:.77rem!important;letter-spacing:1px!important;
  font-weight:700!important;border-radius:8px!important;padding:10px 24px!important}
.stButton>button:hover{opacity:.88!important}
</style>"""

DNA_SVG = """<svg width="{s}" height="{s}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="32" cy="32" r="30" stroke="#00d4aa" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.4"/>
<circle cx="32" cy="32" r="22" fill="#0d2e26" stroke="#00d4aa" stroke-width="1.5"/>
<path d="M24 18 C24 22 28 24 28 28 C28 32 24 34 24 38 C24 42 28 44 28 46"
      stroke="#00d4aa" stroke-width="2" stroke-linecap="round" fill="none"/>
<path d="M40 18 C40 22 36 24 36 28 C36 32 40 34 40 38 C40 42 36 44 36 46"
      stroke="#ffd166" stroke-width="2" stroke-linecap="round" fill="none"/>
<line x1="24" y1="22" x2="40" y2="22" stroke="#00d4aa" stroke-width="1.2" opacity="0.7"/>
<line x1="28" y1="28" x2="36" y2="28" stroke="#00d4aa" stroke-width="1.2" opacity="0.7"/>
<line x1="24" y1="34" x2="40" y2="34" stroke="#ffd166" stroke-width="1.2" opacity="0.7"/>
<line x1="28" y1="40" x2="36" y2="40" stroke="#ffd166" stroke-width="1.2" opacity="0.7"/>
<path d="M26 44 Q32 48 38 44" stroke="#00d4aa" stroke-width="1.5" fill="none" stroke-linecap="round"/>
<circle cx="32" cy="32" r="2.5" fill="#00d4aa"/>
<circle cx="32" cy="32" r="2.5" fill="#00d4aa" opacity="0.3">
  <animate attributeName="r" values="2.5;6;2.5" dur="2.5s" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="0.3;0;0.3" dur="2.5s" repeatCount="indefinite"/>
</circle></svg>"""

# ══════════════════════════════════════════════════════════════════════════════
# Core helpers
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    """Load amr_data.csv. Falls back to synthetic demo data if not found."""
    try:
        df = pd.read_csv(path)
        df.columns       = df.columns.str.strip().str.lower()
        df["date"]       = pd.to_datetime(df["date"], errors="coerce")
        df["result"]     = df["result"].str.strip().str.title()
        df["organism"]   = df["organism"].str.strip()
        df["city"]       = df["city"].str.strip()
        df["antibiotic"] = df["antibiotic"].str.strip()
        log.info("Loaded %d rows from %s", len(df), path)
        return df
    except FileNotFoundError:
        log.warning("amr_data.csv not found — using synthetic demo data")
        import numpy as np; np.random.seed(42)
        n = 300
        return pd.DataFrame({
            "city":       np.random.choice(["Karachi","Lahore","Islamabad","Peshawar","Quetta"], n),
            "organism":   np.random.choice(["Escherichia coli","Klebsiella pneumoniae",
                                             "Acinetobacter spp.","Salmonella spp.",
                                             "Streptococcus pneumoniae"], n),
            "antibiotic": np.random.choice(["Ceftriaxone","Meropenem","Co-trimoxazole",
                                             "Ampicillin","Ciprofloxacin"], n),
            "result":     np.random.choice(["Resistant","Susceptible","Intermediate"],
                                            n, p=[0.47, 0.42, 0.11]),
            "date":       pd.date_range("2023-01-01", periods=n, freq="D")[:n],
        })


def get_groq_client():
    """
    Return authenticated Groq client.
    Key lookup order:
      1. st.secrets["GROQ_API_KEY"]   ← Hugging Face / Streamlit Cloud secrets
      2. os.environ["GROQ_API_KEY"]   ← Colab / local environment variable
    """
    key = ""
    try:    key = st.secrets["GROQ_API_KEY"]
    except: key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        st.error("❌ **GROQ_API_KEY not found.**\n\n"
                 "• **Hugging Face:** Space Settings → Variables and Secrets\n"
                 "• **Colab:** `os.environ['GROQ_API_KEY'] = 'gsk_...'`")
        return None
    return Groq(api_key=key)


def groq_chat(client, messages: list, max_tokens: int = 900, temperature: float = 0.3) -> str:
    """Thin wrapper around Groq chat completions with error handling."""
    try:
        r = client.chat.completions.create(
            model=GROQ_MODEL, messages=messages,
            temperature=temperature, max_tokens=max_tokens)
        return r.choices[0].message.content
    except Exception as e:
        log.error("Groq error: %s", e)
        return f"⚠️ Groq API error: {e}"


def pct_resistant(series: pd.Series) -> float:
    """Percentage of 'Resistant' values in a result Series."""
    return 0.0 if series.empty else round((series == "Resistant").mean() * 100, 1)


# ══════════════════════════════════════════════════════════════════════════════
# UI Sections
# ══════════════════════════════════════════════════════════════════════════════

def render_header():
    st.markdown(f"""
<div class="amr-header">
  {DNA_SVG.format(s=64)}
  <div style="flex:1">
    <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
      <p class="amr-title" style="margin:0">AMR Guardian</p>
      <span style="font-family:'Space Mono',monospace;font-size:.65rem;letter-spacing:2px;
                   color:#00d4aa;background:rgba(0,212,170,.08);border:1px solid rgba(0,212,170,.3);
                   padding:3px 10px;border-radius:20px">LIVE · v25</span>
    </div>
    <p class="amr-subtitle" style="margin:6px 0 0">
      Antimicrobial Resistance Surveillance &nbsp;·&nbsp; Pakistan &nbsp;·&nbsp; WHO GLASS 2023
    </p>
  </div>
</div>""", unsafe_allow_html=True)


def build_sidebar(df: pd.DataFrame):
    """Render sidebar filters + WHO reference panel. Returns (org, abx, city)."""
    with st.sidebar:
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:8px 0 12px">
  {DNA_SVG.format(s=36)}
  <div>
    <div style="font-family:'Space Mono',monospace;font-size:1rem;font-weight:700;
                color:#00d4aa;line-height:1">AMR Guardian</div>
    <div style="font-family:'Space Mono',monospace;font-size:.65rem;color:#64748b;margin-top:3px">
      Pakistan · WHO GLASS 2023</div>
  </div>
</div>""", unsafe_allow_html=True)
        st.markdown("---")

        wdf = st.session_state.working_df
        sel_org  = st.selectbox("Organism",   ["All"] + sorted(wdf["organism"].unique()))
        sel_abx  = st.selectbox("Antibiotic", ["All"] + sorted(wdf["antibiotic"].unique()))
        sel_city = st.selectbox("City",       ["All"] + sorted(wdf["city"].unique()))

        st.markdown("---")
        st.markdown('<p class="section-title">WHO Reference Rates (PK 2023)</p>',
                    unsafe_allow_html=True)
        for label, rate in WHO_REFERENCE:
            color = "#ff6b6b" if rate >= 70 else "#ffd166" if rate >= 50 else "#00d4aa"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:.77rem;'
                f'padding:4px 0;border-bottom:1px solid #1e2d40">'
                f'<span style="color:#94a3b8">{label}</span>'
                f'<span style="font-family:Space Mono,monospace;font-weight:700;color:{color}">{rate}%</span>'
                f'</div>', unsafe_allow_html=True)
    return sel_org, sel_abx, sel_city


def apply_filters(df: pd.DataFrame, org: str, abx: str, city: str) -> pd.DataFrame:
    fdf = df.copy()
    if org  != "All": fdf = fdf[fdf["organism"]   == org]
    if abx  != "All": fdf = fdf[fdf["antibiotic"] == abx]
    if city != "All": fdf = fdf[fdf["city"]        == city]
    return fdf


def render_kpis(fdf: pd.DataFrame):
    """5 KPI cards: Total | Resistant | Susceptible | Intermediate | Rate%"""
    if fdf.empty:
        st.info("No data matches current filters.")
        return
    total = len(fdf)
    nr = int((fdf["result"] == "Resistant").sum())
    ns = int((fdf["result"] == "Susceptible").sum())
    ni = int((fdf["result"] == "Intermediate").sum())
    rate = round(nr / total * 100, 1)
    rate_cls = "red" if rate >= 50 else "yellow" if rate >= 30 else "green"
    st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card"><div class="kpi-label">Total Isolates</div>
    <div class="kpi-value white">{total:,}</div></div>
  <div class="kpi-card"><div class="kpi-label">Resistant</div>
    <div class="kpi-value red">{nr:,}</div></div>
  <div class="kpi-card"><div class="kpi-label">Susceptible</div>
    <div class="kpi-value green">{ns:,}</div></div>
  <div class="kpi-card"><div class="kpi-label">Intermediate</div>
    <div class="kpi-value yellow">{ni:,}</div></div>
  <div class="kpi-card"><div class="kpi-label">Resistance Rate</div>
    <div class="kpi-value {rate_cls}">{rate}%</div></div>
</div>""", unsafe_allow_html=True)


def render_charts(fdf: pd.DataFrame):
    """4 charts in a 2×2 grid + antibiogram summary table."""
    if fdf.empty:
        st.info("No data matches filters.")
        return

    col1, col2 = st.columns(2)

    # Chart 1 — Resistance by organism
    with col1:
        st.markdown('<p class="section-title">Resistance Rate by Organism</p>',
                    unsafe_allow_html=True)
        org_rates = fdf.groupby("organism")["result"].apply(pct_resistant).sort_values()
        labels = (org_rates.index
                  .str.replace("Escherichia coli",        "E. coli")
                  .str.replace("Klebsiella pneumoniae",    "K. pneumoniae")
                  .str.replace("Streptococcus pneumoniae", "S. pneumoniae"))
        colors = ["#ff6b6b" if v >= 70 else "#ffd166" if v >= 50 else "#00d4aa"
                  for v in org_rates.values]
        fig = go.Figure(go.Bar(x=org_rates.values, y=labels, orientation="h",
                               marker_color=colors,
                               text=[f"{v}%" for v in org_rates.values],
                               textposition="outside",
                               textfont=dict(family="Space Mono", size=11)))
        fig.update_layout(**PLOT_CFG, xaxis=dict(range=[0,105], ticksuffix="%"), height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Chart 2 — Resistance trend over time
    with col2:
        st.markdown('<p class="section-title">Resistance Trend Over Time</p>',
                    unsafe_allow_html=True)
        dated = fdf.dropna(subset=["date"]).copy()
        dated["month"] = dated["date"].dt.to_period("M").dt.to_timestamp()
        trend = dated.groupby("month")["result"].apply(pct_resistant).reset_index(name="rate")
        fig = go.Figure(go.Scatter(x=trend["month"], y=trend["rate"],
                                   mode="lines+markers",
                                   line=dict(color="#00d4aa", width=2),
                                   marker=dict(size=6, color="#00d4aa"),
                                   fill="tozeroy", fillcolor="rgba(0,212,170,.06)"))
        fig.update_layout(**PLOT_CFG, yaxis=dict(ticksuffix="%", range=[0,105]), height=300)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    # Chart 3 — Resistance by city
    with col3:
        st.markdown('<p class="section-title">Resistance Rate by City</p>',
                    unsafe_allow_html=True)
        city_rates = fdf.groupby("city")["result"].apply(pct_resistant).sort_values(ascending=False)
        colors = ["#ff6b6b" if v >= 70 else "#ffd166" if v >= 50 else "#00d4aa"
                  for v in city_rates.values]
        fig = go.Figure(go.Bar(x=city_rates.index, y=city_rates.values,
                               marker_color=colors,
                               text=[f"{v}%" for v in city_rates.values],
                               textposition="outside",
                               textfont=dict(family="Space Mono", size=11)))
        fig.update_layout(**PLOT_CFG, yaxis=dict(ticksuffix="%", range=[0,115]), height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Chart 4 — Organism × City heatmap
    with col4:
        st.markdown('<p class="section-title">Resistance Heatmap (Organism × City)</p>',
                    unsafe_allow_html=True)
        heat = (fdf.groupby(["organism","city"])["result"]
                .apply(pct_resistant).unstack(fill_value=0))
        heat.index = (heat.index
                      .str.replace("Escherichia coli",        "E. coli")
                      .str.replace("Klebsiella pneumoniae",    "K. pneumoniae")
                      .str.replace("Streptococcus pneumoniae", "S. pneumoniae"))
        fig = go.Figure(go.Heatmap(
            z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
            colorscale=[[0,"#0d2e26"],[0.5,"#ffd166"],[1,"#ff6b6b"]],
            zmin=0, zmax=100,
            text=heat.values, texttemplate="%{text}%",
            textfont=dict(family="Space Mono", size=11),
            colorbar=dict(ticksuffix="%", tickfont=dict(family="Space Mono", size=10))))
        fig.update_layout(**PLOT_CFG, height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Antibiogram summary table
    st.markdown('<p class="section-title">Antibiotic Resistance Summary</p>',
                unsafe_allow_html=True)
    abx_sum = (fdf.groupby("antibiotic")["result"]
               .value_counts(normalize=True).mul(100).round(1)
               .unstack(fill_value=0).reset_index())
    for c in ["Resistant","Susceptible","Intermediate"]:
        if c not in abx_sum.columns: abx_sum[c] = 0.0
    abx_sum = abx_sum.rename(columns={"antibiotic":"Antibiotic"})
    abx_sum["Total Isolates"] = fdf.groupby("antibiotic").size().reindex(abx_sum["Antibiotic"]).values
    abx_sum = abx_sum.sort_values("Resistant", ascending=False)

    def _col(v):
        if isinstance(v, float):
            return ("color:#ff6b6b;font-weight:600" if v >= 70
                    else "color:#ffd166" if v >= 50 else "color:#00d4aa")
        return ""

    styled = (abx_sum[["Antibiotic","Resistant","Susceptible","Intermediate","Total Isolates"]]
              .style.map(_col, subset=["Resistant","Susceptible","Intermediate"])
              .format({"Resistant":"{:.1f}%","Susceptible":"{:.1f}%","Intermediate":"{:.1f}%"})
              .set_properties(**{"background-color":"#111827","color":"#e2e8f0",
                                 "border-color":"#1e2d40","font-size":"0.9rem"})
              .set_table_styles([{"selector":"th","props":[
                  ("background-color","#0a0e1a"),("color","#64748b"),
                  ("font-family","Space Mono, monospace"),("font-size","0.72rem"),
                  ("letter-spacing","1px"),("text-transform","uppercase"),
                  ("border-bottom","1px solid #1e2d40")]}]))
    st.dataframe(styled, use_container_width=True, height=220)


def render_map():
    """Pakistan city bubble map — bubble size = isolate count, colour = resistance %."""
    st.markdown("---")
    st.markdown('<p class="section-title">🗺 Resistance Intensity Map — Pakistan Cities</p>',
                unsafe_allow_html=True)
    wdf = st.session_state.working_df
    map_df = (wdf.groupby("city")["result"].apply(pct_resistant)
              .reset_index(name="resistance_rate"))
    map_df["lat"]      = map_df["city"].map(lambda c: CITY_COORDS.get(c,{}).get("lat"))
    map_df["lon"]      = map_df["city"].map(lambda c: CITY_COORDS.get(c,{}).get("lon"))
    map_df["isolates"] = map_df["city"].map(wdf.groupby("city").size())
    map_df             = map_df.dropna(subset=["lat","lon"])

    if map_df.empty:
        st.info("Map requires city names matching: Karachi, Lahore, Islamabad, Peshawar, Quetta.")
        return

    fig = go.Figure(go.Scattergeo(
        lat=map_df["lat"], lon=map_df["lon"],
        text=map_df.apply(
            lambda r: f"{r['city']}<br>Resistance: {r['resistance_rate']}%<br>Isolates: {int(r['isolates'])}",
            axis=1),
        mode="markers+text", textposition="top center",
        textfont=dict(family="Space Mono", size=11, color="#e2e8f0"),
        marker=dict(
            size=map_df["isolates"] / map_df["isolates"].max() * 40 + 18,
            color=map_df["resistance_rate"],
            colorscale=[[0,"#0d2e26"],[0.4,"#ffd166"],[1,"#ff6b6b"]],
            cmin=0, cmax=100,
            colorbar=dict(title="Resistance %", ticksuffix="%",
                          tickfont=dict(family="Space Mono",size=10,color="#e2e8f0"),
                          titlefont=dict(family="Space Mono",size=10,color="#64748b"),
                          bgcolor="rgba(17,24,39,.8)", bordercolor="#1e2d40"),
            line=dict(width=1.5, color="#0a0e1a"), opacity=0.88),
        hoverinfo="text"))
    fig.update_layout(
        geo=dict(scope="asia", center=dict(lat=30.3753,lon=69.3451), projection_scale=5,
                 showland=True, landcolor="#111827", showocean=True, oceancolor="#0a0e1a",
                 showcountries=True, countrycolor="#1e2d40",
                 showcoastlines=True, coastlinecolor="#1e2d40",
                 bgcolor="rgba(0,0,0,0)", lataxis_range=[23,38], lonaxis_range=[60,78]),
        paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0),
        font=dict(color="#e2e8f0"), height=420)
    st.plotly_chart(fig, use_container_width=True)


def render_uploader():
    """
    Lab report upload expander.
    .txt / pasted text → Groq extracts organism, antibiotic, result, city, date
    .csv (Format A raw or Format B aggregated) → merged directly into working_df
    """
    with st.expander("📤 Upload Lab Report — Auto-parse & Add to Dataset", expanded=False):
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">Lab Report Parser</p>', unsafe_allow_html=True)

        c1, c2 = st.columns([3,2])
        with c1:
            uploaded = st.file_uploader("Upload .txt or .csv", type=["txt","csv"],
                                        key="lab_upload")
            pasted   = st.text_area("Or paste raw lab report text",
                                    placeholder=("e.g.\nOrganism: Klebsiella pneumoniae\n"
                                                 "Ceftriaxone: R (MIC >32)\n"
                                                 "Meropenem: S\nCity: Lahore\nDate: 2024-03-15"),
                                    height=140, key="lab_text")
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            parse_btn = st.button("🔬 PARSE REPORT", key="parse_btn", use_container_width=True)

        raw_text     = ""
        csv_handled  = False

        if uploaded:
            if uploaded.name.lower().endswith(".csv"):
                csv_handled = _handle_csv(uploaded)
            else:
                try:    raw_text = uploaded.read().decode("utf-8")
                except: st.error("Could not read file. Upload a valid UTF-8 .txt file.")
        elif pasted.strip():
            raw_text = pasted.strip()

        if parse_btn:
            if csv_handled:    pass
            elif not raw_text: st.warning("Paste a report or upload a file first.")
            else:              _parse_text(raw_text)

        st.markdown('</div>', unsafe_allow_html=True)


def _handle_csv(uploaded_file) -> bool:
    """Parse uploaded CSV and merge into working_df. Returns True on success."""
    try:
        df = pd.read_csv(io.BytesIO(uploaded_file.read()))
        df.columns = (df.columns.str.replace(r"^\ufeff","",regex=True)
                      .str.strip().str.lower())
        df = df.loc[:, ~df.columns.str.startswith("unnamed")]
        cols = set(df.columns)

        # Alias mapping — handles varied column naming conventions
        aliases = {
            "organism":   ["pathogen","bacteria","bug","microorganism","species"],
            "antibiotic": ["drug","antimicrobial","agent","abx","medication"],
            "result":     ["susceptibility","interpretation","sir","category"],
            "city":       ["location","region","hospital","facility","site"],
            "date":       ["test_date","report_date","collection_date","sample_date"],
        }
        rmap = {}
        for std, alts in aliases.items():
            if std not in cols:
                for a in alts:
                    if a in cols: rmap[a] = std; break
        if rmap: df = df.rename(columns=rmap); cols = set(df.columns)

        raw_req = {"city","organism","antibiotic","result","date"}
        agg_req = {"antibiotic","resistant","susceptible","intermediate"}

        # Format A — raw isolate rows
        if raw_req.issubset(cols):
            df["date"]       = pd.to_datetime(df["date"], errors="coerce")
            df["result"]     = df["result"].str.strip().str.title()
            df["organism"]   = df["organism"].str.strip()
            df["city"]       = df["city"].str.strip()
            df["antibiotic"] = df["antibiotic"].str.strip()
            st.session_state.working_df = pd.concat(
                [st.session_state.working_df, df[list(raw_req)]], ignore_index=True)
            st.success(f"✅ {len(df)} raw isolate rows added.")
            return True

        # Format B — aggregated percentages
        elif agg_req.issubset(cols):
            orgs   = sorted(st.session_state.working_df["organism"].unique())
            cities = sorted(st.session_state.working_df["city"].unique())
            today  = str(datetime.date.today())
            rows   = []
            for _, row in df.iterrows():
                abx   = str(row["antibiotic"]).strip()
                total = int(row.get("total isolates", 10))
                rc    = max(1, round(float(row["resistant"])   / 100 * total))
                sc    = max(0, round(float(row["susceptible"]) / 100 * total))
                ic    = max(0, total - rc - sc)
                org   = random.choice(orgs)  if orgs  else "Unknown"
                city  = random.choice(cities) if cities else "Unknown"
                for res, cnt in [("Resistant",rc),("Susceptible",sc),("Intermediate",ic)]:
                    for _ in range(cnt):
                        rows.append({"city":city,"organism":org,"antibiotic":abx,
                                     "result":res,"date":pd.to_datetime(today)})
            if rows:
                st.session_state.working_df = pd.concat(
                    [st.session_state.working_df, pd.DataFrame(rows)], ignore_index=True)
                st.success(f"✅ Aggregated CSV imported — {len(rows)} rows generated.")
                return True

        st.error(f"Unrecognised CSV format. Columns: `{', '.join(sorted(cols))}`\n\n"
                 "**Format A:** city, organism, antibiotic, result, date\n\n"
                 "**Format B:** antibiotic, resistant, susceptible, intermediate")
        return False
    except Exception as e:
        st.error(f"CSV read error: {e}"); return False


def _parse_text(raw: str):
    """Send pasted/uploaded text to Groq, extract JSON record, append to dataset."""
    prompt = f"""You are a clinical microbiology data extractor.
Extract structured data from the lab report below.
Return ONLY a valid JSON object — no markdown, no backticks, no explanation.

Schema:
{{
  "organism":   "full organism name",
  "antibiotic": "antibiotic name",
  "result":     "Resistant" or "Susceptible" or "Intermediate",
  "city":       "Pakistani city (use Lahore if unclear)",
  "date":       "YYYY-MM-DD (use {datetime.date.today()} if not given)"
}}

If multiple antibiotics appear, return only the FIRST.

LAB REPORT:
{raw}"""

    client = get_groq_client()
    if not client: return

    with st.spinner("Parsing with Groq…"):
        raw_json = groq_chat(client, [{"role":"user","content":prompt}],
                             max_tokens=300, temperature=0.1)

    try:
        clean = raw_json.strip().lstrip("```json").lstrip("```").rstrip("```")
        p     = json.loads(clean)
        res   = p.get("result","").strip().title()
        if res not in ("Resistant","Susceptible","Intermediate"): res = "Resistant"
        res_color = "#ff6b6b" if res=="Resistant" else "#00d4aa" if res=="Susceptible" else "#ffd166"

        st.markdown(f"""
<div class="parsed-card">
  <div style="display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #1e4030">
    <span class="parsed-key">Organism</span><span class="parsed-val">{p.get('organism','—')}</span></div>
  <div style="display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #1e4030">
    <span class="parsed-key">Antibiotic</span><span class="parsed-val">{p.get('antibiotic','—')}</span></div>
  <div style="display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #1e4030">
    <span class="parsed-key">Result</span>
    <span class="parsed-val" style="color:{res_color};font-weight:600">{res}</span></div>
  <div style="display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #1e4030">
    <span class="parsed-key">City</span><span class="parsed-val">{p.get('city','—')}</span></div>
  <div style="display:flex;gap:12px;padding:6px 0">
    <span class="parsed-key">Date</span><span class="parsed-val">{p.get('date','—')}</span></div>
</div>""", unsafe_allow_html=True)

        new_row = pd.DataFrame([{
            "city": p.get("city","Lahore"), "organism": p.get("organism","Unknown"),
            "antibiotic": p.get("antibiotic","Unknown"), "result": res,
            "date": pd.to_datetime(p.get("date", str(datetime.date.today())), errors="coerce"),
        }])
        st.session_state.working_df = pd.concat(
            [st.session_state.working_df, new_row], ignore_index=True)
        st.success("✅ Record added — charts update automatically.")
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"Could not parse Groq response: {e}\n\nRaw: {raw_json}")


def render_bulletin():
    """
    AI Weekly AMR Bulletin Generator — the demo centrepiece.
    Groq reads city resistance stats and writes a structured 1-page clinical bulletin.
    """
    st.markdown("---")
    st.markdown('<p class="section-title">📋 AI Weekly AMR Bulletin Generator</p>',
                unsafe_allow_html=True)

    c1, c2 = st.columns([2,1])
    with c1:
        city = st.selectbox("Select City for Bulletin",
                            sorted(st.session_state.working_df["city"].unique()),
                            key="bulletin_city")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        gen = st.button("📄 GENERATE BULLETIN", key="gen_bulletin", use_container_width=True)

    if not gen: return

    client = get_groq_client()
    if not client: return

    cdf = st.session_state.working_df[st.session_state.working_df["city"] == city]
    if cdf.empty:
        st.warning(f"No data for {city}.")
        return

    # Compute statistics for the prompt
    total    = len(cdf)
    rate     = pct_resistant(cdf["result"])
    abx_r    = cdf.groupby("antibiotic")["result"].apply(pct_resistant).sort_values(ascending=False)
    org_r    = cdf.groupby("organism")["result"].apply(pct_resistant).sort_values(ascending=False)
    failing  = abx_r[abx_r >= 60].to_dict()
    critical = org_r[org_r >= 70].to_dict()

    data_block = f"""
CITY: {city}  |  TOTAL ISOLATES: {total}  |  OVERALL RESISTANCE RATE: {rate}%

ANTIBIOTIC RESISTANCE RATES:
{chr(10).join(f'  {k}: {v}%' for k, v in abx_r.items())}

ORGANISM RESISTANCE RATES:
{chr(10).join(f'  {k}: {v}%' for k, v in org_r.items())}

ANTIBIOTICS FAILING (>60%): {', '.join(f'{k} ({v}%)' for k,v in failing.items()) or 'None'}
CRITICAL ORGANISMS (>70%):  {', '.join(f'{k} ({v}%)' for k,v in critical.items()) or 'None'}
"""

    # Bulletin prompt — instructs Groq to produce a structured 5-section bulletin
    bulletin_prompt = f"""You are a senior clinical microbiologist writing a formal weekly
AMR surveillance bulletin for {city}, Pakistan.

Write a structured 1-page bulletin with EXACTLY these 5 sections:
1. EXECUTIVE SUMMARY (2-3 sentences — overall resistance situation)
2. ANTIBIOTICS FAILING (each antibiotic >60% resistance + clinical implication)
3. EMPIRIC TREATMENT RECOMMENDATIONS (by infection type: UTI, pneumonia, sepsis, wound)
4. ⚠ RESISTANCE ALERT (critical organisms needing infection control action)
5. RECOMMENDED ACTIONS (3-4 bullet points for hospital pharmacy / ID team)

Rules: clinical language, direct and actionable, reference WHO GLASS Pakistan 2023
benchmarks where relevant, never prescribe — recommend ID/pharmacy consultation.

SURVEILLANCE DATA FOR {city.upper()}:
{data_block}"""

    with st.spinner(f"Generating AMR bulletin for {city}…"):
        bulletin = groq_chat(client, [{"role":"user","content":bulletin_prompt}], max_tokens=1000)

    date_str = pd.Timestamp.now().strftime("%d %b %Y").upper()
    st.markdown(f"""
<div style="font-family:'Space Mono',monospace;font-size:.72rem;color:#64748b;
            letter-spacing:1px;margin-bottom:8px">
  AMR WEEKLY BULLETIN · {city.upper()} · {date_str}
</div>
<div class="bulletin-box">{bulletin}</div>""", unsafe_allow_html=True)

    if critical:
        alert_html = "".join(f"<b>{o}</b> — {r}% resistance<br>" for o,r in critical.items())
        st.markdown(f"""
<div class="alert-box">
  ⚠ <b>CRITICAL RESISTANCE ALERT — {city.upper()}</b><br><br>
  {alert_html}
  Immediate infection control review recommended for carbapenem-resistant
  and ESBL-producing organisms.
</div>""", unsafe_allow_html=True)


def render_chatbot():
    """Lab report interpreter chatbot — paste any AST result, get clinical guidance."""
    st.markdown("---")
    st.markdown('<p class="section-title">🔬 Lab Report Interpreter — Powered by Groq</p>',
                unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role":"assistant","content":(
            "Hello, Doctor. I'm your AMR Guardian assistant.\n\n"
            "Paste a lab report or ask about resistance patterns — I'll interpret "
            "results using WHO Pakistan 2023 data.\n\n"
            "Example: 'Patient has Klebsiella pneumoniae, Ceftriaxone MIC 32 μg/mL'")}]

    wdf = st.session_state.working_df
    resist_summary = (wdf.groupby("organism")["result"]
                      .apply(lambda s: f"{pct_resistant(s)}% resistant").to_dict())

    system = f"""You are AMR Guardian, an expert clinical microbiology AI for Pakistani hospitals.
Interpret lab reports and AST results, providing actionable clinical guidance.

LIVE DATASET (WHO Pakistan 2023):
{chr(10).join(f'  • {k}: {v}' for k,v in resist_summary.items())}

KEY REFERENCE RATES:
  • Klebsiella + Ceftriaxone: 84%   • E. coli + Ceftriaxone: 83%
  • Strep + Co-trimoxazole: 87%     • Acinetobacter + Meropenem: 68% (CRITICAL)
  • Klebsiella + Meropenem: 59%     • Salmonella + Ceftriaxone: 49%

RULES: Interpret MIC/S/I/R values · Highlight critical resistances · Suggest alternatives
when primary agents are failing · Flag infection control concerns · Be concise and clinical
· Never prescribe — recommend ID/pharmacy consultation for final decisions."""

    bot_svg = ('<svg width="18" height="18" viewBox="0 0 64 64" fill="none">'
               '<circle cx="32" cy="32" r="22" fill="#0d2e26" stroke="#00d4aa" stroke-width="2"/>'
               '<path d="M24 18 C24 22 28 24 28 28 C28 32 24 34 24 38" stroke="#00d4aa" '
               'stroke-width="2.5" stroke-linecap="round" fill="none"/>'
               '<path d="M40 18 C40 22 36 24 36 28 C36 32 40 34 40 38" stroke="#ffd166" '
               'stroke-width="2.5" stroke-linecap="round" fill="none"/>'
               '<circle cx="32" cy="32" r="2.5" fill="#00d4aa"/></svg>')

    chat_html = '<div class="chat-wrap">'
    for msg in st.session_state.chat_history:
        role     = msg["role"]
        avatar   = bot_svg if role == "assistant" else "👨‍⚕️"
        av_cls   = "bot" if role == "assistant" else "user-av"
        content  = msg["content"].replace("\n","<br>")
        chat_html += (f'<div class="msg {role}">'
                      f'<div class="avatar {av_cls}">{avatar}</div>'
                      f'<div class="msg-bubble">{content}</div></div>')
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    ci, cb = st.columns([5,1])
    with ci:
        user_input = st.text_area("Question or lab report", label_visibility="collapsed",
                                  placeholder=("Paste lab report:\nOrganism: Klebsiella pneumoniae\n"
                                               "Ceftriaxone: R (MIC >32)\nMeropenem: R (MIC >8)"),
                                  height=90, key="chat_input")
    with cb:
        st.markdown("<br>", unsafe_allow_html=True)
        send = st.button("⬆ SEND", use_container_width=True)

    if send:
        if not user_input.strip():
            st.warning("Enter a question or lab report first.")
        else:
            client = get_groq_client()
            if not client: return
            st.session_state.chat_history.append({"role":"user","content":user_input.strip()})
            with st.spinner("Analyzing…"):
                payload = ([{"role":"system","content":system}]
                           + [{"role":m["role"],"content":m["content"]}
                              for m in st.session_state.chat_history])
                reply = groq_chat(client, payload, max_tokens=700)
            st.session_state.chat_history.append({"role":"assistant","content":reply})
            st.rerun()

    if st.button("🗑 Clear Chat", key="clear_chat"):
        st.session_state.chat_history = st.session_state.chat_history[:1]
        st.rerun()


def render_footer():
    st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2d40;
            display:flex;justify-content:space-between;align-items:center">
  <span style="font-family:Space Mono,monospace;font-size:.72rem;color:#334155">
    AMR Guardian · WHO GLASS Pakistan 2023 · Streamlit + Groq llama-3.3-70b
  </span>
  <span style="font-family:Space Mono,monospace;font-size:.72rem;color:#334155">
    ⚠ For clinical decision support only — not a substitute for ID consultation
  </span>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown(CSS, unsafe_allow_html=True)

    if "working_df" not in st.session_state:
        st.session_state.working_df = load_data(DATA_PATH)

    render_header()
    sel_org, sel_abx, sel_city = build_sidebar(st.session_state.working_df)
    render_uploader()

    fdf = apply_filters(st.session_state.working_df, sel_org, sel_abx, sel_city)
    render_kpis(fdf)
    render_charts(fdf)
    render_map()
    render_bulletin()
    render_chatbot()
    render_footer()


if __name__ == "__main__":
    main()

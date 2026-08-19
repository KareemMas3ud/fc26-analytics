import streamlit as st
import clickhouse_connect
from cassandra.cluster import Cluster
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import time
import json
import os
import uuid

st.set_page_config(
    page_title="FC 26 • Live Match Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    PREMIUM CSS DESIGN SYSTEM                        ║
# ╚══════════════════════════════════════════════════════════════════════╝
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global Reset & Dark Theme ── */
.stApp {
    background: linear-gradient(160deg, #080b12 0%, #0d1117 40%, #111827 100%);
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Sidebar Styling ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 50%, #0f1419 100%) !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15);
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    font-family: 'Outfit', sans-serif !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(30, 34, 48, 0.9) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.45) !important;
}

/* ── Typography ── */
h1 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.1rem !important;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 40%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    padding-bottom: 0.3rem;
}
h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    color: #f1f5f9 !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px;
}

/* ── Glassmorphism Card ── */
.glass-card {
    background: rgba(17, 24, 39, 0.65);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    transition: border-color 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(99, 102, 241, 0.12);
}
.section-header .icon {
    font-size: 1.5rem;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: rgba(99, 102, 241, 0.1);
}
.section-header .title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #f1f5f9;
    letter-spacing: -0.2px;
}
.section-header .subtitle {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 400;
}

/* ── Match Banner ── */
.match-banner {
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.4) 0%, rgba(88, 28, 135, 0.3) 50%, rgba(127, 29, 29, 0.4) 100%);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 20px;
    padding: 28px 36px;
    text-align: center;
    margin-bottom: 24px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
    position: relative;
    overflow: hidden;
}
.match-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #6366f1, #a855f7, #ec4899, transparent);
}
.match-banner .vs-text {
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 6px 0;
}
.match-banner .team-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.3px;
}
.match-banner .team-home { color: #60a5fa; }
.match-banner .team-away { color: #f87171; }
.match-banner .live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #f87171;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.match-banner .live-dot {
    width: 7px; height: 7px;
    background: #ef4444;
    border-radius: 50%;
    animation: pulse-live 1.5s ease-in-out infinite;
}
@keyframes pulse-live {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
    50% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
}

/* ── Possession Bar ── */
.possession-container {
    background: rgba(17, 24, 39, 0.5);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.1);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 24px;
}
.possession-labels {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}
.possession-labels .team-label {
    font-family: 'Outfit', sans-serif;
    font-size: 1rem;
    font-weight: 600;
}
.possession-labels .pct {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.35rem;
    font-weight: 700;
}
.possession-labels .home-label { color: #60a5fa; }
.possession-labels .away-label { color: #f87171; text-align: right; }
.possession-track {
    width: 100%;
    height: 10px;
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.25), rgba(239, 68, 68, 0.4));
    border-radius: 99px;
    overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.4);
}
.possession-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}

/* ── KPI Metric Cards ── */
[data-testid="stMetric"] {
    background: rgba(17, 24, 39, 0.6) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.1) !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    transition: border-color 0.3s ease, transform 0.2s ease;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(99, 102, 241, 0.3) !important;
    transform: translateY(-1px);
}
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
}

/* ── DataFrame Styling ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid rgba(99, 102, 241, 0.1) !important;
}
[data-testid="stDataFrame"] table {
    font-family: 'Inter', sans-serif !important;
}

/* ── Horizontal Rule ── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.2), transparent) !important;
    margin: 28px 0 !important;
}

/* ── Waiting / Info Banner ── */
[data-testid="stAlert"] {
    background: rgba(99, 102, 241, 0.08) !important;
    border: 1px solid rgba(99, 102, 241, 0.15) !important;
    border-radius: 12px !important;
    color: #c7d2fe !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Credits Card ── */
.credits-card {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.7), rgba(30, 34, 48, 0.5));
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 14px;
    padding: 18px 16px;
    margin-top: 20px;
}
.credits-card .credits-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    color: #a78bfa;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.credits-card .credits-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(167, 139, 250, 0.3), transparent);
}
.credits-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
}
.credits-badge .badge-icon {
    width: 26px; height: 26px;
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    flex-shrink: 0;
}
.credits-badge .badge-label {
    font-size: 0.65rem;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    line-height: 1;
}
.credits-badge .badge-value {
    font-size: 0.82rem;
    color: #e2e8f0;
    font-weight: 500;
    line-height: 1.3;
}
.credits-divider {
    height: 1px;
    background: rgba(99, 102, 241, 0.08);
    margin: 4px 0;
}
.tech-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 10px;
}
.tech-pill {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 0.62rem;
    color: #a5b4fc;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}

/* ── Footer Bar ── */
.footer-bar {
    text-align: center;
    padding: 20px;
    margin-top: 32px;
    border-top: 1px solid rgba(99, 102, 241, 0.08);
    color: #475569;
    font-size: 0.72rem;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.3px;
}
.footer-bar a {
    color: #818cf8;
    text-decoration: none;
}
</style>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                 BACKEND CONNECTIONS (UNTOUCHED)                     ║
# ╚══════════════════════════════════════════════════════════════════════╝
@st.cache_resource
def init_connections():
    ch = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    cluster = Cluster(['127.0.0.1'], port=9042)
    cass = cluster.connect('fc26')
    return ch, cass

ch_client, cass_session = init_connections()

# --- PRE-LOAD BATCH LAYER DIMENSIONS (The Lambda JOIN) ---
@st.cache_data
def get_dimensions():
    dim_teams = ch_client.query_df("SELECT team_id, official_name FROM fc26_analytics.teams")
    dim_teams['team_id'] = dim_teams['team_id'].astype(str)

    dim_players = ch_client.query_df("SELECT player_id, short_name, currentTeamId FROM fc26_analytics.players")
    dim_players['player_id'] = dim_players['player_id'].astype(str)
    dim_players['currentTeamId'] = dim_players['currentTeamId'].astype(str)
    return dim_teams, dim_players

dim_teams, dim_players = get_dimensions()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    SIDEBAR: MATCH SETUP + CREDITS                   ║
# ╚══════════════════════════════════════════════════════════════════════╝
st.sidebar.markdown("""
<div style="text-align: center; padding: 8px 0 18px 0;">
    <div style="font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800;
                background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text; letter-spacing: -0.5px;">
        FC 26 Analytics
    </div>
    <div style="font-size: 0.7rem; color: #64748b; font-family: 'Inter', sans-serif;
                letter-spacing: 2px; text-transform: uppercase; margin-top: 2px;">
        Lambda Architecture Engine
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div class="section-header" style="padding-bottom:8px; margin-bottom:8px;">
    <div class="icon">⚙️</div>
    <div>
        <div class="title">Match Configuration</div>
        <div class="subtitle">Select teams to deploy simulation</div>
    </div>
</div>
""", unsafe_allow_html=True)

teams_list = dim_teams.to_dict('records')
team_options = {t['official_name']: t['team_id'] for t in teams_list}
team_names = sorted(list(team_options.keys()))

selected_team_a = st.sidebar.selectbox("🏠  Home Team", team_names, index=0)
selected_team_b = st.sidebar.selectbox("✈️  Away Team", team_names, index=1 if len(team_names) > 1 else 0)

if st.sidebar.button("🚀  Deploy Match Setup"):
    session_id = str(uuid.uuid4())[:12]
    config = {
        "team_a_id": team_options[selected_team_a],
        "team_a_name": selected_team_a,
        "team_b_id": team_options[selected_team_b],
        "team_b_name": selected_team_b,
        "match_session_id": session_id
    }
    with open("match_config.json", "w") as f:
        json.dump(config, f)
    # Truncate old speed-layer data for a clean physical state
    try:
        cass_session.execute("TRUNCATE fc26.live_events")
        cass_session.execute("TRUNCATE fc26.live_team_stats")
    except Exception:
        pass  # Non-fatal: session ID isolation is the primary safeguard
    st.sidebar.success("✅ Config Saved! Simulator will hot-reload.")

# --- Sidebar Credits ---
st.sidebar.markdown("""
<div class="credits-card">
    <div class="credits-title">📋 Project Info</div>
    <div class="credits-badge">
        <div class="badge-icon" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">🎓</div>
        <div>
            <div class="badge-label">Track</div>
            <div class="badge-value">Huawei Big Data Associate</div>
        </div>
    </div>
    <div class="credits-divider"></div>
    <div class="credits-badge">
        <div class="badge-icon" style="background: rgba(236, 72, 153, 0.12); color: #f472b6;">🏛️</div>
        <div>
            <div class="badge-label">Academy</div>
            <div class="badge-value">NTI — Huawei Egyptian Talents Academy</div>
        </div>
    </div>
    <div class="credits-divider"></div>
    <div class="credits-badge">
        <div class="badge-icon" style="background: rgba(250, 204, 21, 0.12); color: #fbbf24;">👑</div>
        <div>
            <div class="badge-label">Team Leader</div>
            <div class="badge-value">Kareem Mohammed</div>
        </div>
    </div>
    <div class="credits-divider"></div>
    <div class="credits-badge">
        <div class="badge-icon" style="background: rgba(52, 211, 153, 0.12); color: #34d399;">👤</div>
        <div>
            <div class="badge-label">Team Member</div>
            <div class="badge-value">Omar Hisham</div>
        </div>
    </div>
    <div class="credits-divider"></div>
    <div class="credits-badge">
        <div class="badge-icon" style="background: rgba(96, 165, 250, 0.12); color: #60a5fa;">👤</div>
        <div>
            <div class="badge-label">Team Member</div>
            <div class="badge-value">Mohamed Gamal</div>
        </div>
    </div>
    <div class="credits-divider"></div>
    <div class="credits-badge">
        <div class="badge-icon" style="background: rgba(167, 139, 250, 0.12); color: #a78bfa;">🎯</div>
        <div>
            <div class="badge-label">Instructor</div>
            <div class="badge-value">Eng. Ahmed Saeed Farg</div>
        </div>
    </div>
    <div class="tech-pills">
        <span class="tech-pill">ClickHouse</span>
        <span class="tech-pill">Kafka</span>
        <span class="tech-pill">PySpark</span>
        <span class="tech-pill">Cassandra</span>
        <span class="tech-pill">Streamlit</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         MAIN DASHBOARD AREA                         ║
# ╚══════════════════════════════════════════════════════════════════════╝
st.title("⚽ FC 26 Live Match Analytics")

# --- AUTO-REFRESH UI LOOP ---
placeholder = st.empty()

while True:
    with placeholder.container():

        if not os.path.exists("match_config.json"):
            st.info("👈 Please select two distinct teams in the sidebar and click **Deploy Match Setup**.")
            time.sleep(2)
            st.rerun()

        with open("match_config.json", "r") as f:
            match_config = json.load(f)
            t_a_id, t_a_name = str(match_config['team_a_id']), match_config['team_a_name']
            t_b_id, t_b_name = str(match_config['team_b_id']), match_config['team_b_name']
            match_session_id = match_config.get('match_session_id', 'FC26_FINAL_01')

        # ── SPEED LAYER QUERIES (UNTOUCHED) ──
        stats_df = pd.DataFrame()
        try:
            stats_rows = cass_session.execute(f"SELECT team, total_events FROM live_team_stats WHERE match_id='{match_session_id}' ALLOW FILTERING")
            stats_df = pd.DataFrame(list(stats_rows)).drop_duplicates(subset=['team'], keep='last')
        except: pass

        live_df = pd.DataFrame()
        try:
            # High limit ensures we capture the last known position of all 22 active players
            query = f"SELECT timestamp, team, player_id, event_type, x_coord, y_coord FROM live_events WHERE match_id='{match_session_id}' ORDER BY timestamp DESC LIMIT 1000"
            rows = cass_session.execute(query)
            live_df = pd.DataFrame(list(rows))
        except: pass

        # LAMBDA JOIN: Resolve real player/team names from the Batch Layer
        if not live_df.empty:
            # Ensure consistent string types for joining
            live_df['team'] = live_df['team'].astype(str)
            live_df['player_id'] = live_df['player_id'].astype(str)

            # Join team names from the batch dimension
            live_df = pd.merge(live_df, dim_teams, left_on='team', right_on='team_id', how='left')
            live_df['team_name'] = live_df['official_name'].fillna(live_df['team'])

            # Join player names from the batch dimension
            live_df = pd.merge(live_df, dim_players[['player_id', 'short_name']], on='player_id', how='left')
            live_df['player_name'] = live_df['short_name'].fillna(live_df['player_id'])

            # STRICT FILTER: Only show events from the two currently selected teams
            live_df = live_df[live_df['team'].isin([t_a_id, t_b_id])]

        # ╔══════════════════════════════════════════════════════════════╗
        # ║              MATCH BANNER (Home vs Away)                     ║
        # ╚══════════════════════════════════════════════════════════════╝
        st.markdown(f"""
        <div class="match-banner">
            <div class="live-badge"><div class="live-dot"></div> LIVE SIMULATION</div>
            <div style="display: flex; align-items: center; justify-content: center; gap: 32px; flex-wrap: wrap;">
                <div class="team-name team-home">{t_a_name}</div>
                <div class="vs-text">VS</div>
                <div class="team-name team-away">{t_b_name}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ╔══════════════════════════════════════════════════════════════╗
        # ║                    POSSESSION BAR                            ║
        # ╚══════════════════════════════════════════════════════════════╝
        if not stats_df.empty:
            stats_df['team'] = stats_df['team'].astype(str)
            matched_stats = stats_df[stats_df['team'].isin([t_a_id, t_b_id])]
            if len(matched_stats) == 2:
                t1 = matched_stats[matched_stats['team'] == t_a_id].iloc[0]
                t2 = matched_stats[matched_stats['team'] == t_b_id].iloc[0]

                total_ev = t1['total_events'] + t2['total_events']
                p1 = (t1['total_events'] / total_ev) * 100 if total_ev > 0 else 50
                p2 = (t2['total_events'] / total_ev) * 100 if total_ev > 0 else 50

                st.markdown(f"""
                <div class="possession-container">
                    <div class="possession-labels">
                        <div class="home-label">
                            <div class="team-label">{t_a_name}</div>
                            <div class="pct">{p1:.1f}%</div>
                        </div>
                        <div style="align-self: center; color: #475569; font-size: 0.75rem;
                                    font-family: 'Inter', sans-serif; text-transform: uppercase;
                                    letter-spacing: 2px; font-weight: 600;">Possession</div>
                        <div class="away-label">
                            <div class="team-label">{t_b_name}</div>
                            <div class="pct">{p2:.1f}%</div>
                        </div>
                    </div>
                    <div class="possession-track">
                        <div class="possession-fill" style="width: {p1}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("⏳ Awaiting stateful momentum aggregations from PySpark for selected teams...")
        else:
            st.info("⏳ Awaiting stateful momentum aggregations from PySpark for selected teams...")

        # ╔══════════════════════════════════════════════════════════════╗
        # ║               PITCH VISUALS (Radar + Heatmap)                ║
        # ╚══════════════════════════════════════════════════════════════╝
        col_radar, col_actions = st.columns(2, gap="large")
        team_colors = {t_a_name: '#3b82f6', t_b_name: '#ef4444'}

        with col_radar:
            st.markdown("""
            <div class="section-header">
                <div class="icon">📡</div>
                <div>
                    <div class="title">22-Player Live Radar</div>
                    <div class="subtitle">Real-time formation positions · 11 v 11</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not live_df.empty:
                # --- STRICT 11v11 RADAR LOGIC ---
                # For each team, find the LAST known position of each UNIQUE player,
                # then take only the 11 most recently active players per team.
                radar_frames = []
                for tid, tname in [(t_a_id, t_a_name), (t_b_id, t_b_name)]:
                    team_events = live_df[live_df['team'] == tid].copy()
                    if team_events.empty:
                        continue
                    # Get the most recent event per player (last known position)
                    last_positions = team_events.sort_values('timestamp', ascending=False) \
                                                .drop_duplicates(subset=['player_id'], keep='first')
                    # Strictly cap at 11 — take the 11 players with the most recent events
                    last_positions = last_positions.head(11)
                    last_positions['team_name'] = tname
                    radar_frames.append(last_positions)

                if radar_frames:
                    radar_df = pd.concat(radar_frames, ignore_index=True)

                    pitch1 = Pitch(pitch_type='wyscout', pitch_color='#111827', line_color='#374151')
                    fig1, ax1 = pitch1.draw(figsize=(8, 5.5))

                    for team in radar_df['team_name'].unique():
                        team_data = radar_df[radar_df['team_name'] == team]
                        color = team_colors.get(team, 'yellow')
                        glow_color = '#60a5fa' if color == '#3b82f6' else '#f87171'

                        # Outer glow ring
                        pitch1.scatter(team_data['x_coord'], team_data['y_coord'], ax=ax1,
                                       color=glow_color, edgecolors='none', s=600, zorder=1, alpha=0.15)
                        # Main player dot
                        pitch1.scatter(team_data['x_coord'], team_data['y_coord'], ax=ax1,
                                       color=color, edgecolors='white', linewidths=1.5,
                                       s=280, zorder=2)

                        # Add player name labels to the moving radar dots
                        for _, row in team_data.iterrows():
                            label = str(row['player_name']).split()[-1] if pd.notnull(row['player_name']) else row['player_id']
                            pitch1.annotate(label[:10], xy=(row['x_coord'], row['y_coord'] - 3.5),
                                            ax=ax1, ha='center', va='center', color='#e2e8f0',
                                            fontsize=6.5, fontweight='bold')

                    # Player count badge at bottom
                    for i, team in enumerate(radar_df['team_name'].unique()):
                        n = len(radar_df[radar_df['team_name'] == team])
                        color = team_colors.get(team, 'yellow')
                        ax1.text(50, -6 + i * 4, f"{team}: {n} players",
                                 ha='center', va='center', color=color,
                                 fontsize=8, fontweight='bold',
                                 transform=ax1.transData)

                    fig1.patch.set_facecolor('#0b0f19')
                    ax1.set_facecolor('#111827')
                    st.pyplot(fig1)
                    plt.close(fig1)

        with col_actions:
            st.markdown("""
            <div class="section-header">
                <div class="icon">🏟️</div>
                <div>
                    <div class="title">Action Pitch Map</div>
                    <div class="subtitle">Last 100 events with event type legend</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not live_df.empty:
                plot_df = live_df.head(100)
                pitch2 = Pitch(pitch_type='wyscout', pitch_color='#1a472a', line_color='#4ade80',
                               stripe=True, stripe_color='#16613a')
                fig2, ax2 = pitch2.draw(figsize=(8, 5.5))

                event_markers = {'pass': 'o', 'shot': '*', 'interception': 'D', 'foul': 'X'}
                for team in plot_df['team_name'].unique():
                    for event in plot_df['event_type'].unique():
                        subset = plot_df[(plot_df['team_name'] == team) & (plot_df['event_type'] == event)]
                        if not subset.empty:
                            color = team_colors.get(team, 'yellow')
                            marker = event_markers.get(event, 'o')
                            size = 400 if event == 'shot' else 120
                            label = f"{team} {event.title()}"
                            pitch2.scatter(subset['x_coord'], subset['y_coord'], ax=ax2,
                                           color=color, edgecolors='black', marker=marker,
                                           s=size, label=label, zorder=2, alpha=0.85)

                handles, labels = ax2.get_legend_handles_labels()
                if handles:
                    legend = ax2.legend(handles, labels, loc='upper center',
                                        bbox_to_anchor=(0.5, 1.18), ncol=2,
                                        frameon=True, fontsize=8, labelcolor='white',
                                        facecolor='#111827', edgecolor='#374151',
                                        framealpha=0.85)
                    legend.get_frame().set_linewidth(0.5)

                fig2.patch.set_facecolor('#0b0f19')
                st.pyplot(fig2)
                plt.close(fig2)

        st.markdown("---")

        # ╔══════════════════════════════════════════════════════════════╗
        # ║                   LAMBDA COMPARISON ROW                      ║
        # ╚══════════════════════════════════════════════════════════════╝
        col_speed, col_batch = st.columns(2, gap="large")

        with col_speed:
            st.markdown("""
            <div class="section-header">
                <div class="icon" style="background: rgba(250, 204, 21, 0.1);">⚡</div>
                <div>
                    <div class="title">Speed Layer</div>
                    <div class="subtitle">Real-time feed from Kafka → PySpark → Cassandra</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not live_df.empty:
                display_df = live_df[['team_name', 'player_name', 'event_type']].rename(
                    columns={'team_name': 'Team', 'player_name': 'Player', 'event_type': 'Event'}
                ).head(6)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.caption("Waiting for live events...")

        with col_batch:
            st.markdown("""
            <div class="section-header">
                <div class="icon" style="background: rgba(99, 102, 241, 0.1);">🗄️</div>
                <div>
                    <div class="title">Batch Layer</div>
                    <div class="subtitle">Historical baselines from ClickHouse OLAP warehouse</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            try:
                hist_df = ch_client.query_df("SELECT count() / count(DISTINCT match_id) as avg_events FROM fc26_analytics.wyscout_events")
                historical_avg = int(hist_df.iloc[0]['avg_events'])
            except:
                historical_avg = 1450 # Fallback if events schema lacks match_id

            current_total = len(live_df[live_df['team'].isin([t_a_id, t_b_id])]) if not live_df.empty else 0

            c1, c2 = st.columns(2)
            c1.metric("Historical Avg Events/Match", f"{historical_avg:,}")
            c2.metric("Current Live Events Logged", f"{current_total:,}",
                       delta=f"{historical_avg - current_total} to average", delta_color="inverse")

        # ╔══════════════════════════════════════════════════════════════╗
        # ║                        FOOTER BAR                           ║
        # ╚══════════════════════════════════════════════════════════════╝
        st.markdown("""
        <div class="footer-bar">
            FC 26 Live Match Analytics &nbsp;·&nbsp; Lambda Architecture Pipeline &nbsp;·&nbsp;
            Huawei Big Data Associate Track &nbsp;·&nbsp; NTI — Huawei Egyptian Talents Academy<br>
            <span style="color: #334155;">Built with ClickHouse · Kafka · PySpark · Cassandra · Streamlit</span>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(1.5)
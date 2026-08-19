import time
import json
import random
import os
from kafka import KafkaProducer
import clickhouse_connect

print("Waiting for Match Setup from the Dashboard...")
while not os.path.exists("match_config.json"):
    time.sleep(2)

ch = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')

producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def fetch_team_roster(team_id, team_name):
    """
    Fetch exactly 11 real player IDs for a given team using a 3-tier fallback:
      1. players.currentTeamId  (dimension table, added by schema fix)
      2. wyscout_events fact table (players who actually played for this team)
      3. Any 22 random real players split evenly (absolute last resort)
    Returns a list of (player_id, player_name) tuples, always length 11.
    """
    roster = []

    # --- Tier 1: Direct dimension lookup via currentTeamId ---
    try:
        q = ch.query_df(
            f"SELECT DISTINCT player_id, short_name "
            f"FROM fc26_analytics.players "
            f"WHERE currentTeamId = '{team_id}' "
            f"LIMIT 11"
        )
        if not q.empty:
            q['player_id'] = q['player_id'].astype(str)
            roster = list(zip(q['player_id'].tolist(), q['short_name'].tolist()))
    except Exception as e:
        print(f"  [Tier 1 MISS] currentTeamId query failed for {team_name}: {e}")

    # --- Tier 2: Fact table lookup — players who appeared in events for this team ---
    if len(roster) < 11:
        try:
            q2 = ch.query_df(
                f"SELECT DISTINCT e.player_id, p.short_name "
                f"FROM fc26_analytics.wyscout_events e "
                f"LEFT JOIN fc26_analytics.players p ON e.player_id = p.player_id "
                f"WHERE e.team_id = '{team_id}' "
                f"LIMIT 11"
            )
            if not q2.empty:
                q2['player_id'] = q2['player_id'].astype(str)
                existing_ids = {pid for pid, _ in roster}
                for _, row in q2.iterrows():
                    if row['player_id'] not in existing_ids and len(roster) < 11:
                        roster.append((row['player_id'], row['short_name']))
                        existing_ids.add(row['player_id'])
        except Exception as e:
            print(f"  [Tier 2 MISS] Events fact-table query failed for {team_name}: {e}")

    # --- Tier 3: Absolute fallback — any real players ---
    if len(roster) < 11:
        try:
            q3 = ch.query_df(
                f"SELECT DISTINCT player_id, short_name "
                f"FROM fc26_analytics.players "
                f"LIMIT {11 - len(roster)}"
            )
            if not q3.empty:
                q3['player_id'] = q3['player_id'].astype(str)
                existing_ids = {pid for pid, _ in roster}
                for _, row in q3.iterrows():
                    if row['player_id'] not in existing_ids and len(roster) < 11:
                        roster.append((row['player_id'], row['short_name']))
                        existing_ids.add(row['player_id'])
        except Exception as e:
            print(f"  [Tier 3 MISS] Global player query failed: {e}")

    # Safety: if we STILL have fewer than 11, pad with synthetic IDs
    while len(roster) < 11:
        synthetic_id = f"SYN_{team_id}_{len(roster)+1}"
        roster.append((synthetic_id, f"Player {len(roster)+1}"))

    return roster[:11]


def load_rosters(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    t_a_id, t_a_name = str(config['team_a_id']), config['team_a_name']
    t_b_id, t_b_name = str(config['team_b_id']), config['team_b_name']
    session_id = config.get('match_session_id', 'FC26_FINAL_01')
    print(f"\n--- NEW MATCH DEPLOYED: {t_a_name} vs {t_b_name} [Session: {session_id}] ---")

    # Rigid 4-3-3 Formations (11 slots each)
    form_a_slots = [
        (5, 50),                                      # GK
        (25, 20), (25, 40), (25, 60), (25, 80),       # DEF
        (50, 30), (50, 50), (50, 70),                  # MID
        (75, 30), (75, 50), (75, 70)                   # FWD
    ]
    form_b_slots = [
        (95, 50),                                      # GK
        (75, 20), (75, 40), (75, 60), (75, 80),        # DEF
        (50, 30), (50, 50), (50, 70),                   # MID
        (25, 30), (25, 50), (25, 70)                    # FWD
    ]

    roster_a = fetch_team_roster(t_a_id, t_a_name)
    roster_b = fetch_team_roster(t_b_id, t_b_name)

    print(f"  ✅ {t_a_name}: {len(roster_a)} players locked")
    print(f"  ✅ {t_b_name}: {len(roster_b)} players locked")

    state = {}
    for i, (pid, pname) in enumerate(roster_a):
        state[pid] = {
            'team': t_a_id,
            'player_name': pname,
            'base_x': form_a_slots[i][0],
            'base_y': form_a_slots[i][1]
        }
    for i, (pid, pname) in enumerate(roster_b):
        state[pid] = {
            'team': t_b_id,
            'player_name': pname,
            'base_x': form_b_slots[i][0],
            'base_y': form_b_slots[i][1]
        }

    return t_a_id, t_b_id, state, session_id


last_mod_time = os.path.getmtime("match_config.json")
team_a_id, team_b_id, player_state, match_session_id = load_rosters("match_config.json")

current_team = team_a_id
events_in_phase = 0
phase_length = random.randint(5, 12)

while True:
    # 1. Check for Dynamic Reload (hot-swap teams from dashboard)
    current_mod_time = os.path.getmtime("match_config.json")
    if current_mod_time != last_mod_time:
        last_mod_time = current_mod_time
        team_a_id, team_b_id, player_state, match_session_id = load_rosters("match_config.json")
        current_team = team_a_id
        events_in_phase = 0

    # 2. Momentum / Possession Phase Logic
    if events_in_phase >= phase_length:
        current_team = team_b_id if current_team == team_a_id else team_a_id
        events_in_phase = 0
        phase_length = random.randint(5, 12)
        event = 'interception'
    else:
        event = 'pass' if random.random() > 0.20 else 'shot'

    events_in_phase += 1

    # 3. Extract the 11 active players for the possessing team
    active_players = [pid for pid, data in player_state.items() if data['team'] == current_team]
    player = random.choice(active_players)

    # 4. Generate positional jitter around formation base
    base_x, base_y = player_state[player]['base_x'], player_state[player]['base_y']
    x = max(0, min(100, base_x + random.uniform(-2.5, 2.5)))
    y = max(0, min(100, base_y + random.uniform(-2.5, 2.5)))

    payload = {
        "match_id": match_session_id,
        "timestamp": time.time(),
        "team": current_team,
        "player_id": player,
        "player_name": player_state[player]['player_name'],
        "event_type": event,
        "x_coord": x,
        "y_coord": y
    }

    producer.send('fc26_live_events', payload)
    pname = player_state[player]['player_name']
    print(f" -> {current_team} | {pname} ({player}) | {event} | (X: {x:.1f}, Y: {y:.1f})")
    time.sleep(0.5)
import clickhouse_connect
import pandas as pd
import glob
import os

print("Connecting to ClickHouse...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')

# 1. Define and Create Dimension Tables
print("Creating Dimension Tables...")

# Players Schema
client.command("""
CREATE TABLE IF NOT EXISTS fc26_analytics.players (
    player_id String,
    short_name String,
    first_name String,
    last_name String,
    foot String,
    birth_date String,
    currentTeamId String
) ENGINE = MergeTree()
ORDER BY player_id
""")

# Teams Schema
client.command("""
CREATE TABLE IF NOT EXISTS fc26_analytics.teams (
    team_id String,
    name String,
    official_name String,
    city String,
    type String
) ENGINE = MergeTree()
ORDER BY team_id
""")

# Matches Schema
client.command("""
CREATE TABLE IF NOT EXISTS fc26_analytics.matches (
    match_id String,
    label String,
    dateutc String,
    competition_id String,
    season_id String,
    gameweek Int32
) ENGINE = MergeTree()
ORDER BY match_id
""")

print("Schemas applied successfully.")

# 2. Base Configuration
DATA_DIR = r"C:\Users\Administrator\fc26-analytics\wyscout_data"

# Helper function for safe ingestion
def ingest_dimension_file(file_path, table_name, expected_columns, rename_map):
    if not os.path.exists(file_path):
        print(f"  [SKIPPED] File not found: {file_path}")
        return
        
    print(f" -> Processing {os.path.basename(file_path)} into {table_name}...")
    df = pd.read_csv(file_path, low_memory=False)
    
    # Apply column renaming (mapping camelCase/wyId to snake_case)
    df.rename(columns=rename_map, inplace=True)
    
    # Ensure all expected columns exist, fill missing ones
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0 if col == 'gameweek' else ''
            
    # Filter strictly to expected columns and fill NaNs
    insert_df = df.reindex(columns=expected_columns).fillna('')
    
    # ENFORCE DATA TYPES TO MATCH CLICKHOUSE DDL
    for col in expected_columns:
        if col == 'gameweek':
            insert_df[col] = pd.to_numeric(insert_df[col], errors='coerce').fillna(0).astype(int)
        else:
            # Force all other columns to string. We strip '.0' in case pandas read an ID as a float
            insert_df[col] = insert_df[col].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # Bulk Insert
    client.insert_df(f'fc26_analytics.{table_name}', insert_df)
    print(f"    [SUCCESS] Inserted {len(insert_df)} records into {table_name}.")

# 3. Execute Ingestions

# A. Ingest Players
ingest_dimension_file(
    file_path=os.path.join(DATA_DIR, "players.csv"),
    table_name="players",
    expected_columns=['player_id', 'short_name', 'first_name', 'last_name', 'foot', 'birth_date', 'currentTeamId'],
    rename_map={'wyId': 'player_id', 'shortName': 'short_name', 'firstName': 'first_name', 'lastName': 'last_name', 'birthDate': 'birth_date'}
)

# B. Ingest Teams
ingest_dimension_file(
    file_path=os.path.join(DATA_DIR, "teams.csv"),
    table_name="teams",
    expected_columns=['team_id', 'name', 'official_name', 'city', 'type'],
    rename_map={'wyId': 'team_id', 'officialName': 'official_name'}
)

# C. Ingest Matches (Handling multiple files via glob)
match_files = glob.glob(os.path.join(DATA_DIR, "matches_*.csv"))
if not match_files:
    print("  [SKIPPED] No match files found matching pattern matches_*.csv")
else:
    for match_file in match_files:
        ingest_dimension_file(
            file_path=match_file,
            table_name="matches",
            expected_columns=['match_id', 'label', 'dateutc', 'competition_id', 'season_id', 'gameweek'],
            rename_map={'wyId': 'match_id', 'competitionId': 'competition_id', 'seasonId': 'season_id'}
        )

print("\nDimension Ingestion Complete! The Data Warehouse is now fully populated.")
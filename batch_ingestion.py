import clickhouse_connect
import pandas as pd
import glob
import os

# 1. Connect to ClickHouse locally
print("Connecting to ClickHouse...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')

# 2. Execute SQL DDL commands to create optimized MergeTree tables
print("Creating Database and Tables...")
client.command("CREATE DATABASE IF NOT EXISTS fc26_analytics")

# Defining the historical events table optimized for OLAP aggregations
table_schema = """
CREATE TABLE IF NOT EXISTS fc26_analytics.wyscout_events (
    match_id String,
    event_id String,
    event_name String,
    sub_event_name String,
    player_id String,
    team_id String,
    event_sec Float32,
    x_start Float32,
    y_start Float32,
    x_end Float32,
    y_end Float32
) ENGINE = MergeTree()
ORDER BY (match_id, event_name, player_id)
"""
client.command(table_schema)
print("Schema applied successfully.")

# 3. Exact path and focused glob pattern for event files ONLY
DATA_DIR = r"C:\Users\Administrator\fc26-analytics\wyscout_data\events_*.csv"
csv_files = glob.glob(DATA_DIR)

if not csv_files:
    print(f"No event CSV files found matching {DATA_DIR}.")
else:
    print(f"Found {len(csv_files)} event files. Beginning targeted Batch Ingestion...")
    
    # Expected columns to enforce strict schema adherence
    expected_columns = [
        'match_id', 'event_id', 'event_name', 'sub_event_name', 
        'player_id', 'team_id', 'event_sec', 'x_start', 'y_start', 
        'x_end', 'y_end'
    ]

    # Standard Wyscout camelCase to snake_case mapping
    rename_map = {
        'matchId': 'match_id',
        'eventId': 'event_id',
        'eventName': 'event_name',
        'subEventName': 'sub_event_name',
        'playerId': 'player_id',
        'teamId': 'team_id',
        'eventSec': 'event_sec'
    }
    
    for file in csv_files:
        print(f" -> Processing {os.path.basename(file)}...")
        
        # Read in chunks of 100,000 to prevent memory exhaustion
        chunk_iterator = pd.read_csv(file, chunksize=100000, low_memory=False)
        
        for i, chunk in enumerate(chunk_iterator):
            # Map column names
            chunk.rename(columns=rename_map, inplace=True)
            
            # Pad coordinate columns if they are not pre-flattened in your CSVs 
            # to ensure the dataframe perfectly matches the ClickHouse DDL
            for col in ['x_start', 'y_start', 'x_end', 'y_end']:
                if col not in chunk.columns:
                    chunk[col] = 0.0
                    
            # Enforce string types for IDs to prevent ClickHouse casting errors
            for col in ['match_id', 'event_id', 'event_name', 'sub_event_name', 'player_id', 'team_id']:
                if col in chunk.columns:
                    chunk[col] = chunk[col].astype(str)
            
            # Filter strictly to expected columns and fill any NaNs
            insert_df = chunk.reindex(columns=expected_columns).fillna(0)
            
            # Bulk insert DataFrame directly into ClickHouse for ultra-low latency OLAP querying
            client.insert_df('fc26_analytics.wyscout_events', insert_df)
            print(f"    Inserted chunk {i+1} for {os.path.basename(file)}")

print("Batch Ingestion Complete! ClickHouse is ready for analytical queries.")
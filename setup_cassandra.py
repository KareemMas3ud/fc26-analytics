from cassandra.cluster import Cluster

print("Connecting to Cassandra...")
# Connect to the exposed localhost port
cluster = Cluster(['127.0.0.1'], port=9042)
session = cluster.connect()

print("Creating Keyspace and Table...")
# Create Keyspace
session.execute("""
CREATE KEYSPACE IF NOT EXISTS fc26
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
""")

# Switch to the new keyspace
session.set_keyspace('fc26')

# Create the optimized live events table
session.execute("""
CREATE TABLE IF NOT EXISTS live_events (
    match_id text,
    timestamp double,
    team text,
    player_id text,
    event_type text,
    x_coord double,
    y_coord double,
    PRIMARY KEY (match_id, timestamp)
)
""")

# Create the aggregated team stats table (used by PySpark windowed stream)
session.execute("""
CREATE TABLE IF NOT EXISTS live_team_stats (
    match_id text,
    team text,
    total_events bigint,
    PRIMARY KEY (match_id, team)
)
""")

print("Cassandra schema applied successfully! Ready for PySpark streaming.")
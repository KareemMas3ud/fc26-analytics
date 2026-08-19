from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, count, from_unixtime, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

print("Initializing PySpark Streaming Context...")
spark = SparkSession.builder \
    .appName("FC26_Speed_Layer") \
    .config("spark.cassandra.connection.host", "fc26_cassandra") \
    .config("spark.cassandra.connection.port", "9042") \
    .master("local[*]") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

event_schema = StructType([
    StructField("match_id", StringType(), True),
    StructField("timestamp", DoubleType(), True),
    StructField("team", StringType(), True),
    StructField("player_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("x_coord", DoubleType(), True),
    StructField("y_coord", DoubleType(), True)
])

kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "fc26_live_events") \
    .option("startingOffsets", "latest") \
    .load()

parsed_df = kafka_df.select(from_json(col("value").cast("string"), event_schema).alias("data")).select("data.*")
time_df = parsed_df.withColumn("event_time", from_unixtime(col("timestamp")).cast("timestamp"))

# --- STREAM 1: Raw Events (For Radar & Mapping) ---
raw_query = parsed_df.writeStream \
    .format("org.apache.spark.sql.cassandra") \
    .option("keyspace", "fc26") \
    .option("table", "live_events") \
    .option("checkpointLocation", "/tmp/spark_checkpoints_raw_v7") \
    .outputMode("append") \
    .start()

# --- STREAM 2: Stateful Sliding Window (For Possession) ---
windowed_agg = time_df \
    .withWatermark("event_time", "10 seconds") \
    .groupBy(window(col("event_time"), "60 seconds", "10 seconds"), "match_id", "team") \
    .agg(count("*").alias("total_events"))

def upsert_window_to_cassandra(batch_df, batch_id):
    if batch_df.count() > 0:
        latest_window_df = batch_df.orderBy(col("window.end").desc()).drop("window")
        latest_window_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .option("keyspace", "fc26") \
            .option("table", "live_team_stats") \
            .mode("append") \
            .save()

agg_query = windowed_agg.writeStream \
    .foreachBatch(upsert_window_to_cassandra) \
    .outputMode("update") \
    .option("checkpointLocation", "/tmp/spark_checkpoints_agg_v7") \
    .start()

print("Continuous Stateful Streams Started...")
spark.streams.awaitAnyTermination()
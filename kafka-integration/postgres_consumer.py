"""
Listens to the 'inegi-sanctions' Kafka topic and writes each message to
PostgreSQL (upsert: updates the row if entity_name already exists,
otherwise inserts a new one).
 
This script runs completely independently from Scrapy -- a separate
process, in a separate terminal, start/stop it whenever you want.
"""


import json
import os

import psycopg2
from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BOOTSTRAP_SERVERS = "localhost:9094"
KAFKA_TOPIC = "inegi-sanctions"
KAFKA_GROUP_ID = "inegi-postgres-writer"

PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5433)),
    "dbname": os.getenv("PG_DBNAME", "inegi"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sanctions (
    entity_name TEXT PRIMARY KEY,
    sanction_numbers TEXT[],
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_SQL = """
INSERT INTO sanctions (entity_name, sanction_numbers, updated_at)
VALUES (%s, %s, NOW())
ON CONFLICT (entity_name)
DO UPDATE SET sanction_numbers = EXCLUDED.sanction_numbers, updated_at = NOW();
"""


def get_pg_connection():
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    return conn


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)


def write_to_postgres(conn, entity_name: str, sanction_numbers: list):
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL, (entity_name, sanction_numbers))


def main():
    conn = get_pg_connection()
    ensure_table(conn)

    consumer_conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    print(f"Listening to '{KAFKA_TOPIC}', writing to PostgreSQL... Press Ctrl+C to exit.")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            event = json.loads(msg.value().decode("utf-8"))
            entity_name = event["entity_name"]
            sanction_numbers = event.get("sanction_numbers", [])

            write_to_postgres(conn, entity_name, sanction_numbers)
            print(f"Written to PostgreSQL -> {entity_name} ({sanction_numbers})")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        consumer.close()
        conn.close()


if __name__ == "__main__":
    main()
# INEGI Sanctions Scraper + Kafka + PostgreSQL Pipeline

A Selenium/Scrapy scraper for INEGI's supplier sanctions registry,
streamed through Apache Kafka into PostgreSQL.

## Architecture

```
Selenium/Scrapy spider  --(on each item)-->  Kafka topic (inegi-sanctions)
                                                     |
                                                     v
                                  kafka-integration/postgres_consumer.py
                                                     |
                                                     v
                                        PostgreSQL "sanctions" table
```

The scraper writes to two destinations independently:
- `sanctions.json` (via the original `InegiPipeline`, deduplicated on close)
- Kafka topic `inegi-sanctions` (via `KafkaSanctionsPipeline`, streamed live)

A separate consumer process reads from Kafka and upserts into PostgreSQL,
fully decoupled from the scraper itself.

## Project structure

```
.
├── docker-compose.yml          # Kafka, Kafka UI, PostgreSQL
├── .gitignore       
├── inegi-selenium-scrapy/      # Scrapy + Selenium spider
│   └── inegi/
│       ├── spiders/
│       ├── pipelines.py        # InegiPipeline + KafkaSanctionsPipeline
│       └── settings.py
├── screenshots/
│       ├── docker-sevices-running.jpg
│       └── kafka-to-postgres-flow.jpg
└── kafka-integration/
    ├── postgres_consumer.py    # Kafka -> PostgreSQL consumer
    ├── requirements.txt
    └── README.md
```

## Setup

1. Start the infrastructure:
   ```bash
   docker compose up -d
   ```

2. Create the Kafka topic:
   ```bash
   docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --create \
     --topic inegi-sanctions --bootstrap-server localhost:9092 \
     --partitions 3 --replication-factor 1
   ```

3. Install dependencies for both parts:
   ```bash
   pip install -r inegi-selenium-scrapy/requirements.txt
   pip install -r kafka-integration/requirements.txt
   ```

4. Run the consumer (separate terminal, keeps listening):
   ```bash
   cd kafka-integration
   python postgres_consumer.py
   ```

5. Run the scraper:
   ```bash
   cd inegi-selenium-scrapy
   python main.py
   ```

See `kafka-integration/README.md` for more detail on the Kafka/Postgres layer.

## Configuration

`postgres_consumer.py` reads connection settings from environment
variables (`PG_HOST`, `PG_PORT`, `PG_DBNAME`, `PG_USER`, `PG_PASSWORD`),
falling back to local defaults matching `docker-compose.yml`.
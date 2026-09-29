from datetime import datetime
from confluent_kafka import Producer
import logging

import json
import os

logger = logging.getLogger(__name__)

class InegiPipeline:
    def open_spider(self, spider):
        self.data = []
        spider.logger.info("Pipeline started")

    def process_item(self, item, spider):
        self.data.append(dict(item)) 
        return item

    def close_spider(self, spider):  
        spider.logger.info("Removing duplicate Entity_name entries...")
        
        merged_data = {}
        for entry in self.data:
            name = entry["Entity_name"]
            numbers = entry.get("Sanction_numbers", [])

            # Remove duplicate names and numbers
            if name not in merged_data:
                    merged_data[name] = set(numbers)
            else:
                    merged_data[name].update(numbers)


        cleaned_data = []
        for name, numbers in merged_data.items():
            cleaned_data.append({
                "Entity_name": name,
                "Sanction_numbers": sorted(list(numbers))
            })

        
        output_file = spider.config.get("output_file", "sanctions.json")
        output_path = os.path.abspath(output_file)

        utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        output_data = {
            "last_updated": utc_time,
            "data": cleaned_data,   
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        spider.logger.info(f"{len(cleaned_data)} profile(s) saved: {output_path}")



class KafkaSanctionsPipeline:
    """Her scraped item'i, InegiPipeline'in JSON'a yazmasindan bagimsiz
    olarak, aninda 'inegi-sanctions' Kafka topic'ine gonderir.
 
    InegiPipeline item'lari bellekte biriktirip spider bitince tek
    seferde JSON'a yazarken, bu pipeline her item geldiginde hemen
    Kafka'ya gonderir -- iki pipeline birbirinden tamamen bagimsiz
    calisir.
    """
 
    TOPIC = "inegi-sanctions"
 
    def open_spider(self, spider):
        conf = {
            "bootstrap.servers": "localhost:9094",
            "client.id": "inegi-scraper-producer",
        }
        self.producer = Producer(conf)
 
    def close_spider(self, spider):
        # Kapanmadan once kuyrukta bekleyen tum mesajlarin gonderilmesini bekle
        self.producer.flush()
 
    def process_item(self, item, spider):
        entity_name = item.get("Entity_name", "unknown")
        sanction_numbers = item.get("Sanction_numbers", [])
 
        payload = {
            "entity_name": entity_name,
            "sanction_numbers": sanction_numbers,
        }
 
        self.producer.produce(
            topic=self.TOPIC,
            key=entity_name.encode("utf-8"),
            value=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            callback=self._delivery_report,
        )
        # Callback kuyrugunu islemek icin (bloklamadan) tetikle
        self.producer.poll(0)
 
        # Item'i pipeline zincirinde bir sonraki pipeline'a (InegiPipeline) gecir
        return item
 
    @staticmethod
    def _delivery_report(err, msg):
        if err is not None:
            logger.error(f"Kafka gonderim hatasi: {err}")
        else:
            logger.info(
                f"Kafka'ya gonderildi -> partition={msg.partition()} "
                f"offset={msg.offset()}"
            )
import logging
import time
import uuid
import json
from random import uniform

from confluent_kafka import Producer


def acked(err, msg):  # Delivery report
    if err is not None:
        logging.error(f"Failed to deliver message: {err}")
    else:
        logging.info(f"Message produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Kafka config – only broker address needed
    producer = Producer({"bootstrap.servers": "localhost:9092"})
    topic = "loan-events"   # Use the same topic you created

    while True:
        event = {
            "loan_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "amount": round(uniform(1000, 20000), 2),
            "status": "approved" if uniform(0, 1) > 0.5 else "pending",
            "timestamp": int(time.time())
        }

        # Send as JSON string
        producer.produce(
            topic=topic,
            value=json.dumps(event).encode("utf-8"),
            callback=acked
        )

        producer.poll(1)  # Trigger delivery callbacks
        time.sleep(2)  # wait before next message

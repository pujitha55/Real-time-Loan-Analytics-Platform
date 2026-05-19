import logging
import time
import json
import mysql.connector
from confluent_kafka import Consumer
from mysql.connector import Error
from configparser import ConfigParser

# Read config values
def read_config():
    config_parser = ConfigParser()
    config_parser.read("D:\\spark-structured-streaming-kafka\\movie_ratings_streaming\\config\\config.ini")  # Adjust path if needed
    
    # Log the sections to ensure the config is loaded
    logging.info(f"Config sections: {config_parser.sections()}")
    
    # Flatten the config parser and ensure all keys are directly accessible
    config_dict = {section: dict(config_parser.items(section)) for section in config_parser.sections()}
    
    # Log the config for debugging
    logging.info(f"Config: {config_dict}")
    
    if 'kafka' not in config_dict:
        logging.error("The 'kafka' section is missing from the config file.")
        raise KeyError("'kafka' section not found in config file")
    
    return config_dict

# MySQL connection setup
def create_mysql_connection():
    config = read_config()
    try:
        connection = mysql.connector.connect(
            host=config["mysql"]["host"],
            database=config["mysql"]["database"],
            user=config["mysql"]["user"],
            password=config["mysql"]["password"]
        )
        if connection.is_connected():
            logging.info("MySQL connection established successfully.")
        return connection
    except Error as e:
        logging.error(f"Error connecting to MySQL: {e}")
        raise

# Kafka consumer setup
def create_kafka_consumer():
    config = read_config()
    consumer = Consumer({
        'bootstrap.servers': config["kafka"]["bootstrap.servers"],
        'group.id': 'loan-event-consumer',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([config["kafka"]["subscribe"]])
    return consumer

# Insert data into MySQL
def insert_into_mysql(data):
    try:
        connection = create_mysql_connection()
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO loan_events (loan_id, user_id, amount, status, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (data["loan_id"], data["user_id"], data["amount"], data["status"], data["timestamp"]))
        connection.commit()
        logging.info(f"Inserted record with loan_id: {data['loan_id']}")
    except Error as e:
        logging.error(f"Error inserting data into MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Main function to consume data from Kafka
def consume_data():
    logging.basicConfig(level=logging.INFO)
    consumer = create_kafka_consumer()
    
    while True:
        try:
            msg = consumer.poll(timeout=1.0)  # Adjust timeout if needed
            
            if msg is None:
                continue  # No new message, just wait
            if msg.error():
                logging.error(f"Kafka Error: {msg.error()}")
                continue

            # Deserialize Kafka message
            data = json.loads(msg.value().decode('utf-8'))
            logging.info(f"Received message: {data}")

            # Insert data into MySQL
            insert_into_mysql(data)

        except Exception as e:
            logging.error(f"Error: {e}")
            continue  # Continue consuming data

if __name__ == "__main__":
    consume_data()

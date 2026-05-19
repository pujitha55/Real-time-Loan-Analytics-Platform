import mysql.connector

def test_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Replace with your MySQL username
            password="Maryala@2004",  # Replace with your MySQL password
            database="loan_data"  # Replace with your database name
        )
        if connection.is_connected():
            print("Connection successful!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
    test_mysql_connection()

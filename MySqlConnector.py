import mysql.connector
import json

def connect_to_database():
    db_host = 'localhost'
    db_user = 'root'
    db_password = 'MySQLPassword.2023'
    db_name = 'BookInformationDatabase'

    db_connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

    return db_connection

def insert_book_info(db_connection, book_name, author, book_price, publisher_name, book_info_json):
    db_cursor = db_connection.cursor()

    query = "INSERT IGNORE INTO books (book_name, author , price, book_publisher, book_info) VALUES (%s, %s, %s, %s, %s)"
    values = (book_name, author ,book_price, publisher_name, book_info_json)

    try:
        db_cursor.execute(query, values)
        db_connection.commit()
    except Exception as e:
        print("Error occurred while inserting data into the database:", e)

    db_cursor.close()
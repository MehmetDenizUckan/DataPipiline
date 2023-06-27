# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 18:09:19 2023

@author: UCKAN
"""
import mysql.connector

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

def insert_book_info(db_connection, book_name, book_price, publisher_name):
    db_cursor = db_connection.cursor()

    query = "INSERT IGNORE INTO book_info (book_name, book_price, publisher_name) VALUES (%s, %s, %s)"
    values = (book_name, book_price, publisher_name)
    
    db_cursor.execute(query, values)
    db_connection.commit()

    db_cursor.close()
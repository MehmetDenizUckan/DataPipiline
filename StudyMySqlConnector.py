from ast import boolop
import mysql.connector
import json
import logging


# Configure the logging settings (e.g., log to a file)
logging.basicConfig(filename='book_errors.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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

db_connection = connect_to_database(),




inserted_count = 0
dupelicate_count = 0
updated_count = 0

# resets the counters after going thourgh a scaraping process
def count_reset():
    global inserted_count, duplicate_count, updated_count
    inserted_count, duplicate_count, updated_count = 0, 0, 0
    return inserted_count, duplicate_count, updated_count


def insert_book_info(db_connection, book_name, book_price, publisher_name, book_info_json, image_url, product_id):
    global inserted_count 
    global dupelicate_count
    global updated_count
    try:
        with db_connection.cursor() as db_cursor:
            
            print("Total insert count:", inserted_count)
            print("Total update count:", updated_count)
            print("Total skipped dupe count:", dupelicate_count)
            
            # Check if a book with the same name exists
            query = "SELECT price, product_id FROM idefix_study_books WHERE product_id = %s"
            db_cursor.execute(query, (product_id,))
            existing_entry = db_cursor.fetchone()

            # Consume query results even if not used
            db_cursor.fetchall()


            if existing_entry:
                existing_price = existing_entry[0]
                existing_product_id = existing_entry[1]

                if float(existing_price) == float(book_price) and existing_product_id == product_id:
                    print("Skipping duplicate:", book_name,"|" ,publisher_name,"|" ,book_price)
                    dupelicate_count += 1
                    return product_id
                
                    pass
                    #update_query = "UPDATE idefix_study_books SET product_id = %s WHERE book_name = %s"
                    #values = (product_id, book_name)
                    #db_cursor.execute(update_query, values)
                    #db_connection.commit()  
                    #return product_id

                elif float(existing_price) != float(book_price) and existing_product_id == product_id:
                    print("before:\n", book_name, publisher_name, existing_price)
                    print("Updating existing entry:\n", book_name,"|" ,publisher_name,"|" ,book_price)
                    # Update existing entry
                    update_query = "UPDATE idefix_study_books SET book_info = %s, image_url = %s, price = %s, book_publisher = %s, product_id = %s WHERE book_name = %s AND book_publisher = %s"
                    db_cursor.execute(update_query, (book_info_json, image_url, book_price, publisher_name, product_id, book_name, publisher_name))
                    db_connection.commit()
                    updated_count += 1
                   
                    return product_id

            else:
                print("Inserting a new book:", book_name,"|" ,publisher_name,"|" ,book_price)
                # Insert new entry
                insert_query = "INSERT INTO idefix_study_books (book_name, price, book_publisher, book_info, image_url, is_available, product_id) " \
                               "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                values = (book_name, book_price, publisher_name, book_info_json, image_url, True, product_id)
                db_cursor.execute(insert_query, values)
                db_connection.commit()
                inserted_count +=1
                return product_id           

    except Exception as e:
        error = f"Error inserting/updating book {book_name}: {str(e)}"
        logging.error(error)
    
         
print("Total insert count:", inserted_count)
print("Total update count:", updated_count)
print("Total skipped dupe count:", dupelicate_count)



        
         
def check_product_ids_from_database(db_connection):
    with db_connection.cursor() as db_cursor:
        query = "SELECT product_id FROM idefix_study_books"
        db_cursor.execute(query)
        product_ids = [row[0] for row in db_cursor.fetchall()]

    return set(product_ids)


def delete_redacted_books(redacted_books, db_connection):
    with db_connection.cursor() as db_cursor:
        for product_id in redacted_books:
               query = "DELETE FROM idefix_study_books  WHERE product_id = %s"
               db_cursor.execute(query, (product_id,))
               db_connection.commit()
        #db_connection.close()
    print("books has been deleted succesfully")
    

    
    


    











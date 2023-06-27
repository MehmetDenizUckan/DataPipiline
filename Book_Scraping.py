# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 20:20:24 2023

@author: UCKAN
"""

import requests
from bs4 import BeautifulSoup
import time
from MySqlConnector import connect_to_database, insert_book_info

# source = requests.get('https://www.idefix.com/kitap-kultur-c-3307?sayfa=1').text


# Establish a database connection
db_connection = connect_to_database()



idefix_all_pages = 7665

# max_page = 3

def  Book_Info_Scraper(name_elements, price_elements):
    # For loop gets the book's name, publisher and prices
    for name_element, price_element in zip(name_elements, price_elements):
        book_name = name_element.contents[1].strip()
        book_publisher = name_element.contents[0].text.strip() if len(name_element.contents) > 1 else None       
        price = price_element.span.text
        
        # To remove ',' and TL from the price
        price = price.split()[0].replace(',','.')

        # Insert the data into the database
        insert_book_info(db_connection, book_name, price, book_publisher)

        # print(f' Book Name: {book_name}')
        
        # print(f' Book Publsiher: {book_publisher}')
        
        # print(f' Book Price: {price}')
        
        # print()

        
    
def Scrape_Data(max_page):
    page = 1
       
    while page<max_page: 
          
            link = f'https://www.idefix.com/kitap-kultur-c-3307?sayfa={page}'
            response = requests.get(link)
            source = requests.get(link).text
            
            if response.status_code == 200:
                # Page exists proceed with scraping 
                soup = BeautifulSoup(source,'lxml')
                # book_names = soup.find_all('div', class_='leading-5 mb-2 h-[2.625rem] line-clamp-2')
                book_names = soup.find_all('p', class_='leading-5 mb-2 h-[2.625rem] line-clamp-2')
                book_prices = soup.find_all('div', class_='flex gap-2 mb-2')
                if book_names:
                    # Scaraping Book Name, Publishers and Price
                     Book_Info_Scraper(book_names, book_prices)
                     
                     # Increasing the Page Number
                     page += 1 
        
                else:
                    print("No books were found in this page")
               
            
            else:
                print(f'Error: failled to retrive the page. Status Code:{response.status_code}')
       
    db_connection.close()            
      
            

        

inpt = input("Press 's' to start collecting data: ")

# Set a timer for how often the data will be collected
interval = 5

# While loop incase if the code wanted to be executed repatitively to collect the data in a time basis
while inpt == 's':

    # Executing the scraper
    Scrape_Data(1)
    inpt2 = input("Press 'd' to stop collectting data or 'c to continue': ")
  

    if inpt2 == 'd':
        print("The collection has been stopped succefully")
        break
    else:
        oft= int(input("How often data should be collected? :"))
        # Wait for the specified intervel
        time.sleep(oft)
        continue

        

    



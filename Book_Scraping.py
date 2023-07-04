# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 20:20:24 2023

@author: UCKAN
"""

import requests
from bs4 import BeautifulSoup , Tag
import time
from MySqlConnector import connect_to_database, insert_book_info
import json

# source = requests.get('https://www.idefix.com/kitap-kultur-c-3307?sayfa=1').text


# Establish a database connection
db_connection = connect_to_database()



idefix_all_pages = 7665


def href_collecter(a_elements):
    hrefs = []  # Create a list to store collected href values
    for a_element in a_elements:
        href = a_element.get('href')
        if href:
            hrefs.append(href)  # Add the href to the list
    return hrefs  # Return the list of href values


def h1_collector(href):
    link2 = f'https://www.idefix.com{href}'
    response2 = requests.get(link2)
    source2 = response2.text
    
    if response2.status_code == 200:
     soup2 = BeautifulSoup(source2, 'lxml')
     h1_element = soup2.find('h1', class_='text-[1.375rem] font-medium leading-[1.875rem] mb-[0.375rem]')
     if h1_element:
         book_name_parts = [element.strip() for element in h1_element.contents if isinstance(element, str)]
         book_name = ' '.join(book_name_parts)
         book_name = book_name.strip()
         book_name = book_name.strip('-')
         
         book_publisher = "N/A"
         author = "N/A"
         
         a_elements = h1_element.find_all('a')
         for a_element in a_elements:
             text = a_element.get_text(strip=True)
             if "/yayinevi/" in a_element.get('href'):
                 book_publisher = text
             elif "/yazar/" in a_element.get('href'):
                 author = text

         return book_name, book_publisher, author
     
    return None, None, None  # Return None values if no valid h1_element is found     
      
def book_detailed_info_collector(href):
    link3 = f'https://www.idefix.com{href}'
    response3 = requests.get(link3)
    source3 = response3.text
    
    if response3.status_code == 200:
     soup3 = BeautifulSoup(source3, 'lxml')
     main_div_element = soup3.find('div', class_='grid grid-cols-2 lg:grid-cols-3 gap-x-8 lg:gap-x-[2.813rem] gap-y-5 mb-8')
     if main_div_element:
         upper_span_elements = main_div_element.find_all('span', class_='leading-5 xl:text-base lg:text-tiny')
         book_info1 = [element1.get_text(strip=True) for element1 in upper_span_elements if isinstance(element1, Tag)]
         book_info1.pop(1) # Popped the second element because it was about the auother of the book and I already scraped the author in an another function
         
         bottom_span_elements = main_div_element.find_all('span', class_='font-medium leading-5 xl:text-base lg:text-tiny')
         book_info2 = [element2.get_text(strip=True) for element2 in bottom_span_elements if isinstance(element2, Tag)]
         
         # Combine the lists into a dictionary
         comp_book_info = {key: value for key, value in zip(book_info1, book_info2)}

         return comp_book_info
         
def price_collector(href):
    link4 = f'https://www.idefix.com{href}'
    response4 = requests.get(link4)
    source4 = response4.text
    
    if response4.status_code == 200:
     soup4 = BeautifulSoup(source4, 'lxml')
     price_element = soup4.find('span', class_='text-[1.125rem] xl:text-[1.375rem] leading-[1.875rem] font-medium')
     price = price_element.get_text(strip=True)
     return price
            


        
    
def Scrape_Data(max_page):
    page = 1
 
    while page<=max_page: 
          
            link = f'https://www.idefix.com/kitap-kultur-c-3307?sayfa={page}'
            response = requests.get(link)
            source = requests.get(link).text
            
            if response.status_code == 200:
                # Page exists proceed with scraping 
                soup = BeautifulSoup(source,'lxml')
                a_elements = soup.find_all('a', class_='w-full h-full absolute top-0 left-0 bottom-0 right-0 z-10 cursor-pointer')
                hrefs = href_collecter(a_elements)  # Get the list of href values
                if a_elements:
                    for href in hrefs:
                        book_name, book_publisher, author = h1_collector(href)
                        price = price_collector(href)
                        comp_book_info = book_detailed_info_collector(href)

                        # Convert the dictionary to a JSON string
                        comp_book_info_json = json.dumps(comp_book_info)

                        # Call the insert_book_info function with the correct arguments
                        insert_book_info(db_connection, book_name, author ,price, book_publisher, comp_book_info_json)
                        
                    page += 1  # Increment the page value for the next iteration
                
                else:
                    print("No books were found in this page")
            
                   
            
            else:
                print(f'Error: failled to retrive the page. Status Code:{response.status_code}')


    db_connection.close()            
      
            

        



# Set a timer for how often the data will be collected
interval = 5

# While loop incase if the code wanted to be executed repatitively to collect the data at a time basis
while True:

    inpt = input("Press 's' to start collecting data or 'd' to stop: ")

    if inpt.lower() == 's':
        # Executing the scraper for one page
        Scrape_Data(5)
        inpt2 = input("Press 'd' to stop collecting data or 'c' to continue: ")

        if inpt2.lower() == 'd':
            print("The collection has been stopped successfully")
            break

        else:
            oft = int(input("How often data should be collected (in seconds)? :"))
            # Wait for the specified interval
            time.sleep(oft)
            continue

    elif inpt.lower() == 'd':
        print("The collection has been stopped successfully")
        break

    else:
        print("Invalid input. Please enter 's' to start or 'd' to stop.")
        continue

        

    



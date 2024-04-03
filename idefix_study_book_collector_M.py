# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 20:20:24 2023

@author: UCKAN
"""

import requests
from bs4 import BeautifulSoup, Tag
from requests_html import HTMLSession
import time
import json
import re
from cachecontrol import CacheControl
from StudyMySqlConnector import connect_to_database, insert_book_info, check_product_ids_from_database,delete_redacted_books 
import logging
import mysql.connector
import retrying
import cProfile

logging.basicConfig(filename='idefix_book_errors.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# source = requests.get('https://www.idefix.com/kitap-kultur-c-3307?sayfa=1').text

class IdefixScraper:
    def __init__(self, max_page, db_connection, interval=0):
        self.max_page = max_page
        self.db_connection = db_connection
        self.interval = interval
        self.session = CacheControl(requests.session()) # Added Cache control tht refreshed every 15 mins
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10))
        
    @retrying.retry(
        wait_exponential_multiplier=1000,  # Wait for 2^x * 1000 milliseconds between retries
        wait_exponential_max=10000,
        stop_max_attempt_number=3)
  
    def fetch_page(self, page):   # retry func if ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
        response = self.session.get(f'https://www.idefix.com/universiteye-hazirlik-c-3306279440?sayfa={page}')
        return response

    def scrape_data(self):
        while True:
            page = 1
            product_ids = []
            while page <= self.max_page:
                try:
                    response = self.fetch_page(page)
                except requests.exceptions.RequestException as e:
                            print(f"Error: {e}")
                            logging.error(e)
                            time.sleep(5)  # Add a delay before retrying
                            continue
                start_time = time.time() 
                source = response.text

                if response.status_code == 200:
                    soup = BeautifulSoup(source, 'lxml')
                    self.a_elements = soup.find_all('a', class_='w-full h-full absolute top-0 left-0 bottom-0 right-0 z-20 cursor-pointer')
                    print(f'https://www.idefix.com/universiteye-hazirlik-c-3306279440?sayfa={page}')
                    print(f'Now scraping page: {page}')

                    if self.a_elements:
                         product_ids = self.process_books(self.a_elements)

                else:
                    print(f'Error: failed to retrieve the page. Status Code: {response.status_code}')

                page += 1
                elapsed_time = time.time() - start_time
                print(f"Page took {"{:.2f}".format(elapsed_time)} seconds")
                time.sleep(0.25)

            print("Reached max page.")
            return product_ids
            
           
 

    def process_books(self, a_elements):
        a = 1
        product_ids = {}
        for href in self.href_collector(a_elements):
            response = self.session.get(f'https://www.idefix.com{href}')
            source = response.text
            soup = BeautifulSoup(source, 'lxml')
            book_name, book_publisher = self.h1_collector(soup)
            price = self.price_collector(soup)
            comp_book_info = self.book_detailed_info_collector(soup)

            try:
                image_url, product_id = self.image_url_and_product_id_collector(soup)
            except Exception as e:
                print("an error occured", e)

            comp_book_info_json = json.dumps(comp_book_info)
            try:
                product_id = insert_book_info(self.db_connection, book_name, price, book_publisher, 
                                              comp_book_info_json, image_url, product_id)
                
                book_dict = {'key':book_name ,'value': product_id}
                product_ids[product_id] = book_dict 
                print(f'Books Collected for this page so far is: {a}')
                a+=1
            except Exception as e:
                print("an error occured", e)    
            
        return product_ids
    

    def check_product_ids_in_database(self):
        print("invoked")
        diff = {}
        try:
            db_product_ids = check_product_ids_from_database(self.db_connection)
            scraped_product_ids = set(self.scrape_data().keys())

        # Find product IDs in the database but not in the scraped data
            diff_product_ids = scraped_product_ids - db_product_ids 

            print("Product IDs in the database but not in scraped data:", diff_product_ids)
        
            # Calculate the total count of books to be deleted
            total_books_to_delete = len(diff_product_ids)

            if total_books_to_delete:
                print(f"Now deleting: {total_books_to_delete} books")
                delete_redacted_books(diff_product_ids, self.db_connection)
            else:
                print("No books found in the database that are not in the scraped data.")
        except Exception as e:
            print("An error occurred:", e)

        

    def image_url_and_product_id_collector(self, soup):
        image_element = soup.find('img', alt='product image')
        try:

            image_url = image_element.get('src')
            segments = image_url.split("/")
            product_id = segments[7]
            
        except Exception as e:
             print("an error occured with the image url:", str(e),)
             image_url = 'N/A'
             product_id = 'N/A'
             logging.error(e)
        if image_url and product_id:
            return image_url, product_id


    def href_collector(self, a_elements):
        hrefs = [a_element.get('href') for a_element in a_elements if a_element.get('href')]
        return hrefs
    

    def h1_collector(self, soup):
        h1_element = soup.find('h1', class_='text-[1.375rem] font-medium leading-[1.875rem] mb-[0.375rem]')
        if h1_element:
            book_name_parts = [element.strip() for element in h1_element.contents if isinstance(element, str)]
            book_name = ' '.join(book_name_parts).strip('-')
            book_publisher = "N/A"

            for a_element in h1_element.find_all('a'):
                text = a_element.get_text(strip=True)
                if "/yayinevi/" in a_element.get('href'):
                    book_publisher = text
                else:
                    span_element = soup.find('span', class_='text-[1.375rem] leading-[1.875rem] font-semibold cursor-pointer')
                    book_publisher = span_element.get_text(strip=True)

            return book_name, book_publisher
        else:
            return None, None

    def book_detailed_info_collector(self, soup):
        main_div_element = soup.find('div', class_='grid grid-cols-2 lg:grid-cols-3 gap-x-8 lg:gap-x-[2.813rem] gap-y-5 mb-8')
        if main_div_element:
            upper_span_elements = main_div_element.find_all('span', class_='leading-5 xl:text-base lg:text-tiny')
            book_info1 = [element1.get_text(strip=True) for element1 in upper_span_elements if isinstance(element1, Tag)]
            if len(book_info1) >= 2:
                book_info1.pop(1)

            bottom_span_elements = main_div_element.find_all('span', class_='font-medium leading-5 xl:text-base lg:text-tiny')
            book_info2 = [element2.get_text(strip=True) for element2 in bottom_span_elements if isinstance(element2, Tag)]

            comp_book_info = {key: value for key, value in zip(book_info1, book_info2)}
            return comp_book_info

    def price_collector(self, soup):
        price_element = soup.find('span', class_='text-[1.125rem] xl:text-[1.375rem] leading-[1.875rem] font-medium')
        if price_element is None:
            book_name, book_publisher = self.h1_collector(soup)
            print("Couldn't find the price", price_element)
            print("here are the book name and book author: ", book_name , book_publisher)
            return 'N/A'

        price = price_element.get_text(strip=True)
        cleaned_price = price.replace("TL", "").strip()

        if "." not in cleaned_price:
            cleaned_price += ".00"
        else:
            cleaned_price = cleaned_price.replace(".", "").replace(",", ".")

        s_price = re.split(r'[,.]', cleaned_price)

        try:
            final_price = "{:.2f}".format(float(s_price[0] + "." + s_price[1]))
        except ValueError:
            print("Invalid price format:", cleaned_price)
            return None

        return final_price
    
    

    def close_resources(self):
        self.session.close()
        
 
 
 
          
def start_code(inpt1: str, scraper):
    if inpt1 == 's':
        start_time = time.time() 
        scraper.check_product_ids_in_database()
        elapsed_time = time.time() - start_time
        print(f"Whole scraping took {elapsed_time:.2f} seconds")
    elif inpt1 == 'c':
        start_time = time.time() 
        oft = int(input("How often data should be collected (in seconds)? :"))
        scraper.check_product_ids_in_database()
        elapsed_time = time.time() - start_time
        print(f"Whole scraping took {elapsed_time:.2f} seconds")
        while True:
            time.sleep(oft)
                
            start_time = time.time() 
            scraper.check_product_ids_in_database()
            elapsed_time = time.time() - start_time
            print(f"Whole scraping took {elapsed_time:.2f} seconds")
            
    else:
        print("Invalid input. Please enter 's' to start, 'd' to stop, or 'c' to continue.")


def main():
    max_page = 170  # Set your desired max_page value
    db_connection = connect_to_database()  # Replace with your connect_to_database function
    scraper = IdefixScraper(max_page, db_connection)

    while True:
        user_input = input("Press 's' to start the scraping or 'd' to close the program, press 'c' (idefix): ").lower()

        if user_input == 'd':
            break
        elif user_input == 's' or user_input == 'c':
            start_code(user_input, scraper)
        else:
            print("Invalid input. Please enter 's' to start, 'd' to stop, or 'c' to continue.")

if __name__ == "__main__":
    main()


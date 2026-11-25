#imports
from dataclasses import dataclass, field
import re
import pandas as pd
#from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
import time
from datetime import datetime
import logging

#logging levels
#debug, error, info, warning, critical

# <class 'seleniumbase.undetected.cdp_driver.element.Element'>
#log = logging.getLogger
# last_height = new_height
#         log.info("  Scrolled → page height %d px", new_height)

#guitar dataclass for simplicity
@dataclass
class Guitar:
    product_name:   str
    price:          float
    condition:      str
    reverb_bump:    bool = False
    free_shipping:  bool = False
    great_value:    bool = False
    price_drop:     str = ""
    url:            str = ""
    scraped:        datetime = field(default_factory=lambda: datetime.now())




#variables
driver = Driver(uc=True)
#link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page=1" <- old fender one
#link =  unsold ->"https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make[]=fender&make[]=prs&make[]=gibson&make[]=ibanez&make[]=squier&make[]=epiphone&country_of_origin=US"
link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?show_only_sold=true&preferred_seller=true&page=450"
page_number = 1
keep_scraping = True
guitars = []




#functions
# def iterate_page(page_number) -> str:
#     base_link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page="
#     page_number += 1
#     iterated_link = f"{base_link} + {page_number}"
#     return iterated_link



def parse_price(raw: str) -> float:
    clean = re.sub(r"[$,]", "", raw)
    try:
        return float(clean) if clean else None
    except ValueError:
        return None



def parse_discount(raw: str) -> float:
    clean = re.sub(r"[$, off]", "", raw)
    try:
        return float(clean) if clean else None
    except ValueError:
        return None

# def scroll_to_bottom(driver) -> None:
#     last_height = driver.execute_script("return document.body.scrollHeight")
#     while True:
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(2)
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break
#         last_height = new_height



def scroll_to_bottom(driver, downum: int):
    for i in range(downum):
        driver.execute_script("window.scrollBy(0,500)")
        driver.sleep(0.2)



def scrape_grid(driver, link) -> list:
    global keep_scraping
    page_guitars = []
    if page_number == 1:
        driver.uc_open_with_reconnect(link, reconnect_time=4)
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "rc-listing-grid")
            )
        )
        time.sleep(3)
        if page_number == 1:
            scroll_to_bottom(driver, downum=10)
        else:
            scroll_to_bottom(driver, downum=9)
        time.sleep(2)
    except:
        keep_scraping = False
        return []

    try: 
        grid_element = driver.find_element(By.CLASS_NAME, "rc-listing-grid")
        grid_list = grid_element.find_elements(By.CLASS_NAME, "rc-listing-grid__item")
    except:
        grid_list = []

    for listing in grid_list:
        try:
            nudge_check = listing.find_elements(By.CLASS_NAME, "rc-nudge")
        except:
            nudge_check = []

        nudge_check = len(nudge_check) > 0

        try:
            #price_drop = listing.find_element(By.CSS_SELECTOR, "span[class='td-line-through mr-space']").text'
            price_drop = listing.find_element(By.CLASS_NAME, "rc-price-block__discount-description").text
            price_drop = parse_discount(price_drop)
            #price_drop = price_drop - price
            price_drop = str(price_drop)
        except:
            price_drop = ""

        try:
            product_name = listing.find_element(By.CLASS_NAME, "rc-listing-card__title").text
        except:
            product_name = "title not workin"

        try:
            price = listing.find_element(By.CLASS_NAME, "rc-price-block__price").text
            price = parse_price(price)
        except:
            price = "price not workin"

        try:
            condition = listing.find_element(By.CLASS_NAME, "rc-listing-card__condition").text
        except:
            condition = "condition not workin"

        try:
            url = listing.find_element(By.CSS_SELECTOR, "meta[itemprop='url']")
            url = url.get_attribute("content")
        except:
            url = "url not workin"

        try:
            reverb_bump = listing.find_element(By.CLASS_NAME, "text-eyebrow-300.fg-color-text-accent").text
            if reverb_bump:
                reverb_bump = True
            else:
                reverb_bump = False
        except:
            reverb_bump = False

        clean_nudges = []

        if nudge_check:
            nudges = listing.find_elements(By.CLASS_NAME, "rc-nudge__icon__label")
            for nudge in nudges:
                nudge = nudge.text
                if "Free" in nudge:
                    nudge = "Free Shipping"
                clean_nudges.append(nudge)

        free_shipping = False
        great_value = False
                
        if nudge_check:
            if "Free Shipping" in clean_nudges:
                free_shipping = True
            if "Great Value" in clean_nudges:
                great_value = True

        row = Guitar(
            product_name=product_name,
            price=price,
            condition=condition,
            reverb_bump=reverb_bump,
            free_shipping=free_shipping,
            great_value=great_value,
            price_drop=price_drop,
            url=url
        )
        page_guitars.append(row)

    return page_guitars




#pathing
scrape_number = 2
scrape_name = "sold_grid_scrape"

scrape_csv = f"{scrape_name}{scrape_number}.csv"
path = "guitar_data_analysis/data/"
final_path = f"{path}{scrape_csv}"




def main():
    global page_number
    global keep_scraping
    #link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page=1"
    
    while keep_scraping == True:
        page_guitars = scrape_grid(driver, link)
        
        if len(page_guitars) == 0:
            print("No guitars to scrape")
            keep_scraping = False
            break

        # if page_number == 10:
        #     print("Ending Scraping at 10")
        #     keep_scraping = False

        guitars.extend(page_guitars)



        driver.click_if_visible("a:contains('Next')")
        page_number += 1
        print(f"\nCurrent Page Number:  {page_number}")
        time.sleep(5)
    print("Done Scraping.")

    df = pd.DataFrame(guitars)
    df.to_csv(final_path, index=False)


if __name__ == "__main__":
    main()




driver.quit()

'''Fender,Gibson,PRS,Ibanez,Squier,Epiphone,Jackson,ESP LTD,Schecter,Charvel,Gretsch,Yamaha,EVH,G&L,Dean,Ernie Ball Music Man,ESP,B.C. Rich,Suhr,Reverend'''


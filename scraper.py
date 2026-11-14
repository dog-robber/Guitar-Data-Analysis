#imports
from dataclasses import dataclass
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time



#guitar dataclass for simplicity
@dataclass
class Guitar:
    product_name: str
    price: float
    condition: str
    reverb_bump: bool = False
    free_shipping: bool = False
    great_value: bool = False
    price_drop: str = ""
    url:str = ""


#variables
driver = webdriver.Chrome()
link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page=1"
page_number = 1
keep_scraping = True
guitars = []


#functions
def iterate_page(page_number) -> str:
    base_link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page="
    page_number += 1
    iterated_link = f"{base_link} + {page_number}"
    return iterated_link


def parse_price(raw: str) -> float:
    clean = re.sub(r"[$,.]", "", raw)
    try:
        return float(clean) if clean else None
    except ValueError:
        return None


def scroll_to_bottom(driver: webdriver.Chrome) -> None:
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def scrape_page(driver: webdriver.Chrome, link) -> None:
    global keep_scraping
    driver.get(link)
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "rc-listing-grid")
            )
        )
        time.sleep(3)
        scroll_to_bottom(driver)
        time.sleep(2)
    except:
        pass

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
            price_drop = listing.find_element(By.CLASS_NAME, "rc-price-block__discount-description").text
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
        guitars.append(row)

    if len(grid_list) > 0:
        keep_scraping = True
    else:
        keep_scraping = False


def main():
    global page_number

    first_link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page=1"
    scrape_page(driver, first_link)

    while keep_scraping == True:
        new_page = iterate_page(page_number)
        scrape_page(driver, new_page)

    print("Done Scraping.")

main()

df = pd.DataFrame(guitars)
df.to_csv("data.csv", index=False)

driver.quit()
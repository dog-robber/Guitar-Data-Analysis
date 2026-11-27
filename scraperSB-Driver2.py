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
    base_price:     float
    shipping_price: float
    total_price:    float
    condition:      str
    seller:         str
    location:       str
    brand:          str
    decade:         str
    # reverb_bump:    bool = False
    free_shipping:  bool = False
    great_value:    bool = False
    price_drop:     str = ""
    url:            str = ""
    scraped:        datetime = field(default_factory=lambda: datetime.now())

@dataclass
class Link:
    url:        str
    brand:      str
    decade:     str


#variables
def build_driver() -> Driver:
    driver = Driver(uc=True)
    return driver
#link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page=1" <- old fender one
#link =  unsold ->"https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make[]=fender&make[]=prs&make[]=gibson&make[]=ibanez&make[]=squier&make[]=epiphone&country_of_origin=US"
#link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?show_only_sold=true&preferred_seller=true&page=450"


test_link = "https://reverb.com/b/fender/electric-guitars--864?show_only_sold=true&trait_values[]=8e61e6c8-037f-4382-bba2-3f32e9b8266d&trait_values[]=0f9004ea-aa92-46a6-b997-bb83e7b21c86&trait_values[]=ceabf42c-9797-4387-96ac-495aad620205&trait_values[]=d006e9b9-016d-4c0b-b65e-01d3fcc8a877&decades=202"
#they create hashes, so i can't use a bunch of links with custom filters

test_link2 = "https://reverb.com/b/fender/electric-guitars/solid-body--1504?show_only_sold=true&decades=202"


page_number = 1
keep_scraping = True
guitars = []

brands = [
    "Fender",
    "Gibson",
    "Ibanez",
    "PRS",
    "Squier",
    "Epiphone"
]

decades = {
    "2020s":202,
    "2010s":201,
    "2000s":200,
    "1990s":199,
    "1980s":198,
    "1970s":197,
    "1960s":196,
    "1950s":195
}

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



def parse_shipping(raw: str) -> float:
    clean = re.sub(r"[$, Shipping]", "", raw)
    try:
        return float(clean) if clean else None
    except ValueError:
        return None



def build_links(brands: list, decades: dict) -> list:
    links = []
    for brand in brands:
        for display, search_value in decades.items():
            constructed_link = f"https://reverb.com/b/{brand.lower()}/electric-guitars/solid-body--1504?show_only_sold=true&decades={search_value}"
            display = str(display)
            link_data = Link(
                url=constructed_link,
                brand=brand,
                decade=display
                )
            links.append(link_data)
    return links



def click_list_view() -> None:
    driver.click_if_visible("button[aria-label='List View']", timeout=3)

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



def scrape_list(driver, link) -> list:
    global keep_scraping
    page_guitars = []

    link_object = link
    link = link.url

    if page_number == 1:
            driver.uc_open_with_reconnect(link, reconnect_time=4)
    try:
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "ul[class='rc-listing-grid']")
            )
        )
        time.sleep(2) #previously 3
        if page_number == 1:
            click_list_view()
            time.sleep(2)
            scroll_to_bottom(driver, downum=6)
        else:
            scroll_to_bottom(driver, downum=5)
        time.sleep(1.5) #previously 2
    except:
        keep_scraping = False
        return []

    try: 
        grid_element = driver.find_element(By.CSS_SELECTOR, "ul[class='rc-listing-grid']")
        grid_list = grid_element.find_elements(By.CSS_SELECTOR, "li[class='rc-listing-grid__item rc-listing-grid__item--span-all']")
    except:
        grid_list = []

    for listing in grid_list:
        try:
            nudge_check = listing.find_elements(By.CLASS_NAME, "rc-nudge")
            #same?
        except:
            nudge_check = []

        nudge_check = len(nudge_check) > 0

        try:
            #price_drop = listing.find_element(By.CSS_SELECTOR, "span[class='td-line-through mr-space']").text'

            price_drop = listing.find_element(By.CLASS_NAME, "rc-price-block")
            price_drop = price_drop.find_element(By.CLASS_NAME, "visually-hidden").text
            match = re.search(r"^(?:[^$]*\$\d+(?:\.\d+)?){2}[^$]*\(\$(\d+(?:\.\d+)?)\s", price_drop)

            if match:
                price_drop = str(match.group(1)) if match else ""

            if "$" in price_drop:
                price_drop = ""
            #price_drop = parse_discount(price_drop)

            #price_drop = price_drop - price

            #find what regex keeps the parenthesis number  -  Originally $999, now $899.10 ($99.90 price drop)
            #must change
        except:
            price_drop = ""

        try:
            product_name = listing.find_element(By.CLASS_NAME, "rc-listing-row-card__title").text
            #new
        except:
            product_name = "title not workin"

        try:
            base_price = listing.find_element(By.CLASS_NAME, "rc-price-block__price").text
            base_price = parse_price(base_price)
            #same, but needs shipping and total
        except:
            base_price = "price not workin"

        try:
            shipping_price = listing.find_element(By.CLASS_NAME, "rc-price-block__shipping").text
            shipping_price = parse_shipping(shipping_price)
        except:
            shipping_price = 0

        try:
            total_price = base_price + shipping_price
            #new
        except:
            total_price = "total price broken"

        try:
            seller = listing.find_element(By.CSS_SELECTOR, "a.rc-shop-info__name").text
            # seller = seller.get_attribute("href")
            # seller = seller.text
            #new, probably wont work
        except:
            seller = "seller broken"

        try:
            location = listing.find_element(By.CLASS_NAME, "rc-shop-info__location").text
            #new
        except:
            location = "location broken"

        try:
            condition = listing.find_element(By.CLASS_NAME, "rc-listing-row-card__condition").text
            #changed to include '-row'
        except:
            condition = "condition not workin"

        try:
            url = listing.find_element(By.CSS_SELECTOR, "meta[itemprop='url']")
            url = url.get_attribute("content")
            #same
        except:
            url = "url not workin"

        # try:
        #     reverb_bump = listing.find_element(By.CLASS_NAME, "text-eyebrow-300.fg-color-text-accent").text
        #     if reverb_bump:
        #         reverb_bump = True
        #     else:
        #         reverb_bump = False
        # except:
        #     reverb_bump = False

        clean_nudges = []

        if nudge_check:
            #same
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
            base_price=base_price,
            shipping_price=shipping_price,
            total_price=total_price,
            condition=condition,
            seller=seller,
            location=location,
            brand=link_object.brand,
            decade=link_object.decade,
            #reverb_bump=reverb_bump,
            free_shipping=free_shipping,
            great_value=great_value,
            price_drop=price_drop,
            url=url
        )
        page_guitars.append(row)

    return page_guitars


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
scrape_number = 3
scrape_name = "sold_list_scrape"

scrape_csv = f"{scrape_name}{scrape_number}.csv"
#path = "guitar_data_analysis/data/"
path = "data/"
final_path = f"{path}{scrape_csv}"

links = build_links(brands, decades)

driver = build_driver()

def main():
    global page_number
    global keep_scraping
    global driver
    #link = "https://reverb.com/cat/electric-guitars/solid-body/6-string--522?make=fender&page=1"
    for link in links:
        keep_scraping = True
        page_number = 1
        print(f"Now Scraping:  {link.decade} {link.brand}")
        while keep_scraping == True:
            page_guitars = scrape_list(driver, link)
            
            
            # if len(page_guitars) == 0:
            #     print("No guitars to scrape")
            #     keep_scraping = False
            #     break
            guitars.extend(page_guitars)


            # if page_number == 10:
            #     print("Ending Scraping at 10")
            #     keep_scraping = False
            #     break

            



            driver.click_if_visible("a:contains('Next')")
            page_number += 1
            print(f"\nCurrent Page Number:  {page_number}")
            time.sleep(1.5)

        # if page_number == 10:
        #     print("Ending Scraping at 10")
        #     break
        
        print(f"Done Scraping:  {link.decade} {link.brand}")
        driver.quit()
        driver = build_driver()





if __name__ == "__main__":
    main()


df = pd.DataFrame(guitars)
df.to_csv(final_path, index=False)
# links = build_links(brands, decades)
# for link in links:
#     print(f"\nLink: {link}")

# print(f"\n\nLength: {len(links)}")

driver.quit()

'''Fender,Gibson,PRS,Ibanez,Squier,Epiphone,Jackson,ESP LTD,Schecter,Charvel,Gretsch,Yamaha,EVH,G&L,Dean,Ernie Ball Music Man,ESP,B.C. Rich,Suhr,Reverend'''


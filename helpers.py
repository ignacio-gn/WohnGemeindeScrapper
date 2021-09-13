import logging
import os
import time

import xlsxwriter
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

# ===============================================
# SETUP =========================================
# ===============================================


# Setup ###########################################################################################
def setup() -> None:
    # Setup os
    os.chdir("/Users/Igo/Desktop/Python Programs/WohnGemeindeScrapper")

    # Setup log
    logging.basicConfig(filename="logs.txt", level=logging.DEBUG,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    time1 = f"""{time.localtime().tm_year}, 
                {time.localtime().tm_mday} of {time.localtime().tm_mon}, 
                time is {time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}."""
    logging.critical(f'Start of program, at time {time1}')


# ===============================================
# BROWSER =======================================
# ===============================================

# Get valid offers in drivers current page ########################################################
def get_pages_valid_offers(driver: webdriver,
                           offer_class: str,
                           price_xpath: str,
                           settings: dict[str, int]):
    # Local variables
    offers_list = driver.find_elements_by_class_name(offer_class)
    output = []
    # Populate output
    for offer in offers_list:
        try:
            local_price = clean_price(offer.find_element_by_xpath(price_xpath).text)
        except NoSuchElementException:
            return None
        if settings["min"] <= local_price <= settings["max"]:
            local_link = offer.find_element_by_xpath("./div/div[2]/div[1]/div[1]/h3/a").get_attribute("href")
            output.append(local_link)

    return output


# Get next page's link ############################################################################
def get_next_page_url(driver: webdriver) -> str:
    outp = None
    i = 40
    while i > 0:
        try:
            outp = driver.find_element_by_css_selector(
                f".col-md-9 > nav:nth-child(1) > ul:nth-child(1) > li:nth-child({i}) > a:nth-child(1)"
            ).get_attribute("href")
        except NoSuchElementException:
            i -= 1
            continue
        break
    return outp


# Click the accept cookies button, if needed ######################################################
def approve_cookies(driver: webdriver) -> None:
    html_body = driver.find_element_by_xpath("/html/body")
    # Cookies should be accepted
    if html_body.get_attribute("style") != "":
        button = driver.find_element_by_css_selector(".cmpboxbtnyes")
        button.click()


# Collect offer's information #####################################################################
def get_offer(driver: webdriver) -> dict[str: str]:
    output = dict()
    driver.implicitly_wait(1)
    # Populate dictionary
    try:
        output["price"] = driver.find_element_by_css_selector("#graph_wrapper > div:nth-child(2) > label:nth-child(1)").text
    except NoSuchElementException:
        return None
    output["size"] = driver.find_element_by_css_selector("div.print_inline:nth-child(2) > h2:nth-child(1)").text
    output["url"] = driver.current_url
    # Available since
    # FIXME
    try:
        output["av_since"] = driver.find_element_by_css_selector(
            "div.row:nth-child(7) > div:nth-child(3) > p:nth-child(2) > b:nth-child(1)"
        ).text
    except NoSuchElementException:
        return None
    # Available until
    try:
        output["av_until"] = driver.find_element_by_css_selector(
            "div.row:nth-child(7) > div:nth-child(3) > p:nth-child(2) > b:nth-child(3)"
        ).text
    except NoSuchElementException:
        output["av_until"] = '-'
    # Misc
    try:
        misc = driver.find_element_by_css_selector("div.row:nth-child(13) > div:nth-child(1) > div:nth-child(2)").text
    except NoSuchElementException:
        try:
            misc = driver.find_element_by_css_selector(
                "div.row:nth-child(14) > div:nth-child(1) > div:nth-child(2)"
            ).text
        except NoSuchElementException:
            misc = ""
    output["misc"] = misc
    # Whitespace
    output[""] = ""
    # Info
    headers = driver.find_elements_by_class_name("wordWrap")
    output["info"] = dict()
    for i in range(len(headers)):
        # header = headers[i].find_element_by_xpath("h3").text  # FIXME
        output["info"][i] = headers[i].find_element_by_css_selector("p.freitext").text
    # Mitbewohner
    try:  # FIXME: this is awful but its the only way it works :|
        output["mitbewohner"] = driver.find_element_by_css_selector(".headlineContent > span:nth-child(2)")\
            .get_attribute("title")
    except NoSuchElementException:
        try:
            output["mitbewohner"] = driver.find_element_by_css_selector("#sliderTopTitle > span:nth-child(2)")\
                .get_attribute("title")
        except NoSuchElementException:
            try:
                output["mitbewohner"] = driver.find_element_by_css_selector("#sliderTopTitle > span:nth-child(2)") \
                    .get_attribute(".headline-detailed-view-title > span:nth-child(2)")
            except NoSuchElementException:
                try:
                    output["mitbewohner"] = driver.find_element_by_xpath("/html/body/div[4]/div[2]/div[6]/div[1]/div[1]/div/div[4]/div/h3/span") \
                        .get_attribute(".headline-detailed-view-title > span:nth-child(2)")
                except NoSuchElementException:
                    output["mitbewohner"] = driver.find_element_by_css_selector(".headline-detailed-view-title > span:nth-child(2)") \
                        .get_attribute(".headline-detailed-view-title > span:nth-child(2)")


    # Return formatted output
    return output


# ===============================================
# XLSX WRITER ===================================
# ===============================================

# Create writer, basic setup ######################################################################
def create_workbook(title: str) -> tuple[xlsxwriter.Workbook, xlsxwriter.workbook.Worksheet]:
    # File setup
    workbook = xlsxwriter.Workbook(f"{title}.xlsx")
    worksheet = workbook.add_worksheet()

    # Header
    row = 0
    col = 0
    headers = [
        "PRICE",
        "SIZE",
        "MITBEWOHNER",
        "",
        "AV. SINCE",
        "AV. UNTIL",
        "",
        "URL",
        "",
        "MISC",
        "INFO"
    ]
    for i in range(len(headers)):
        worksheet.write(row, col, headers[i])
        col += 1

    # Return output
    return workbook, worksheet


# Write gathered data into workbook ###############################################################
def write_data(worksheet: xlsxwriter.workbook.Worksheet, data_dict: dict[str: str], row: int) -> None:
    col_map = [
        "price",
        "size",
        "mitbewohner",
        "",
        "av_since",
        "av_until",
        "",
        "url",
        "",
        "misc",
    ]
    for i in range(len(col_map)):
        worksheet.write(row, i, data_dict[col_map[i]])
    for i in range(len(data_dict["info"])):
        worksheet.write(row, i + len(col_map), data_dict["info"][i])  # FIXME


# ===============================================
# STRING PROCESSING =============================
# ===============================================

# Clean price #####################################################################################
def clean_price(text: str) -> int:
    """ Format: "450 $"  -> 450 """
    return int(text.split(" ")[0])


# Get input #######################################################################################
def get_input() -> dict[str, int]:
    while True:
        price_min = None
        price_max = None
        ppl_min = None
        ppl_max = None
        try:
            price_min = int(input("Lowest price: "))
            price_max = int(input("Highest price: "))
            ppl_min = int(input("Min size: "))
            ppl_max = int(input("Max size: "))
        except TypeError:
            print("Please enter a valid integer")
            continue
        break
    return {
            "min": price_min,
            "max": price_max,
            "ppl_min": ppl_min - 1,
            "ppl_max": ppl_max - 1
            }

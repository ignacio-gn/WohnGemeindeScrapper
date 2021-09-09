"""
TODO
- Continue execution with errors in data collection
- Fix occasional error in get_offer
- Automatically detect on which page offers are sold-out
- Check if Misc is working
- Add option to ignore date limited offers
- Fix date limit to offer showing last online time
"""

from helpers import *
from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException

if __name__ == "__main__":
    # Setup
    setup()

    # Get input
    settings = get_input()

    # Create browser object
    browser = webdriver.Firefox(executable_path="/usr/local/Cellar/geckodriver/0.28.0/bin/geckodriver")
    browser.get(f"https://www.wg-gesucht.de/wg-zimmer-in-Munchen.90.0.1.0.html?offer_filter=1&city_id=90&sort_column=0&noDeact=1&categories%5B%5D=0&rent_types%5B%5D=0&rMax={settings['max']}&radDis=10000&wgMnF={settings['ppl_min']}&wgMxT={settings['ppl_max']}&wgAge=18")

    # Accept cookies, if needed
    approve_cookies(browser)

    # Create workbook and worksheet objects
    workbook, worksheet = create_workbook("alpha")

    # MAIN LOOP
    pages = 1
    i = 1
    while pages < 15:
        # Find next page
        next_page = get_next_page_url(browser)
        # Check issues
        if next_page is None:
            print("Issues in next_data")

        # Find offers
        valid_offers = get_pages_valid_offers(driver=browser,
                                              offer_class="offer_list_item",
                                              price_xpath="./div/div[2]/div[2]/div[1]/b",
                                              settings=settings
                                              )
        if valid_offers is not None:
            num_offers = len(valid_offers)
        else:
            num_offers = 0

        # Check if there were issues
        if valid_offers == None:
            print("Issues in valid_offers")
            continue

        # Iterate through offers
        for local_idx in range(num_offers):
            print(f" Iteration {local_idx} of {num_offers}")
            # Go to offer
            browser.get(valid_offers[local_idx])

            # Gather data
            browser.implicitly_wait(1)
            local_data = get_offer(browser)
            # Check issues
            if local_data == None:
                print("Issues in local_data")
                continue

            # Write data
            write_data(worksheet, local_data, i)
            i += 1

        # Pass page
        if next_page is not None:
            try:
                browser.get(next_page)
            except InvalidArgumentException:
                break
        else:
            break
        pages += 1

    # Close objects
    workbook.close()
    browser.close()
    print("Success")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import os
import json

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')  # Disable GPU to prevent issues
options.add_argument('--disable-software-rasterizer')

# Replace 'path_to_chromedriver' with your actual ChromeDriver executable path
service = Service('D:/Tools/chromedriver-win64/chromedriver.exe')

driver = webdriver.Chrome(service=service, options=options)

# Define the target URL
url = 'https://www.sinyi.com.tw/buy/list'

# Open the webpage
driver.get(url)

# Wait for the main content to load
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, '__next'))
    )
    print("Successfully loaded the webpage!")
    print(driver.page_source)  # Print full HTML of the loaded page
except TimeoutException:
    print("Failed to load the page or locate elements.")
    print(driver.page_source)  # Debug: Output HTML for troubleshooting
    driver.quit()
    exit()

# Scroll to load all property items dynamically
previous_item_count = 0
scroll_attempts = 0
max_scroll_attempts = 20  # Increased attempts for scrolling

while scroll_attempts < max_scroll_attempts:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(5, 10))  # Wait for additional content to load

    # Check the number of loaded items
    property_items = driver.find_elements(By.CLASS_NAME, 'buy-list-item')
    current_item_count = len(property_items)

    if current_item_count > previous_item_count:
        previous_item_count = current_item_count
        print(f"Loaded {current_item_count} property items.")
        scroll_attempts = 0  # Reset attempts if new items are loaded
    else:
        scroll_attempts += 1  # Increment attempts if no new items are loaded

# Extract data from property items
prices = []
areas = []
locations = []

# Extract data from each property item
for item in property_items:
    try:
        # Extract price
        try:
            price_element = item.find_element(By.XPATH, ".//div[contains(@class,'LongInfoCard_Type_Right')]//span[contains(text(),'萬')]")
            price = price_element.text.strip() if price_element else "N/A"
        except NoSuchElementException:
            price = "N/A"

        # Extract area
        try:
            area_element = item.find_element(By.XPATH, ".//div[contains(@class,'LongInfoCard_Type_HouseInfo')]//span[contains(text(),'建坪')]")
            area = area_element.text.strip() if area_element else "N/A"
        except NoSuchElementException:
            area = "N/A"

        # Extract location
        try:
            location_element = item.find_element(By.XPATH, ".//div[contains(@class,'LongInfoCard_Type_Address')]")
            location = location_element.text.strip() if location_element else "N/A"
        except NoSuchElementException:
            location = "N/A"

        print(f"Extracted: Price={price}, Area={area}, Location={location}")

        prices.append(price)
        areas.append(area)
        locations.append(location)

    except Exception as e:
        print(f"Error extracting data from an item: {e}")
        print(item.get_attribute('outerHTML'))  # Debug: Output problematic item's HTML

# Extract additional data from JSON if available
try:
    script_tags = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
    for script_tag in script_tags:
        json_content = script_tag.get_attribute("innerText")  # Get JSON text
        data = json.loads(json_content)  # Parse JSON

        # Debug: Output parsed JSON
        print(json.dumps(data, indent=4, ensure_ascii=False))

        # Extract data from JSON structure if applicable
        if isinstance(data, list):
            for entry in data:
                if entry.get("@type") == "Product":
                    price = entry.get("offers", {}).get("price", "N/A")
                    location = entry.get("name", "N/A")
                    print(f"Extracted from JSON: Price={price}, Location={location}")
                    prices.append(price)
                    locations.append(location)
except Exception as e:
    print(f"Error parsing JSON: {e}")

# Print final HTML for debugging
print("Final HTML of the page:")
print(driver.page_source)

# Close the WebDriver
driver.quit()

# Check if data was found
if not prices or not areas or not locations:
    print("No properties were found. Please check the webpage structure or selectors.")
else:
    # Debug: Output extracted data
    print(f"Prices: {prices}")
    print(f"Areas: {areas}")
    print(f"Locations: {locations}")

    # Create a DataFrame
    data = {
        'Price': prices,
        'Area': areas,
        'Location': locations
    }
    df = pd.DataFrame(data)

    # Save to a specific path
    file_path = 'D:/taiwan_housing_data.txt'  # Save as .txt
    df.to_csv(file_path, index=False, sep='\t', encoding='utf-8-sig')
    print(f"Data saved to {file_path}")
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

options = Options()
options.add_argument("--headless=new")

driver = webdriver.Chrome(options=options,
                          service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()))


def array_key_exists(items, key):
    for item in items:
        if item["name"] == key:
            return True
    return False


def extract_experts(item):
    return {
        'name': item.find_element(By.CLASS_NAME, "experts-item_name").text,
        'location': item.find_element(By.CLASS_NAME, "experts-li_text").text,
        'country': item.find_element(By.CLASS_NAME, "cc-country").text,
        'availability': item.find_element(By.CLASS_NAME, "experts-available-now-text").text,
        'description': item.find_element(By.CLASS_NAME, "line-clamp-3").text,
        'thumbnail': item.find_element(By.CLASS_NAME, "experts-item_profile-image").get_attribute("src"),
        'link': item.find_element(By.CLASS_NAME, "experts-item_link").get_attribute("href")
    }


def get_webflow_experts(url):
    driver.get(url)
    time.sleep(10)
    total = 0
    experts = []
    try:
        page = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.CLASS_NAME, "experts-grid"))
        )

        total_records_expected = driver.find_element(By.CLASS_NAME, "applied-filters_result-count-text")
        total_pages = int(total_records_expected.text) // 10

        while True:
            items = page.find_elements(By.CLASS_NAME, "experts-item")
            if len(items) > 0:
                total += 1
                print(f'Processing page {total} of {total_pages}')
                for item in items:
                    record = extract_experts(item)
                    if not array_key_exists(experts, record['name']):
                        print(record['name'])
                        experts.append(record)
            else:
                break

            next_page = driver.find_element(By.CLASS_NAME, "w-pagination-next")
            if next_page.text == 'Show more':
                next_page.click()
                time.sleep(5)
                print('Waiting for next page....')
            else:
                el_text = driver.find_element(By.CLASS_NAME, "w-pagination-wrapper")
                print(el_text.text)
                print('Cannot find more experts....')
                break

    finally:
        driver.quit()

    return experts, total


def get_expert_info():
    stats = []
    increment = 0
    try:
        data = pd.read_csv("./webflow-experts-results.csv")
        dfx = pd.DataFrame(data)
        for index, row in dfx.iterrows():
            increment += 1
            print(f"Processing page {increment} of {len(data)}")
            result_bag = {
                'name': row['name'],
                'location': row['location'],
                'country': row['country'],
                'expert_since': '',
                'language': ''
            }
            print(f"Load url {row['link']} ......")
            driver.get(row['link'])
            page = WebDriverWait(driver, 5).until(
                ec.presence_of_element_located((By.XPATH, "//div[@style='--local-gap:8px'][@data-sc='VStack Stack']"))
            )

            print("Extract data from ......")
            items = page.find_elements(By.XPATH, "//div[@style='--local-gap:4px'][@data-sc='HStack Stack']")
            print(f"Found {len(items)} items")
            for item in items:
                exists = item.find_elements(By.TAG_NAME, "svg")
                if len(exists) > 0:
                    svg = item.find_element(By.TAG_NAME, "svg").get_attribute('data-wf-icon')
                    if svg == 'DateIcon':
                        expert_since = item.find_element(By.TAG_NAME, 'span').text
                        result_bag['expert_since'] = expert_since.replace('Expert since ', '')

                    if svg == 'LocalizationIcon':
                        result_bag['language'] = item.find_element(By.TAG_NAME, 'span').text

            df_temp = pd.DataFrame([result_bag])
            df_temp.to_csv('log.csv', mode='a', index=False, header=False)
            stats.append(result_bag)
    finally:
        driver.quit()

    return stats


# results, num = get_webflow_experts('https://experts.webflow.com/browse')
# df = pd.DataFrame(results)
# df.to_csv("webflow-experts-results.csv")

full_experts = get_expert_info()
dframe = pd.DataFrame(full_experts)
dframe.to_csv("results.csv")

driver.quit()

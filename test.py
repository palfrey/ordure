import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


postcode = "se23 1nl"
address = "Flat A, 201, Brockley Rise"

class Driver:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1600, 1200)
        self.start = time.time()

    def log(self, msg):
        print(f"{time.time()-self.start:0.3f}: {msg}")
    
    def get(self, url):
        self.log(f"Getting {url}")
        self.driver.get(url)

    def find_element(self, by, spec) -> WebElement:
        self.log(f"Finding {by}, {spec}")
        elements = self.driver.find_elements(by, spec)
        if len(elements) == 0:
            raise Exception("No elements!")
        if len(elements) > 1:
            raise Exception(f"Multiple elements: {elements}")
        return elements[0]

    def wait_for_element(self, by, spec) -> WebElement:
        self.log(f"Waiting for {by}, {spec}")
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((by, spec))
        )

    def quit(self):
        self.driver.quit()

try:
    driver = Driver()
    driver.get("https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection")
    driver.find_element(By.CLASS_NAME, 'js-address-finder-input').send_keys(postcode)
    driver.find_element(By.CLASS_NAME, "js-address-finder-step-address").click()
    select = Select(driver.wait_for_element(By.CSS_SELECTOR, "select#address-selector option:nth-of-type(1)").find_element(By.XPATH, ".."))
    for opt in select.options:
        if opt.text.find(address) !=-1:
            print(opt.get_attribute("value"), opt.text)
            opt.click()
            break
    else:
        raise Exception
    res = driver.wait_for_element(By.CLASS_NAME, "js-find-collection-result")
    bin_pattern = re.compile(r"(?P<type>[A-Za-z]+) is collected (?P<frequency>[A-Z]+) on (?P<day>[A-Za-z]+)\.(?: Your next collection date is (?P<date>\d+/\d+/\d+))?")
    print(res.text)
    print([m.groupdict() for m in bin_pattern.finditer(res.text)])
finally:
    driver.quit()
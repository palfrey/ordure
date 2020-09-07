import os
from selenium import webdriver
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement


class Driver:
    def __init__(self):
        remote_url = os.environ.get("REMOTE_SELENIUM")
        if remote_url is None:
            options = webdriver.ChromeOptions()
            options.headless = True
            options.add_argument("--no-sandbox")
            self.driver = webdriver.Chrome(options=options)
        else:
            self.driver = webdriver.Remote(remote_url, desired_capabilities=DesiredCapabilities.CHROME)
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

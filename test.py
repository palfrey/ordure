from datetime import datetime, timedelta
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import todoist
import calendar

import yaml

settings_name = "settings.yaml"

settings = yaml.safe_load(open(settings_name))

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
    driver.find_element(By.CLASS_NAME, 'js-address-finder-input').send_keys(settings['postcode'])
    driver.find_element(By.CLASS_NAME, "js-address-finder-step-address").click()
    select = Select(driver.wait_for_element(By.CSS_SELECTOR, "select#address-selector option:nth-of-type(1)").find_element(By.XPATH, ".."))
    for opt in select.options:
        if opt.text.find(settings['address']) !=-1:
            print(opt.get_attribute("value"), opt.text)
            opt.click()
            break
    else:
        raise Exception
    res = driver.wait_for_element(By.CLASS_NAME, "js-find-collection-result")
    bin_pattern = re.compile(r"(?P<type>[A-Za-z]+) is collected (?P<frequency>[A-Z]+) on (?P<day>[A-Za-z]+)\.(?: Your next collection date is (?P<date>\d+/\d+/\d+))?")
    print(res.text)
    jobs = [m.groupdict() for m in bin_pattern.finditer(res.text)]
    print(jobs)
finally:
    driver.quit()

def search_for_job(name):
    for item in api.state['items']:
        if item["content"] == name:
            return item

api = todoist.TodoistAPI(settings['api_key'])
print(api.sync())
for job in jobs:
    if job['date']:
        when = datetime.strptime(job['date'], "%d/%m/%Y")
    else:
        now = datetime.today()
        dayNumber = calendar.weekday(now.year, now.month, now.day) 
        wantedDayNumber = list(calendar.day_name).index(job['day'])
        if dayNumber < wantedDayNumber:
            when = now + timedelta(days=wantedDayNumber-dayNumber)
        else:
            when = now + timedelta(days=wantedDayNumber-dayNumber+7)
    when -= timedelta(days=1)
    due = {"date": when.strftime("%Y-%m-%d")}
    due["string"] = due["date"]
    name = f"Take out the {job['type']}"
    if "tasks" not in settings:
        settings["tasks"] = {}
    if job["type"] not in settings["tasks"]:
        settings["tasks"][job["type"]] = {}
    job_id = settings["tasks"][job["type"]].get("id", None)
    if job_id is not None:
        item = api.items.get_by_id(job_id)
    else:
        item = search_for_job(name)
    
    if item is not None:
        settings["tasks"][job["type"]]["id"] = item["id"]
        print(name, when)
        if item["due"]["date"] != due["date"]:
            print("updating")
            item = api.items.get_by_id(item['id'])
            item.update(due=due)
            item.unarchive()
        print(item)
    else:
        task = api.items.add(name, due=due)
        print("Creating", name)
yaml.safe_dump(settings, open(settings_name, "w"))
api.commit()
from datetime import datetime, timedelta
import re
from typing import List
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException
import todoist
import calendar
from driver import Driver
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import dateparser

import yaml
from retry import retry


settings_name = "settings.yaml"
settings = yaml.safe_load(open(settings_name))


@retry(TimeoutException, tries=5, delay=10)
def get_job_data():
    bank_holiday_data = requests.get(
        "https://lewisham.gov.uk/myservices/wasterecycle/rubbish-and-recycling-collections-after-bank-holidays"
    )
    bank_holiday_data.raise_for_status()
    soup = BeautifulSoup(bank_holiday_data.text, "html.parser")
    table: Tag = soup.find("table", class_="markup-table")
    if table is not None:
        cells = table.find_all("td", class_="markup-td")
        cells = [dateparser.parse(c.contents[0].string) for c in cells][2:]
        cells = [c.date() for c in cells]
        switch_dates = dict(zip(cells[::2], cells[1::2]))
    else:
        switch_dates = {}
    print("Bank holiday dates", switch_dates)

    driver = Driver()
    try:
        driver.get(
            "https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection"
        )
        driver.find_element(By.CLASS_NAME, "cookie-banner__close").click()        
        driver.find_element(By.CLASS_NAME, "js-address-finder-input").send_keys(
            settings["postcode"]
        )
        driver.find_element(By.CLASS_NAME, "js-address-finder-step-address").click()
        select = Select(
            driver.wait_for_element(
                By.CSS_SELECTOR, "select#address-selector option:nth-of-type(1)"
            ).find_element(By.XPATH, "..")
        )
        for opt in select.options:
            if opt.text.find(settings["address"]) != -1:
                print(opt.get_attribute("value"), opt.text)
                opt.click()
                break
        else:
            raise Exception
        res = driver.wait_for_element(By.CLASS_NAME, "js-find-collection-result")
        bin_pattern = re.compile(
            r"(?P<type>[A-Za-z]+) is collected (?P<frequency>[A-Z]+) on (?P<day>[A-Za-z]+)\.(?: Your next collection date is (?P<date>\d+/\d+/\d+))?"
        )
        print(res.text)
        jobs = [m.groupdict() for m in bin_pattern.finditer(res.text)]
        print(jobs)
        return (switch_dates, jobs)
    finally:
        driver.quit()


def search_for_job(name):
    for item in api.state["items"]:
        if item["content"] == name:
            return item


(switch_dates, jobs) = get_job_data()

api = todoist.TodoistAPI(settings["api_key"])
print(api.sync())
for job in jobs:
    if job["date"]:
        when = datetime.strptime(job["date"], "%d/%m/%Y")
    else:
        now = datetime.today()
        dayNumber = calendar.weekday(now.year, now.month, now.day)
        wantedDayNumber = list(calendar.day_name).index(job["day"])
        if dayNumber < wantedDayNumber:
            when = now + timedelta(days=wantedDayNumber - dayNumber)
        else:
            when = now + timedelta(days=wantedDayNumber - dayNumber + 7)
    when = when.date()
    if when in switch_dates:
        when = switch_dates[when]
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
            item = api.items.get_by_id(item["id"])
            item.update(due=due)
            item.unarchive()
        print(item)
    else:
        task = api.items.add(name, due=due)
        print("Creating", name)
yaml.safe_dump(settings, open(settings_name, "w"))
api.commit()

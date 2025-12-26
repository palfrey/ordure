import calendar
import logging
import re
import time
from datetime import datetime, timedelta

import dateparser
import requests
import yaml
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from retry import retry
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from todoist_api_python.api import TodoistAPI

from driver import Driver

logging.basicConfig(level=logging.INFO)


settings_name = "settings.yaml"
settings = yaml.safe_load(open(settings_name))


@retry((TimeoutException, requests.exceptions.ConnectionError), tries=5, delay=10)
def get_job_data():
    switch_dates = {}
    bank_holiday_data = requests.get(
        "https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection/bank-holiday-bin"  # noqa: E501
    )
    if bank_holiday_data.status_code != 200:
        print("No bank holiday page")
    else:
        bank_holiday_data.raise_for_status()
        soup = BeautifulSoup(bank_holiday_data.text, "html.parser")
        items = soup.find_all("td", class_="markup-td")

        def get_inner(tag):
            children = list(tag.children)
            if len(children) > 0:
                for c in children:
                    if isinstance(c, NavigableString):
                        if c.string.strip() == "":
                            continue
                        return c.string
                    if isinstance(c, Tag):
                        return get_inner(c)
                    raise Exception(c)
            return tag.contents[0].string

        cells = [get_inner(c).replace("(Bank Holiday)", "") for c in items]
        pairs = list(zip(cells[::2], cells[1::2]))[1:]
        print("pairs", pairs)
        cells = [(dateparser.parse(c[0]), dateparser.parse(c[1])) for c in pairs]
        cells = [
            (c[0].date(), c[1].date())
            for c in cells
            if c[0] is not None and c[1] is not None
        ]
        print("cells", cells)
        switch_dates = dict(cells)
        print("Bank holiday dates", switch_dates)

    driver = Driver()
    try:
        driver.get(
            "https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection"
        )
        try:
            driver.wait_for_element(
                By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
            ).click()
        except ElementNotInteractableException:
            pass
        if driver.source().lower().find("bank holiday") != -1 and switch_dates == {}:
            print("Seeing mention of bank holiday, but no dates known!")

            # FIXME: commented out because the current bank holiday link is to
            # https://lewisham.gov.uk/sitecore/service/notfound.aspx?item=web%3a%7bCDD0AC08-2FA4-4ED4-99FC-39B5829F4432%7d%40en

            extra_dates_patt = re.compile(
                r"of the bank holiday on (.+)</span>\. Your bins will be collected the day after your normal collection day. Normal collections will resume on ([^\.]+)\."  # noqa: E501
            )
            extra_dates = extra_dates_patt.search(driver.source())
            assert extra_dates is None
            # assert extra_dates is not None, extra_dates
            # (start, end) = [dateparser.parse(d).date() for d in extra_dates.groups()]
            # current = start
            # while current < end:
            #     switch_dates[current] = current + timedelta(days=1)
            #     current += timedelta(days=1)
            # print("Revised bank holiday dates", switch_dates)
            # assert switch_dates != {}

        driver.find_element(By.CLASS_NAME, "js-address-finder-input").send_keys(
            settings["postcode"]
        )
        time.sleep(5)
        driver.find_element(By.CLASS_NAME, "js-address-finder-step-address").click()
        driver.wait_for_element(By.CSS_SELECTOR, "select#address-selector")
        for _ in range(5):
            try:
                select = Select(
                    driver.find_element(By.CSS_SELECTOR, "select#address-selector")
                )
                if len(select.options) > 0:
                    break
                driver.screenshot()
                time.sleep(3)
            except StaleElementReferenceException:
                time.sleep(3)
        else:
            raise Exception("panic!")
        print("options", len(select.options))
        choices = []
        for opt in select.options:
            if opt.text.lower().find(settings["address"].lower()) != -1:
                print(opt.get_attribute("value"), opt.text)
                opt.click()
                break
            choices.append(opt.text)
        else:
            for c in sorted(choices):
                print(c)
            raise Exception()
        res = driver.wait_for_element(By.CLASS_NAME, "js-find-collection-result")
        bin_pattern = re.compile(
            r"(?P<type>[A-Za-z ]+) is collected (?P<frequency>[A-Z]+) on (?P<day>[A-Za-z]+)\.(?: Your next collection date is (?P<date>\d+/\d+/\d+))?"  # noqa: E501
        )
        print(res.text)
        jobs = [m.groupdict() for m in bin_pattern.finditer(res.text)]
        print(jobs)
        return (switch_dates, jobs)
    finally:
        driver.quit()


def search_for_job(name):
    for chunk in api.get_tasks():
        if chunk.content == name:
            return item


(switch_dates, jobs) = get_job_data()

api = TodoistAPI(settings["api_key"])
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
    due = when.strftime("%Y-%m-%d")
    name = f"Take out the {job['type']}"
    if "tasks" not in settings:
        settings["tasks"] = {}
    if job["type"] not in settings["tasks"]:
        settings["tasks"][job["type"]] = {}
    job_id = settings["tasks"][job["type"]].get("id", None)
    if job_id is not None:
        print("id", job_id)
        item = api.get_task(task_id=job_id)
    else:
        item = search_for_job(name)

    if item is not None:
        settings["tasks"][job["type"]]["id"] = item.id
        print(name, when)
        if item.due is None or item.due.date != due:
            print("updating date")
            success = api.update_task(task_id=item.id, due_date=str(when))
            assert success, success
        if item.is_completed:
            print("opening")
            success = api.reopen_task(task_id=item.id)
            assert success, success
        print(item)
    else:
        task = api.add_task(content=name, due_date=str(when))
        print("Creating", name)
yaml.safe_dump(settings, open(settings_name, "w"))

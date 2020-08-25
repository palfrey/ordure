import requests
from bs4 import BeautifulSoup

from selenium import webdriver
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
driver.get("https://duckduckgo.com/")
driver.find_element_by_id('search_form_input_homepage').send_keys("realpython")
driver.find_element_by_id("search_button_homepage").click()
print(driver.current_url)
driver.quit()



postcode = "se23 1nl"
address = "Flat A, 201, Brockley Rise"

session = requests.session()
session.get("https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection")
locations = session.post(f"https://lewisham.gov.uk/api/AddressFinder?postcodeOrStreet={postcode}&national=False")
locations.raise_for_status()
print(locations.json())

for loc in locations.json():
    if loc['Title'].find(address) != -1:
        uprn = loc['Uprn']
        print(loc)
        break

#
#https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection/find-your-collection-day-result
#div


res = session.post(f"https://lewisham.gov.uk/api/AddressFinder?uprn={uprn}")
res.raise_for_status()
print(res.json())
print(requests.utils.dict_from_cookiejar(session.cookies))
res = session.get("https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection/find-your-collection-day-result")
res.raise_for_status()


soup = BeautifulSoup(res.text, 'html.parser')
results = soup.find_all('div', class_="js-find-collection-result")
print(results)
print(results[0].prettify())
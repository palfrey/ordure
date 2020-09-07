Ordure
======

    n. dung; manure; excrement


Lewisham Council have what at first glance appears to be a [perfectly good webpage](https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection) for figuring out what day your recycling is on. Except, there's no API, and the pages appear to have been designed for the explicit goal of breaking every option for scripting them.

Hence Ordure, a tool that mostly abuses [Selenium](https://www.selenium.dev/) (because the one thing they probably won't break is human web browsing of it) to manage to fish data from it into [Todoist](https://todoist.com/). It even uses the [bank holiday data](https://lewisham.gov.uk/myservices/wasterecycle/rubbish-and-recycling-collections-after-bank-holidays) to cope with those days (because the main page doesn't).

Usage
-----
1. Copy `settings.yaml.example` to `settings.yaml` and edit as appropriate
    * api_key: Personal API Token from `https://todoist.com/prefs/integrations`
    * postcode: Your postcode
    * address: A substring of your address that matches the search from the [lewisham page](https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection). Note in some cases (my house is one of them) you will need to pick a neighbour's address as they return 0 results for your house for some annoying reason!
2. Run `docker-compose up --exit-code-from=ordure` manually to make sure it all works
3. Add that command to crontab or similar

This will generate two tasks "Take out the Recycling" and "Take out the Refuse", corresponding to Lewisham's two specific names for the types of rubbish. Feel free to move these tasks to other projects or otherwise tag them as their ids have now been written into your settings.yaml.
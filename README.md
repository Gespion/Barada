# Barada
A future web application based on Python to source job offers from local job boards and serve susbscribers based on their preferences.

**Tools used:**

* A VPS running a LEMP stack (Ubuntu 18.10 + Nginx + MySQL + PHP)
* Scrapy to collect and format informations from local job boards
* MongoDB to store job offers scraped from local job boards
* AWS SES and SendinBlue for emails delivery to users
* Website + ContactForm7 plugin to collect users preferences
* Excel to manage subscribers list
* Python for code
* Time & fun :)

**How it works**

1 Set the python script to run once a week to collect jobs from 3 local job boards
2 Clean and format the job offers
3 Check for duplicate then store in DB
4 Based on preferences from Excel list send custom job offers

**To Do**

* Collect and store users+preferences in DB automatically
* Build a web interface to manage profiles, edit preferences, ...

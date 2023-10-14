# TwitterScraperSelenium
The package provides an opportunity to scrape tweets by a particular query, date and parameters. Scraping is powered by Selenium library, which implements auto scrolling and end of the page detection.
# Usage
See the sample written in test.py
- set manual_delay (in sec) parameter to secure the time needed to login.
- After logging in the page will automatically close and a new driver is going to execute all the requested scrape queries.

# Caution
Special characters (mostly everything but for the letters and numbers) should be reformated into HTML URL format (e.g. spaces into %20).
Since and until dates strings should have a format of Y-m-d (e.g. 2016-09-25). 

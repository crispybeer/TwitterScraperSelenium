from src.twitterScraper import Scraper

if __name__ == "__main__":
    scraper = Scraper(chromedriver_path='/Users/mac/Documents/programming/chromedriver', manual_delay=30)
    print(scraper.scrape_request('tasty%20pork', '2010-03-01', '2010-03-03'))
    print(scraper.scrape_request('tasty%20sushi', '2010-03-01', '2010-03-03'))
    print(scraper.scraped_data)
    
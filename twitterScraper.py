import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from time import sleep

import time
import platform
from fake_useragent import UserAgent
ua = UserAgent()

class Scraper:
    def __init__(self, chromedriver_path: str, user_agent: str = ua.chrome, manual_delay: int = 60) -> None:
        self.user_agent = user_agent
        self.scraped_data = list()
        self.chromedriver_path = chromedriver_path
        
        self._login(manual_delay)
        self.driver = self._create_driver()
        
    def _create_driver(self, headless:bool = False) -> webdriver.Chrome:
        chrome_options = webdriver.ChromeOptions()
        service = Service(executable_path=self.chromedriver_path)
        if headless: chrome_options.add_argument('--headless')
        
        system = platform.system()
        if system == "Windows":
            chrome_options.add_argument(r'user-data-dir=C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data\Default')
        elif system == "Darwin":
            chrome_options.add_argument('user-data-dir=./Library/Application Support/Google/Chrome/Default')
        else:
            raise Exception("Unsupported operating system")
        
        chrome_options.add_argument(f'user-agent={self.user_agent}')
        driver = webdriver.Chrome(options=chrome_options, service=service)
        return driver
        
    def _login(self, manual_delay: int) -> None:
        temp_driver = self._create_driver()
        temp_driver.get("https://twitter.com/login")
        time.sleep(manual_delay)
        temp_driver.quit()

    def scrape_request(self, q: str, since: str, until: str, recent: bool = True, exculde_replies: bool = True) -> list[dict]:
        assert until > since
    
        self.driver.get(f'https://twitter.com/search?q={q}%20until%3A{until}%20since%3A{since}'
                        + '%20-filter%3Areplies'*exculde_replies
                        + '&src=recent_search_click'
                        + '&f=live'*recent)
        
        scrollDelay = 0.1  # Delay between each scroll
        
        time.sleep(20)
        
        while 'Something went wrong' in self.driver.page_source:
            sleep(30)
            self.driver.refresh()
            sleep(5)
        
        try:
            articles = self.driver.find_elements(By.XPATH,"//article[@data-testid='tweet']") 
        except:
            raise Exception(RuntimeError)
        
        if len(articles) == 0:
            if 'No results for' in self.driver.page_source:   
                return []
            else: return None
            
        tweets = []
                
        i = 100
        counter = 0
        while True:
            for article in articles:
                try:
                    tag = article.find_element(By.XPATH,".//div[@data-testid='User-Name']").text
                    ts = article.find_element(By.XPATH,".//time").text
                    tweet = article.find_element(By.XPATH,".//div[@data-testid='tweetText']").text.strip().replace('\n', ' ')
                    reply = article.find_element(By.XPATH,".//div[@data-testid='reply']").text
                    retweet = article.find_element(By.XPATH,".//div[@data-testid='retweet']").text
                    like = article.find_element(By.XPATH,".//div[@data-testid='like']").text
                    #view = article.find_element(By.XPATH, "//div[@role='group']//a").text
                    
                    tweets.append({'UserTag': ts, 
                    'TimeStamp': tag,
                    'Tweet': tweet,
                    'Replies': reply,
                    'reTweets': retweet, 
                    'Likes': like,
                    #'Views': view,
                    })
                except:
                    pass
                    
            
            last_height = self.driver.execute_script("return window.pageYOffset")
            
            self.driver.execute_script(f"window.scrollBy(0, {i})")
            self.driver.implicitly_wait(scrollDelay)
            
            new_height = self.driver.execute_script("return window.pageYOffset")
            
            if last_height == new_height:
                counter += 1
                self.driver.implicitly_wait(scrollDelay*10)
            else:
                counter = 0
                
            if counter == 1:
                sleep(5)
            
            if counter == 5:
                break
            
            try:
                articles = self.driver.find_elements(By.XPATH,"//article[@data-testid='tweet']") 
            except:
                pass
        
        self.scraped_data+=tweets
        self.scraped_data = [dict(t) for t in {tuple(d.items()) for d in self.scraped_data}]
        return tweets

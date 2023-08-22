from bs4 import BeautifulSoup
import requests

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from time import sleep
import csv

from login_info import login, psw

from datetime import datetime
from datetime import timedelta
import time


proxy = "205.207.101.161:8282"

chromedriver_path = '/Users/mac/Documents/programming/chromedriver'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--proxy-server=%s' % proxy)
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')

driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chromedriver_path)

#LOGIN

driver.get("https://twitter.com/login")

sleep(10)
username = driver.find_element(By.XPATH,"//input[@name='text']")
username.send_keys(login)

sleep(3)

driver.maximize_window()
driver.implicitly_wait(10)

next_button = driver.find_element(By.XPATH,"//div[span='Next']/..")
next_button.click()

sleep(5)

password = driver.find_element(By.XPATH,"//input[@name='password']")
password.send_keys(psw)
password.send_keys(Keys.ENTER)

sleep(5)

#READ TICKERS AND DATES

with open('dates/names_.csv', encoding='utf-8-sig') as fin:
        all_names = dict()
        reader = csv.DictReader(fin, delimiter=';')
        for row in reader:
            ticker = row['crsp_tic']
            ticker_names = list(set([row['name1'], row['name3'], row['name4'], f'"{row["name+bank"]}"']))
            if '' in ticker_names: ticker_names.remove('')
            if '""' in ticker_names: ticker_names.remove('""')
            all_names[ticker] = ticker_names

with open('left.csv') as fin:
    reader = csv.reader(fin)
    
    data = list(reader)[1:-1]
    
    req_params = []
    
    for unparsed in data:
        row = unparsed[0].split('_')
        ticker = row[0]
        begin = datetime.strptime(row[1], '%Y-%m-%d').date()
        end = (datetime.strptime(row[2], '%Y-%m-%d')).date()
        names = all_names[ticker]
        req_params.append([ticker, begin, end, names])


for ticker, since_, until_, names in req_params[78:81]:
    tweets = list()
    t = '24'+ ticker
    until = '3A' + str(until_ + timedelta(days=1))
    since = '3A' + str(since_)
    
    for name in names:
        
        sleep(5)
        driver.get(f'https://twitter.com/search?q={name.replace(" ", "+").replace("&", "%26")}%20until%{until}%20since%{since}%20-filter%3Areplies&src=recent_search_click&f=live')

        repeat_counter = 0 # Counter for if the data is not updating anymore (means the end of the page)
        prev_set_len = 0
        scrollDelay = 0.1  # Delay between each scroll
        
        get_source = driver.page_source
        
        while 'Something went wrong' in get_source:
            sleep(900)
            driver.get(f'https://twitter.com/search?q={name.replace(" ", "+").replace("&", "%26")}%20until%{until}%20since%{since}%20-filter%3Areplies&src=recent_search_click&f=live')
            sleep(5)
            get_source = driver.page_source
            
        try:
            articles = driver.find_elements(By.XPATH,"//article[@data-testid='tweet']") 
        except:
            print(f'No tweets for {ticker}, {since_}, {until_}')
            continue
        
        if len(articles) == 0:
            continue
        
        print(articles[0].find_element(By.XPATH,".//div[@data-testid='User-Name']").text)
        
        i = 100
        counter = 0
        while True:
            for article in articles:
                st = datetime.now()
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
                    'Searh_tag': name,
                    #'Views': view,
                    })
                except:
                    print('skipped!')
                fin = datetime.now()
                print(fin-st)
                    
            
            last_height = driver.execute_script("return window.pageYOffset")
            
            driver.execute_script(f"window.scrollBy(0, {i})")
            driver.implicitly_wait(scrollDelay)
            
            new_height = driver.execute_script("return window.pageYOffset")
            
            if last_height == new_height:
                counter += 1
                driver.implicitly_wait(scrollDelay*10)
            else:
                counter = 0
                
            if counter == 1:
                driver.implicitly_wait(5)
            
            if counter == 5:
                break
            
            try:
                articles = driver.find_elements(By.XPATH,"//article[@data-testid='tweet']") 
            except:
                print(f'No tweets for {ticker}, {since_}, {until_}')
                continue
        
        keys = tweets[0].keys()
        with open(f'left/{ticker}_{since_}_{until_}.csv', 'w', newline='', errors='ignore') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(tweets)
        

            
        
    #     tweets.append({'UserTag': UserTag, 
    #                 'TimeStamp': TimeStamp,
    #                 'Tweet': Tweet,
    #                 'Replies': Replies,
    #                 'reTweets': reTweets, 
    #                 'Likes': Likes,
    #                 })
                    
    #     # check if html is the same
    #     last_height = driver.execute_script("return document.body.scrollHeight")
        
    #     driver.execute_script(f"window.scrollBy(0, {i})")
    #     # driver.execute_script('window.scrollTo(0,document.body.scrollHeight);') # Scrolls down to the bottom of the loaded page
    #     time.sleep(scrollDelay)
        
    #     new_height = driver.execute_script("return document.body.scrollHeight")
    #     if last_height == new_height:
    #         counter += 1
    #     else:
    #         counter = 0
        
    #     if counter == 5:
    #         break
        
    #     try:
    #         articles = driver.find_elements(By.XPATH,"//article[@data-testid='tweet']") 
    #     except:
    #         print(f'No tweets found')
    #         break
                    
    # try:
    #     keys = tweets[0].keys()
    # except:
    #     print(f'No tweets for {ticker}, {group[0]}, {group[1]}')
    #     continue 
    
    # for i in range(len(tweets)):
    #     tweets[i] = tweets[i].items()
    
    # tweets = list(set(tweets))
    
    # for i in range(len(tweets)):
    #     tweets[i] = dict(tweets[i])
    
    # for i in range(len(tweets)):
    #     for key in tweets[i]:
    #         tweets[i][key] = tweets[i][key].decode('ascii', 'ignore')

    
    # with open(f'{ticker}_{group[0]}_{group[1]}.csv', 'w', newline='') as output_file:
    #     dict_writer = csv.DictWriter(output_file, keys)
    #     dict_writer.writeheader()
    #     dict_writer.writerows(tweets)


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
        # Инициализация экземпляра класса Scraper с заданными параметрами
        self.user_agent = user_agent  # Пользовательский агент для имитации браузера
        self.scraped_data = list()  # Список для сохранения собранных данных
        self.chromedriver_path = chromedriver_path  # Путь к исполняемому файлу ChromeDriver
        
        # Выполняем вход в аккаунт перед созданием драйвера
        self._login(manual_delay)  
        self.driver = self._create_driver()  # Создаем веб-драйвер для взаимодействия с браузером
        
    def _create_driver(self, headless: bool = False) -> webdriver.Chrome:
        ''' Метод для создания драйвера Chrome'''
        chrome_options = webdriver.ChromeOptions()  # Опции для конфигурации Chrome
        service = Service(executable_path=self.chromedriver_path)  # Сервис для запуска ChromeDriver
        if headless:
            chrome_options.add_argument('--headless')  # Включает безголовый режим, если задано

        system = platform.system()  # Определяем операционную систему
        if system == "Windows":
            # Указываем путь к пользовательским данным для Windows
            chrome_options.add_argument(r'user-data-dir=C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data\Default')
        elif system == "Darwin":
            # Указываем путь к пользовательским данным для macOS
            chrome_options.add_argument('user-data-dir=./Library/Application Support/Google/Chrome/Default')
        else:
            raise Exception("Unsupported operating system")  # Обрабатываем неподдерживаемую ОС
        
        chrome_options.add_argument(f'user-agent={self.user_agent}')  # Устанавливаем пользовательский агент
        driver = webdriver.Chrome(options=chrome_options, service=service)  # Создаем экземпляр драйвера
        return driver
        
    def _login(self, manual_delay: int) -> None:
        '''Метод для выполнения входа в Twitter с временной задержкой для ручного ввода'''
        temp_driver = self._create_driver()  # Создаем временный драйвер
        temp_driver.get("https://twitter.com/login")  # Переходим на страницу входа в Twitter
        time.sleep(manual_delay)  # Задержка для ввода учетных данных вручную
        temp_driver.quit()  # Закрываем временный драйвер

    def scrape_request(self, q: str, since: str, until: str, recent: bool = True, exclude_replies: bool = True) -> list[dict]:
        '''Метод для сбора твитов по заданному запросу'''
        assert until > since  # Проверяем, что 'until' позже 'since'

        # Формируем URL для поиска с заданными параметрами
        self.driver.get(f'https://twitter.com/search?q={q}%20until%3A{until}%20since%3A{since}'
                        + '%20-filter%3Areplies'*exclude_replies
                        + '&src=recent_search_click'
                        + '&f=live'*recent)
        
        scrollDelay = 0.1  # Задержка между скроллингом страниц
        
        time.sleep(20)  # Задержка для загрузки контента
        
        # Обработка ошибки: если страница загружается неправильно
        while 'Something went wrong' in self.driver.page_source:
            sleep(30)  # Задержка перед повторной попыткой
            self.driver.refresh()  # Обновляем страницу
            sleep(5)  # Задержка после обновления
        
        try:
            # Поиск всех твитов на странице по указанному XPATH
            articles = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
        except:
            # Обработка ошибок при поиске
            raise Exception(RuntimeError)
        
        if len(articles) == 0:  # Если твиты не найдены
            if 'No results for' in self.driver.page_source:   
                return []  # Возвращаем пустой список, если результатов нет
            else: 
                return None
            
        tweets = []  # Список для сохранения найденных твитов
                
        i = 100  # Количество пикселей для прокрутки
        counter = 0  # Счетчик для отслеживания количества прокруток без обновления
        
        while True:
            for article in articles:  # Цикл по найденным твитам
                try:  # Пытаемся извлечь нужные данные
                    ts = article.find_element(By.XPATH, ".//div[@data-testid='User-Name']").text  # Имя пользователя
                    tag = article.find_element(By.XPATH, ".//time").text  # Время публикации
                    tweet = article.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text.strip().replace('\n', ' ')  # Текст твита
                    reply = article.find_element(By.XPATH, ".//div[@data-testid='reply']").text  # Количество ответов
                    retweet = article.find_element(By.XPATH, ".//div[@data-testid='retweet']").text  # Количество ретвитов
                    like = article.find_element(By.XPATH, ".//div[@data-testid='like']").text  # Количество лайков
                    
                    # Добавляем данные твита в список
                    tweets.append({'UserTag': ts, 
                                   'TimeStamp': tag,
                                   'Tweet': tweet,
                                   'Replies': reply,
                                   'reTweets': retweet, 
                                   'Likes': like,
                                   })
                except:
                    pass  # Игнорируем ошибки при извлечении данных
            
            last_height = self.driver.execute_script("return window.pageYOffset")  # Запоминаем текущую высоту прокрутки
            
            # Скроллим вниз на заданное количество пикселей
            self.driver.execute_script(f"window.scrollBy(0, {i})")
            self.driver.implicitly_wait(scrollDelay)  # Ждем в соответствии с заданной задержкой
            
            new_height = self.driver.execute_script("return window.pageYOffset")  # Новая высота прокрутки
            
            # Если высота прокрутки не изменилась, увеличиваем счетчик
            if last_height == new_height:
                counter += 1
                self.driver.implicitly_wait(scrollDelay * 10)  # Увеличиваем задержку, если ничего не загружено
            else:
                counter = 0  # Сбрасываем счетчик, если есть новые данные
                
            # Задержка перед следующей прокруткой, если данных нет
            if counter == 1:
                sleep(5)
            
            # Выходим из цикла после 5 последовательных прокруток без загрузки новых данных
            if counter == 5:
                break
            
            try:
                # Обновляем список статей твитов на странице
                articles = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']") 
            except:
                pass  # Игнорируем ошибки при повторном поиске статей
        
        # Объединяем собранные твиты с уже существующими данными
        self.scraped_data += tweets
        # Убираем дубликаты из общей коллекции собранных данных
        self.scraped_data = [dict(t) for t in {tuple(d.items()) for d in self.scraped_data}]
        return tweets  # Возвращаем список собранных твитов

    def clean_buffer(self) -> None:
        '''Метод для очистки буффера'''
        self.scraped_data.clear()  # Очищаем список собранных данных

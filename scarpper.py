import requests
from bs4 import BeautifulSoup
import json
import random
import time
from fake_useragent import UserAgent
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


class TwitterScraper:
    def __init__(self, accounts, keywords, use_proxy=True):
        """
        Initialize the Twitter scraper with multiple accounts and keywords
        
        :param accounts: List of dictionaries containing login credentials
        :param keywords: List of keywords to search
        :param use_proxy: Whether to use proxy rotation
        """
        self.accounts = accounts
        self.keywords = keywords
        self.current_account_index = 0
        self.ua = UserAgent()
        

        self.proxies = self._fetch_free_proxies() if use_proxy else []
        

        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def _fetch_free_proxies(self):
        """
        Fetch free proxy list from multiple sources
        :return: List of proxies
        """
        proxy_sources = [
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt'
        ]
        
        proxies = []
        for source in proxy_sources:
            try:
                response = requests.get(source)
                proxies.extend(response.text.split('\n'))
            except Exception as e:
                self.logger.warning(f"Could not fetch proxies from {source}: {e}")
        
        return [f'http://{proxy.strip()}' for proxy in proxies if proxy.strip()]
    
    def _setup_driver(self, proxy=None):
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={self.ua.random}')
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        return uc.Chrome(options=chrome_options)

    def _login(self, driver, account):
        try:
            driver.get('https://x.com/login')


            username_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'text'))
            )
            username_field.send_keys(account['username'])
            driver.find_element(By.XPATH, "//span[contains(text(), 'Next')]").click()


            password_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'password'))
            )
            password_field.send_keys(account['password'])
            driver.find_element(By.XPATH, "//span[contains(text(), 'Log in')]").click()


            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/home']"))
            )
            self.logger.info(f"Logged in as {account['username']}")
        except Exception as e:
            self.logger.error(f"Login failed for {account['username']}: {e}")
            raise

    def scrape_tweets(self, keyword, max_tweets=100):
        """
        Scrape tweets for a specific keyword
        :param keyword: Search keyword
        :param max_tweets: Maximum number of tweets to scrape
        :return: List of tweet dictionaries
        """
        tweets = []
        
        while len(tweets) < max_tweets:
            try:

                account = self.accounts[self.current_account_index]
                proxy = random.choice(self.proxies) if self.proxies else None
                
                with self._setup_driver(proxy) as driver:
                    self._login(driver, account)
                    

                    search_url = f'https://twitter.com/search?q={keyword}&src=typed_query'
                    driver.get(search_url)
                    

                    tweet_elements = driver.find_elements(By.XPATH, "//div[@data-testid='tweet']")
                    
                    for element in tweet_elements[:max_tweets - len(tweets)]:
                        try:
                            tweet_text = element.find_element(By.XPATH, ".//div[@lang]").text
                            tweet_author = element.find_element(By.XPATH, ".//span[contains(text(), '@')]").text
                            
                            tweets.append({
                                'text': tweet_text,
                                'author': tweet_author,
                                'keyword': keyword
                            })
                        except Exception as tweet_error:
                            self.logger.warning(f"Could not extract tweet: {tweet_error}")
                    

                    self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
                    

                    time.sleep(random.uniform(5, 15))
                    
            except Exception as e:
                self.logger.error(f"Scraping error: {e}")
                # Move to next account on failure
                self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
        
        return tweets
    
    def run(self, max_tweets_per_keyword=100):
        """
        Run scraper for all keywords
        :param max_tweets_per_keyword: Maximum tweets per keyword
        :return: JSON of scraped tweets
        """
        all_tweets = {}
        
        for keyword in self.keywords:
            tweets = self.scrape_tweets(keyword, max_tweets_per_keyword)
            all_tweets[keyword] = tweets
        
        # Save to JSON
        with open('twitter_scrape_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_tweets, f, ensure_ascii=False, indent=4)
        
        return all_tweets


accounts = [
    {'username': '33gitag@email.com', 'password': 'Random@1'},
    {'username': 'yashbiswa177@email.com', 'password': 'Random@2'},

]

keywords = ['gaming', 'maps', 'ai']

scraper = TwitterScraper(accounts, keywords)
results = scraper.run()
print(json.dumps(results, indent=2))

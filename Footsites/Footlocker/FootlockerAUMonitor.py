# No restocks, only releases
import requests
from datetime import datetime
import json
from bs4 import BeautifulSoup
import urllib3
import time
import logging
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType
import config
from fp.fp import FreeProxy
import traceback


logging.basicConfig(filename='Footlockerlog.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s', level=logging.DEBUG)

software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)

proxy_obj = FreeProxy(country_id=[config.FREE_PROXY_LOCATION], rand=True)

INSTOCK = []

def test_webhook():
    data = {
        "username": config.USERNAME,
        "avatar_url": config.AVATAR_URL,
        "embeds": [{
            "title": "Testing Webhook",
            "description": "This is just a quick test to ensure the webhook works. Thanks again for using these montiors!",
            "color": int(config.COLOUR),
            "footer": {'text': 'Made by Yasser'},
            "timestamp": str(datetime.utcnow())
        }]
    }

    result = requests.post(config.WEBHOOK, data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))
        logging.info(msg="Payload delivered successfully, code {}.".format(result.status_code))


def discord_webhook(title, url, thumbnail, style, sku, price):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    data = {
        "username": config.USERNAME,
        "avatar_url": config.AVATAR_URL,
        "embeds": [{
            "title": title, 
            "url": url,
            "thumbnail": {"url": thumbnail},
            "color": int(config.COLOUR),
            "footer": {"text": "Made by Yasser"},
            "timestamp": str(datetime.utcnow()),
            "fields": [
                {"name": "Style", "value": style},
                {"name": "SKU", "value": sku},
                {"name": "Price", "value": price},
            ]
        }]
    }

    result = requests.post(config.WEBHOOK, data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        logging.error(msg=err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))
        logging.info("Payload delivered successfully, code {}.".format(result.status_code))


def checker(item):
    """
    Determines whether the product status has changed
    """
    return item in INSTOCK


def scrape_main_site(headers, proxy):
    """
    Scrape the Footlocker site and adds each item to an array
    """
    items = []
    s = requests.Session()
    url = 'https://www.footlocker.com.au/en/men/'
    html = s.get(url=url, headers=headers, proxies=proxy, verify=False, timeout=10)
    soup = BeautifulSoup(html.text, 'html.parser')
    array = soup.find_all('div', {'class': 'fl-category--productlist--item'})
    for i in array:
        item = [i.find('span', {'class': 'ProductName-primary'}).text,
                i.find('span', {'class': 'ProductName-alt'}).text.split(chr(8226))[0],
                i.find('span', {'class': 'ProductName-alt'}).text.split(chr(8226))[1],
                i.find('img')['src'],
                i.find('a', {'class': 'ProductCard-link ProductCard-content'})['href']]
        items.append(item)

    logging.info(msg='Successfully scraped site')
    s.close()
    return items


def remove_duplicates(mylist):
    """
    Removes duplicate values from a list
    """
    return [list(t) for t in set(tuple(element) for element in mylist)]


def comparitor(item, start):
    if checker(item):
        pass
    else:
        INSTOCK.append(item)
        if start == 0:
            print(item)
            discord_webhook(
                title='',
                thumbnail='',
                url='',
                price='',
                colour=''
            )


def monitor():
    """
    Initiates monitor
    """
    print('''\n---------------------------
--- MONITOR HAS STARTED ---
---------------------------\n''')
    print(''' ** Now you will recieve notifications when an item drops or restocks **
This may take some time so you have to leave this script running. It's best to do this on a server (you can get a free one via AWS)!
    
Check out the docs at https://yasserqureshi1.github.io/Sneaker-Monitors/ for more info.
    
Join the Sneakers & Code family via Discord and subscribe to my YouTube channel https://www.youtube.com/c/YasCode\n\n''')
    logging.info(msg='Successfully started monitor')
    # Tests webhook URL
    test_webhook()

    # Ensures that first scrape does not notify all products
    start = 1

    # Initialising proxy and headers
    if config.ENABLE_FREE_PROXY:
        proxy = {'http': proxy_obj.get()}
    else:
        proxy_no = 0
        proxy = {} if config.PROXY == [] else {"http": f"http://{config.PROXY[proxy_no]}"}
    headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
    keywords = config.KEYWORDS
    while True:
        try:
            items = remove_duplicates(scrape_main_site(headers, proxy))
            for item in items:
                check = False
                if keywords == []:
                    comparitor(item, start)
                else:
                    for key in keywords:
                        if key.lower() in item[0].lower():
                            check = True
                            break
                    if check:
                        comparitor(item, start)
            start = 0
            time.sleep(float(config.DELAY))

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.HTTPError,
            requests.exceptions.ProxyError,
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.RetryError,
            requests.exceptions.SSLError,
            requests.exceptions.TooManyRedirects
        ) as e:
            logging.error(e)
            logging.info('Rotating headers and proxy')

            headers['User-Agent'] = user_agent_rotator.get_random_user_agent()
            
            if config.ENABLE_FREE_PROXY:
                proxy = {'http': proxy_obj.get()}

            elif config.PROXY != []:
                proxy_no = 0 if proxy_no == (len(config.PROXY)-1) else proxy_no + 1
                proxy = {"http": f"http://{config.PROXY[proxy_no]}"}

        except Exception as e:
            print(f"Exception found: {traceback.format_exc()}")
            logging.error(e)

if __name__ == '__main__':
    urllib3.disable_warnings()
    monitor()

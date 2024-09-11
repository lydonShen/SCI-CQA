import wget
import os 
import requests
from bs4 import BeautifulSoup
import random
from tqdm import tqdm


def get_soup_from_url(url, headers='', timeout=20, features='html.parser'):
    user_agents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
        'Opera/8.0 (Windows NT 5.1; U; en)',
        'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
        'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2 ',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52'
    ]
    if headers:
        url_response = requests.get(url, headers=headers, timeout=timeout)
    else:
        headers = {
            "User-Agent": str(random.choice(user_agents)),
            "Connection": 'keep-alive'
        }
        url_response = requests.get(url, headers=headers, timeout=timeout)
    if url_response.status_code != 200:
        return f'Response code is {url_response.status_code}'
    else:
        url_soup = BeautifulSoup(url_response.text, features)
        return url_soup


def download_file(download_url, dir):
    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
        filename = os.path.basename(download_url).split('?')[0]
        save_path = os.path.join(dir, filename)
        if not os.path.exists(save_path):
            wget.download(download_url, save_path)
            print(f'Download {filename} successful.')
        return
    except Exception as e:
        print(f'{download_url} {e}')

def fetch_and_down(url, save_dir):
    base_url = 'https://hf-mirror.com'
    work_soup = get_soup_from_url(url)
    urls = work_soup.find_all('a', {'title':'Download file'})
    for url in tqdm(urls, desc='Downloading...'):
        download_url = base_url + url['href']
        download_file(download_url, save_dir)

base_url = 'https://hf-mirror.com'
save_dir = '/home/data_sld/llava_v1.5-13B'
url = 'https://hf-mirror.com/liuhaotian/llava-v1.5-13b/tree/main'

fetch_and_down(url, save_dir)
'''
Author: Qigqi
LastEditors: lydonShen lyden_shen@sina.com
FilePath: /tools/download_papers.py
Copyright (c) 2024 by Qigqi, All Rights Reserved. 
'''

# -*- coding: utf-8 -*-
import csv
import os
import random
import re
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
import subprocess
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from requests.adapters import HTTPAdapter


def get_response_from_url(url, timeout=25, proxies = '', features='html.parser'):
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
    
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=5))
    session.mount('https://', HTTPAdapter(max_retries=5))
    headers = {
            "User-Agent": str(random.choice(user_agents)),
        }
    if proxies:
        url_response = session.get(url, headers=headers, timeout=timeout, proxies=proxies)
    else:
        
        url_response = session.get(url, headers=headers, timeout=timeout)
    # url_response = requests.get(url, headers=headers, timeout=timeout)
    
    return url_response
    

def sanitize_filename(filename):
    filename = filename.replace(' ', '_')
    allowed_chars = re.compile(r'[^a-zA-Z0-9_\-\\]')
    sanitized_filename = allowed_chars.sub('', filename)
    return sanitized_filename


def verify_zip_file_v1(file_path):
    try:
        # Run tar command to test the .tar.gz file
        result = subprocess.run(['tar', '-tzf', file_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Tar.gz file {file_path} verification successful.")
        return True
    except subprocess.CalledProcessError as e:
        return False


def verify_zip_file_v2(file_path):
    try:
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.getnames()
        print(f"Tar.gz file {file_path} verification successful.")
        return True
    except (tarfile.TarError, OSError) as e:
        print(f"Tar.gz file {file_path} verification failed.")
        return False
    

# , '--tries=3'
def download_file_with_wget(url, save_path):
    for i in range(5):
        try:
            result = subprocess.run(['wget', '-c', '-O', save_path, url], check=True)
            print(f'Downloaded: {save_path}')
            if not verify_zip_file_v2(save_path):
                continue
            return
        except subprocess.CalledProcessError as e:
            print(f'Failed to download {url} with wget. Error: {e}')
    print(f'Failed to download {save_path} with wget.')


def download_file(url, save_path, proxies=''):
    response = get_response_from_url(url, proxies=proxies)
    if response.status_code == 200:
        for _ in range(3):
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                # print(f'Downloaded: {save_path}')
            if not verify_zip_file_v2(save_path):
                time.sleep(random.uniform(1, 3))
                continue
            return
        print(f'Failed to download {save_path}.')
    else:
        print(f'Failed to download {url}. Status code: {response.status_code}')


# def download_file(url, save_path, proxies=''):
#     response = get_response_from_url(url, proxies=proxies)
#     if response.status_code == 200:
#         with open(save_path, 'wb') as file:
#             for chunk in response.iter_content(chunk_size=8192):
#                 file.write(chunk)
#             print(f'Downloaded: {save_path}')
#             # print(f'Downloaded: {save_path}')
#     else:
#         print(f'Failed to download {url}. Status code: {response.status_code}')

# def download_file_arxiv(dir, row):
#     title = row[1]
#     filename = sanitize_filename(row[1])+'.tar.gz'
#     try:
#         client = arxiv.Client(delay_seconds=3, num_retries=5)
#         search = arxiv.Search(
#             query=title,
#             max_results=1
#         )
#         for result in client.results(search):
#             arvix_links = result.links
#             if len(arvix_links) == 0:
#                 return
#             for i in range(3):
#                 result.download_source(dirpath=dir, filename=filename)
#                 save_path = os.path.join(dir, filename)
#                 if not verify_zip_file(save_path):
#                     time.sleep(random.uniform(1, 3))
#                     print(f'Retrying {i+1} times to download {save_path}.')
#                     continue
#                 else:
#                     print(f'Successful to download {save_path}.')
#                     return
                
#             print(f'Failed to download {save_path}.')
#     except Exception as e:
#         print(e)

def fetch_and_download(row, save_dir, proxies=''):
    base_url = row[-1]
    file_name = os.path.join(save_dir, sanitize_filename(sanitize_filename(row[1]))) + ".tar.gz"
    if not os.path.exists(file_name):
        try:
            if base_url not in ['No abs url', '', 'no abs link']:
                time.sleep(1 + random.uniform(0, 5))
                response = get_response_from_url(base_url, proxies=proxies)
                time.sleep(1 + random.uniform(0, 5))
                if response.status_code != 200:
                    print(f'Failed to access {base_url}. Status code: {response.status_code}')
                    while response.status_code == 403:
                        time.sleep(500 + random.uniform(0, 100))
                        print(response.status_code)
                soup = BeautifulSoup(response.content, 'html.parser')
                # latex_link = soup.find('a', class_='abs-button download-eprint')
                btn_tex_source = soup.find(string='TeX Source')
                if btn_tex_source:
                    latex_link = btn_tex_source.parent
                    download_url = latex_link.get('href')
                    if not download_url.startswith('http'):
                        download_url = 'https://arxiv.org' + download_url
                    # file_name = os.path.join(save_dir, sanitize_filename(sanitize_filename(row[1]))) + ".tar.gz"
                    if not os.path.exists(file_name):
                        download_file(download_url, file_name, proxies)
                    # download_file_with_wget(download_url, file_name)
                else:
                    print('No LaTeX source link found.')
                    # time.sleep(500 + random.uniform(0, 100))
            else:
                pass
        except Exception as e:
            print(e)
    return


def main():
    username = 't12146194416720'
    password = '3l3xq49e'
    tunnel = 'k997.kdltpspro.com:15818'

    papers_list = './paperlist/paper_list_v2.csv'
    save_dir = './tex_source_v2'

    proxies = {
    "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": tunnel},
    "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": tunnel}
}
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    with open(papers_list, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader, None)
        rows = list(csv_reader)[1400:10000]
    # for row in tqdm(rows[48625:], desc='Downloading...'):
    #     a = row
    #     fetch_and_download(row, save_dir, proxies)
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(tqdm(executor.map(lambda row: fetch_and_download(row, save_dir, proxies), rows), total=len(rows),
                  desc='Loading url...'))


if __name__ == '__main__':
    main()

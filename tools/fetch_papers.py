'''
Author: Qigqi
FilePath: /tools/fetch_papers.py
Description: get article title
Copyright (c) 2024 by Qigqi, All Rights Reserved. 
'''

# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import random
import arxiv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import re


def get_arxiv_links(title):
    pdf_link = ''
    abs_link = ''

    client = arxiv.Client()
    search = arxiv.Search(
        query=title,
        max_results=1
    )

    for result in client.results(search):
        arvix_links = result.links
        if len(arvix_links) == 0:
            return 'Not found on arxiv'
        else:
            for arvix_link in arvix_links:
                if 'abs' in arvix_link.href:
                    abs_link = arvix_link.href
                elif 'pdf' in arvix_link.href:
                    pdf_link = arvix_link.href
        if len(abs_link)==0 and len(pdf_link)==0:            
            abs_link = 'No abs url'
            pdf_link = 'No pdf url'
    return pdf_link, abs_link


def extract_conference_and_year(url):
    match = re.search(r'([a-zA-Z]+)(\d{4})', url)
    if match:
        conference_name = match.group(1)
        year = match.group(2)
        return conference_name, year
    return None, None


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


def fetch_papers_from_dblp(conference, year):
    # if conference not in ['acl', 'siggraph']:
    #     print(f'{conference} don\'t support.')
    #     return
    if conference == 'nips':
        url = f'https://dblp.org/db/conf/nips/neurips{year}.html'
    url = f'https://dblp.org/db/conf/{conference}/{conference}{year}.html'
    worksshops_soup = get_soup_from_url(url)
    papers = []
    titles_list = []
    links_list = []
    authors_list = []
    arxiv_abs_link_list = []
    conference_title_list = []
    try:
        # for page in worksshops_soup.find_all(string='table of contents in dblp'):
        #     page_url = page.parent['href']
        #     conference, year = extract_conference_and_year(page_url)
        #     conference_title = conference
        #     years = [str(year) for year in range(2015, 2024)]
        #     if year in years:
        #         page_workshop = get_soup_from_url(page_url)
        #         for workshops in tqdm(page_workshop.find_all('li', {'class': 'entry inproceedings'}), desc=f'{conference_title}{year}'):
        #             title = workshops.find('span', {'class': 'title'}).text
        #             pdf_link, arxiv_link = get_arxiv_links(title)
        #             authors = ", ".join([author.text for author in workshops.find_all('span', itemprop='author')])
        #             conference_title_list.append(conference_title)
        #             titles_list.append(title)
        #             arxiv_abs_link_list.append(arxiv_link)
        #             links_list.append(pdf_link)
        #             authors_list.append(authors)
        page_workshop = get_soup_from_url(url)
        for workshops in tqdm(page_workshop.find_all('li', {'class': 'entry inproceedings'}), desc=f'{conference}{year}'):
            title = workshops.find('span', {'class': 'title'}).text
            conference_title = f'{conference}{year}'
            pdf_link, arxiv_link = get_arxiv_links(title)
            authors = ", ".join([author.text for author in workshops.find_all('span', itemprop='author')])
            conference_title_list.append(conference_title)
            titles_list.append(title)
            arxiv_abs_link_list.append(arxiv_link)
            links_list.append(pdf_link)
            authors_list.append(authors)
        for i in range(len(titles_list)):
            papers.append([conference_title_list[i],
                        titles_list[i],
                        links_list[i],
                        authors_list[i],
                        arxiv_abs_link_list[i]])

        papers = list(set(tuple(sub_list) for sub_list in papers))
        return papers
    except Exception as e:
        print(e)


def main():
    output_dir = './paper_list'
    file_name = 'paper_list_v3.csv'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    conferences = ['nips', 'iclr', 'chi']
    all_papers = []
    years = range(2015, 2024)
    try:
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_papers = {
            executor.submit(fetch_papers_from_dblp, conference, year): (conference, year)
            for conference in conferences
            for year in years
        }
        for future in as_completed(future_to_papers):
            conference, year = future_to_papers[future]
            try:
                papers = future.result()
                if papers is not None:
                    all_papers.extend(papers)
            except Exception as e:
                print(f"Error fetching papers for {conference} {year}: {e}")

        with open(os.path.join(output_dir, file_name), 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Conference', 'Title', 'Link', 'Authors', 'arxiv_abs_link'])
            csvwriter.writerows(all_papers)

        print("CSV file has been generated.")
    except Exception as e:
        print(e)
if __name__ == "__main__":
    main()
'''
Author: Qigqi
Date: 2024-07-31 08:58:02
LastEditors: Qigqi
LastEditTime: 2024-07-31 08:59:43
FilePath: /tools/get_arxiv_links.py
Description: 通过title查找arXiv的源文件url

Copyright (c) 2024 by Qigqi, All Rights Reserved. 
'''
# -*- coding: utf-8 -*-
import csv
from tqdm import tqdm
import arxiv

def get_arxiv_link(title):
    """

    :param title: paper's title
    :return: if the paper  has arxiv abs link return abs link
    """
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
                    return arvix_link.href
                else:
                    return 'No abs url'

def process_row(row):
    conference = row[0]
    title = row[1].replace('"', '')
    arxiv_link = get_arxiv_link(title)
    pdf_link = row[2]
    authors = row[3]
    return [conference, title, arxiv_link, pdf_link, authors]
def main():

    all_paper_with_arxiv_urls = []

    file_path = 'test_list.csv'
    flag = 0
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader, None)
        for row in tqdm(csv_reader, desc='Getting arXiv url...'):
            flag += 1
            all_paper_with_arxiv_urls.append(process_row(row))
            if flag == 10:
                break
        with open('arxiv_papers_list.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Conference', 'Title', 'arXiv Link', 'PDF Link', 'Authors'])
            csvwriter.writerows(all_paper_with_arxiv_urls)

        print("CSV file has been generated.")

if __name__ == "__main__":
    main()


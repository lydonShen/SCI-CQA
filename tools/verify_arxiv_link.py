'''
Author: Qigqi
FilePath: /tools/verify_arxiv_link.py
Copyright (c) 2024 by Qigqi, All Rights Reserved. 
'''
import arxiv
import csv
import urllib, urllib.request
import requests

def get_arxiv_links(title,author):
    pdf_link = ''
    abs_link = ''
    title = title.replace('.','')
    query = f'ti:{title}'
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=20
    )

    for result in client.results(search):
        arvix_links = result.links
        if result.title == title:
            print(1)
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

paper_list = "/data/datasets/chart/paperlist/paper_list_v3.csv"

with open(paper_list, 'r') as csv_file:
    csv_list = csv.reader(csv_file)
    headr = next(csv_list)
    for row in csv_list:
        title = row[1].replace('.','').split(' ')
        t = '+'.join(title)
        url = f'http://export.arxiv.org/api/cs?query?search_query=all:{t}&max_results=1'
        data = requests.get(url).text
        # data = urllib.request.urlopen(url)
        print(data)


"""'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" lang="en">\n<head>\n<title>Not found</title>\n<link rel="shortcut icon" href="/favicon.ico" type="image/x-icon" />\n<link rel="stylesheet" type="text/css" media="screen" href="/css/arXiv-export.css" />\n<link rel="stylesheet" type="text/css" media="screen" href="/bibex/bibex.css?20181009">\n<link rel="stylesheet" type="text/css" media="screen" href="https://static.arxiv.org/static/browse/0.3.8/css/browse_search.css" />\n\n\n</head>\n<body class="with-cu-identity">\n\n<div id="cu-identity">\n<div id="cu-logo">\n<a href="https://www.cornell.edu/"><img src="//static.arxiv.org/icons/cu/cornell-reduced-white-SMALL.svg" alt="Cornell University" width="200" border="0" /></a>\n</div>\n<div id="support-ack">\n<a href="https://confluence.cornell.edu/x/ALlRF">We gratefully acknowledge support from<br /> the Simons Foundation and member institutions.</a>\n</div>\n</div>\n<div id="header">\n<h1 class="header-breadcrumbs"><a href="/"><img src="//static.arxiv.org/images/arxiv-logo-one-color-white.svg" aria-label="logo" alt="arxiv logo" width="85" style="width:85px;margin-right:8px;"></a></h1>\n<div id="search">\n<form id="search-arxiv" method="post" action="/search_classic">\n\n<div class="wrapper-search-arxiv">\n<input class="keyword-field" type="text" name="query" placeholder="Search or Article ID"/>\n\n<div class="filter-field">\n <select name="searchtype">\n<option value="all" selected="selected">All papers</option>\n<option value="ti">Titles</option>\n<option value="au">Authors</option>\n<option value="abs">Abstracts</option>\n<option value="ft">Full text</option>\n</select>\n</div>\n<input class="btn-search-arxiv" value="" type="submit">\n<div class="links">(<a href="https://info.arxiv.org/help">Help</a> | <a href="/find">Advanced search</a>)</div>\n</div>\n</form>\n</div>\n</div>\n<div id="content">\n<h1>Not Found</h1>\n<p>The requested URL \'/api/cs?query?search_query=Logic+Bonbon:+Exploring+Food+as+Computational+Artifact&amp;max_results=1\' was not found on this server.</p>\n<p>Try starting at the  \n<a href="https://export.arxiv.org/">front page.</a></p>\n</div>\n <footer style="clear: both;">\n      <div class="columns is-desktop" role="navigation" aria-label="Secondary" style="margin: -0.75em -0.75em 0.75em -0.75em">\n        <!-- Macro-Column 1 -->\n        <div class="column" style="padding: 0;">\n          <div class="columns">\n            <div class="column">\n              <ul style="list-style: none; line-height: 2;">\n                <li><a href="https://arxiv.org/about">About</a></li>\n                <li><a href="https://arxiv.org/help">Help</a></li>\n              </ul>\n            </div>\n            <div class="column">\n              <ul style="list-style: none; line-height: 2;">\n                <li>\n                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-black" role="presentation"><title>contact arXiv</title><desc>Click here to contact arXiv</desc><path d="M502.3 190.8c3.9-3.1 9.7-.2 9.7 4.7V400c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V195.6c0-5 5.7-7.8 9.7-4.7 22.4 17.4 52.1 39.5 154.1 113.6 21.1 15.4 56.7 47.8 92.2 47.6 35.7.3 72-32.8 92.3-47.6 102-74.1 131.6-96.3 154-113.7zM256 320c23.2.4 56.6-29.2 73.4-41.4 132.7-96.3 142.8-104.7 173.4-128.7 5.8-4.5 9.2-11.5 9.2-18.9v-19c0-26.5-21.5-48-48-48H48C21.5 64 0 85.5 0 112v19c0 7.4 3.4 14.3 9.2 18.9 30.6 23.9 40.7 32.4 173.4 128.7 16.8 12.2 50.2 41.8 73.4 41.4z"/></svg>\n                  <a href="https://arxiv.org/help/contact"> Contact</a>\n                </li>\n                <li>\n                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-black" role="presentation"><title>subscribe to arXiv mailings</title><desc>Click here to subscribe</desc><path d="M476 3.2L12.5 270.6c-18.1 10.4-15.8 35.6 2.2 43.2L121 358.4l287.3-253.2c5.5-4.9 13.3 2.6 8.6 8.3L176 407v80.5c0 23.6 28.5 32.9 42.5 15.8L282 426l124.6 52.2c14.2 6 30.4-2.9 33-18.2l72-432C515 7.8 493.3-6.8 476 3.2z"/></svg>\n                  <a href="https://arxiv.org/help/subscribe"> Subscribe</a>\n                </li>\n              </ul>\n            </div>\n          </div>\n        </div>\n        <!-- End Macro-Column 1 -->\n        <!-- Macro-Column 2 -->\n        <div class="column" style="padding: 0;">\n          <div class="columns">\n            <div class="column">\n              <ul style="list-style: none; line-height: 2;">\n                <li><a href="https://arxiv.org/help/license">Copyright</a></li>\n                <li><a href="https://arxiv.org/help/policies/privacy_policy">Privacy Policy</a></li>\n              </ul>\n            </div>\n            <div class="column sorry-app-links">\n              <ul style="list-style: none; line-height: 2;">\n                <li><a href="https://arxiv.org/help/web_accessibility">Web Accessibility Assistance</a></li>\n                <li>\n                  <p class="help">\n                    <a class="a11y-main-link" href="https://status.arxiv.org" target="_blank">arXiv Operational Status <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 512" class="icon filter-dark_grey" role="presentation"><path d="M224.3 273l-136 136c-9.4 9.4-24.6 9.4-33.9 0l-22.6-22.6c-9.4-9.4-9.4-24.6 0-33.9l96.4-96.4-96.4-96.4c-9.4-9.4-9.4-24.6 0-33.9L54.3 103c9.4-9.4 24.6-9.4 33.9 0l136 136c9.5 9.4 9.5 24.6.1 34z"/></svg></a><br>\n                    Get status notifications via\n                    <a class="is-link" href="https://subscribe.sorryapp.com/24846f03/email/new" target="_blank"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-black" role="presentation"><path d="M502.3 190.8c3.9-3.1 9.7-.2 9.7 4.7V400c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V195.6c0-5 5.7-7.8 9.7-4.7 22.4 17.4 52.1 39.5 154.1 113.6 21.1 15.4 56.7 47.8 92.2 47.6 35.7.3 72-32.8 92.3-47.6 102-74.1 131.6-96.3 154-113.7zM256 320c23.2.4 56.6-29.2 73.4-41.4 132.7-96.3 142.8-104.7 173.4-128.7 5.8-4.5 9.2-11.5 9.2-18.9v-19c0-26.5-21.5-48-48-48H48C21.5 64 0 85.5 0 112v19c0 7.4 3.4 14.3 9.2 18.9 30.6 23.9 40.7 32.4 173.4 128.7 16.8 12.2 50.2 41.8 73.4 41.4z"/></svg>email</a>\n                    or <a class="is-link" href="https://subscribe.sorryapp.com/24846f03/slack/new" target="_blank"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" class="icon filter-black" role="presentation"><path d="M94.12 315.1c0 25.9-21.16 47.06-47.06 47.06S0 341 0 315.1c0-25.9 21.16-47.06 47.06-47.06h47.06v47.06zm23.72 0c0-25.9 21.16-47.06 47.06-47.06s47.06 21.16 47.06 47.06v117.84c0 25.9-21.16 47.06-47.06 47.06s-47.06-21.16-47.06-47.06V315.1zm47.06-188.98c-25.9 0-47.06-21.16-47.06-47.06S139 32 164.9 32s47.06 21.16 47.06 47.06v47.06H164.9zm0 23.72c25.9 0 47.06 21.16 47.06 47.06s-21.16 47.06-47.06 47.06H47.06C21.16 243.96 0 222.8 0 196.9s21.16-47.06 47.06-47.06H164.9zm188.98 47.06c0-25.9 21.16-47.06 47.06-47.06 25.9 0 47.06 21.16 47.06 47.06s-21.16 47.06-47.06 47.06h-47.06V196.9zm-23.72 0c0 25.9-21.16 47.06-47.06 47.06-25.9 0-47.06-21.16-47.06-47.06V79.06c0-25.9 21.16-47.06 47.06-47.06 25.9 0 47.06 21.16 47.06 47.06V196.9zM283.1 385.88c25.9 0 47.06 21.16 47.06 47.06 0 25.9-21.16 47.06-47.06 47.06-25.9 0-47.06-21.16-47.06-47.06v-47.06h47.06zm0-23.72c-25.9 0-47.06-21.16-47.06-47.06 0-25.9 21.16-47.06 47.06-47.06h117.84c25.9 0 47.06 21.16 47.06 47.06 0 25.9-21.16 47.06-47.06 47.06H283.1z"/></svg>slack</a>\n                  </p>\n                </li>\n              </ul>\n            </div>\n          </div>\n        </div> <!-- end MetaColumn 2 -->\n        <!-- End Macro-Column 2 -->\n      </div>\n    </footer>\n</body>\n</html>\n'"""
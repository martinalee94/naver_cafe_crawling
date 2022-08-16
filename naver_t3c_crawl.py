import os
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup as bs

from mysql import MysqlConnector, connect_url

def update_post_number(mode, latest_number=None) -> int:
    with open('/Users/martina/git/naver_t3c/last_updated_number.txt', f'{mode}') as f:
        if mode == 'r':
            post_number = int(f.readline())
        elif mode == 'w':
            f.write(latest_number)
            post_number = latest_number
    return post_number

def insert_db(posts):
    posts_db_format = [(post['content'], "1", "141") for post in posts]
    print(posts_db_format)
    try:
        with MysqlConnector(connect_url) as db:
            query = 'insert into board(content, category_id, user_id) values(%s, %s, %s)'
            db.executemany(query, posts_db_format)
    except Exception as e:
        print(e)
    

BASE_URL = "https://cafe.naver.com/model3tesla"
url = "/ArticleList.nhn?search.clubid=29893475&search.menuid=1&search.boardtype=L"
response = requests.get(BASE_URL + url)
driver_path = r"/Users/martina/git/naver_t3c/chromedriver"

exec_time = datetime.now()

saved_post_number = update_post_number(mode="r")

if response.status_code == 200:
    html = response.text
    soup = bs(html, 'html.parser')
    posts = []

    board_numbers = soup.select("#main-area > div:nth-child(4) > table > tbody > tr > td.td_article > div.board-number")
    titles = soup.select("#main-area > div:nth-child(4) > table > tbody > tr > td.td_article > div.board-list > div > a.article")
    board_dates = soup.select("#main-area > div:nth-child(4) > table > tbody > tr > td.td_date")
    urls = soup.select("#main-area > div:nth-child(4) > table > tbody > tr > td.td_article > div.board-list > div > a.article")
    authors = soup.find_all("td",{"class": "p-nick"})[1:]

    s = Service(driver_path)
    browser = webdriver.Chrome(service=s)
    browser.implicitly_wait(time_to_wait=2)

    for board_number, title, board_date, url, author in zip(board_numbers, titles, board_dates, urls, authors):
        if int(board_number.get_text().strip()) > saved_post_number:
            content = ""
            image_urls = []

            browser.get(BASE_URL + url.attrs['href'])
            browser.implicitly_wait(time_to_wait=5)
            browser.switch_to.frame("cafe_main")
            html = browser.page_source
            soup = bs(html, 'html.parser')

            main = browser.window_handles
            # 창 하나 더 생성되면 로그인이 필요한 글임(외부공개 비허용)
            if len(main) == 2:
                browser.switch_to.window(main[1])
                browser.close()
                browser.switch_to.window(main[0])
            else:
                images = soup.find_all("img", {"class": "se-image-resource"})
                contents = soup.select("#tbody > div > div")
                image_urls = [image.attrs['src'] for image in images if images]
                for c in contents:
                    content += c.get_text().strip().replace(u"\u200b", " ").replace("\n", "").replace("  ", "")

                reformatted = {
                    "board_number" : board_number.get_text().strip(),
                    "author" : author.get_text(),
                    "title" : title.get_text().strip().replace(u"\u200b", " ").replace("\n", " ").replace("  ", ""),
                    "content" : content,
                    "created_date" : board_date.get_text().strip().replace("\n", ""),
                    "url" : BASE_URL + url.attrs['href'],
                    "images" : image_urls
                }
                posts.append(reformatted)
            browser.switch_to.default_content()

    if posts:
        insert_db(posts)
        update_post_number("w", posts[0]["board_number"])
else : 
    print(exec_time, response.status_code)


# for p in posts:
#     print(p, "\n")

browser.quit()







import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup as bs
from db.mysql import MysqlConnector, connect_url
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def insert_db(posts):
    posts_db_format = [(post['content'], "1", "141") for post in posts]
    print(posts_db_format)
    try:
        with MysqlConnector(connect_url) as db:
            query = 'insert into board(content, category_id, user_id) values(%s, %s, %s)'
            db.executemany(query, posts_db_format)
    except Exception as e:
        print(e)
    

BASE_URL = "https://cafe.naver.com/kig"
# url = "/ArticleList.nhn?search.clubid=29893475&search.menuid=1&search.boardtype=L"
response = requests.get(BASE_URL)
driver_path = r"/Users/martina/git/naver_t3c/chromedriver"

exec_time = datetime.now()


if response.status_code == 200:

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


browser.quit()







import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import requests
from bs4 import BeautifulSoup as bs
from constants.etc import DRIVER_PATH, PETER_URL
from db.mysql import MysqlConnector, connect_url
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

brokers_info = []


def insert_db(brokers: list):
    global brokers_info
    db_format = [
        (
            broker["company"],
            broker["manager"],
            broker["contact"],
            broker["address"],
            broker["license"],
            broker["url"],
            broker["board"],
        )
        for broker in brokers
    ]
    try:
        with MysqlConnector(connect_url) as db:
            query = "insert into peterpan_brokers(company, manager, contact, address, busi_license, post_url, board)\
                values(%s, %s, %s, %s, %s, %s, %s) on duplicate key update posts_cnt = posts_cnt + 1"
            db.executemany(query, db_format)
        brokers_info = []
    except Exception as e:
        print(e)


def check_each_house_info(navigation, browser, browser2, board):
    for navi in navigation:
        browser.get(navi)
        print(navi)
        browser.switch_to.frame("cafe_main")
        board_list = browser.find_elements(By.CLASS_NAME, "article-board")
        for b in board_list:
            if b.get_attribute("id") != "upperArticleList":
                board_list = b
        houses = board_list.find_elements(By.CLASS_NAME, "article")

        # check house, broker info
        for house in houses:
            broker_info = {}
            house_link = house.get_attribute("href")
            browser2.get(house_link)
            browser2.switch_to.default_content()

            # iframe is loading...'
            try:
                WebDriverWait(browser2, 5).until(
                    ec.presence_of_element_located((By.ID, "cafe_main"))
                )
                browser2.switch_to.frame("cafe_main")
                WebDriverWait(browser2, 5).until(
                    ec.presence_of_element_located((By.CLASS_NAME, "broker-info"))
                )
                broker_info_div_text = browser2.find_element(
                    By.CLASS_NAME, "broker-info"
                ).text
                broker_info_div_text = broker_info_div_text.splitlines()
            except Exception as e:
                print("로그인창 : ", e)
                continue

            if len(broker_info_div_text) == 4:
                try:
                    broker_info["company"] = broker_info_div_text[0]
                    broker_info["manager"] = (
                        broker_info_div_text[1].split("|")[0].split()[-1]
                    )
                    broker_info["contact"] = (
                        broker_info_div_text[1].split("|")[-1].split()[-1]
                    )
                    broker_info["address"] = broker_info_div_text[2]
                    broker_info["license"] = broker_info_div_text[3].split()[-1]
                    broker_info["url"] = house_link
                    broker_info["board"] = board
                    if broker_info["contact"]:
                        brokers_info.append(broker_info)
                except Exception as e:
                    print("broker_info 에러: ", e)
            else:
                with open("./extra_brokers_info.txt", "a") as f:
                    broker_info_to_text = ",".join(broker_info_div_text)
                    f.write(broker_info_to_text + "\n")
    insert_db(brokers_info)
    return brokers_info


def get_board_house_list(board, browser, browser2):
    check = 0
    browser.get(PETER_URL)
    board_link = browser.find_element(By.LINK_TEXT, board).get_attribute("href")
    browser.get(board_link)

    browser.switch_to.frame("cafe_main")

    while True:
        check += 1
        if check > 20:
            return
        navigation = browser.find_element(By.CLASS_NAME, "prev-next").find_elements(
            By.TAG_NAME, "a"
        )
        if navigation[0].text == "이전" and navigation[-1].text == "다음":  # 가운데
            next_link = navigation[-1].get_attribute("href")
            navigation = [navi.get_attribute("href") for navi in navigation][1:-1]
        elif navigation[-1].text == "다음":  # 시작
            next_link = navigation[-1].get_attribute("href")
            navigation = [navi.get_attribute("href") for navi in navigation][:-1]
        elif navigation[0].text == "이전":  # 끝
            navigation = [navi.get_attribute("href") for navi in navigation][1:]
            break
        else:
            navigation = [navi.get_attribute("href") for navi in navigation]
            break

        check_each_house_info(navigation, browser, browser2, board)
        browser.get(next_link)
        browser.switch_to.default_content()
        WebDriverWait(browser, 5).until(
            ec.presence_of_element_located((By.ID, "cafe_main"))
        )
        browser.switch_to.frame("cafe_main")

    check_each_house_info(navigation, browser, browser2, board)

    return


if __name__ == "__main__":
    response = requests.get(PETER_URL)

    if response.status_code == 200:
        s = Service(DRIVER_PATH)
        browser = webdriver.Chrome(service=s)
        browser2 = webdriver.Chrome(service=s)

        board_group = [f"[서울]{i}호선" for i in range(1, 10)]
        boards = [
            "[서울]신림선",
            "[서울]우이신설선",
            "[수도권]공항철도선",
            "[수도권]경강선",
            "[수도권]경의중앙선",
            "[수도권]경춘선",
            "[수도권]김포골드라인",
            "[수도권]서해선",
            "[수도권]수인분당선",
            "[수도권]신분당선",
            "[수도권]에버라인선",
            "[수도권]의정부선",
        ]
        board_group.extend(boards)

        try:
            for board in board_group:
                get_board_house_list(board, browser, browser2)
                brokers_info = []
        except Exception as e:
            print(e)
        finally:
            browser.quit()
            browser2.quit()
    else:
        print(response.status_code)

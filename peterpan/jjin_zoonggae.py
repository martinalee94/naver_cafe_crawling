import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from datetime import datetime

import requests
from bs4 import BeautifulSoup as bs
from constants.etc import DRIVER_PATH
from db.mysql import MysqlConnector, connect_url
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

brokers_info = []
license_check = set()


def insert_db(brokers: list):
    db_format = [
        (
            broker["company"],
            broker["manager"],
            broker["contact"],
            broker["address"],
            broker["license"],
        )
        for broker in brokers
    ]
    try:
        with MysqlConnector(connect_url) as db:
            query = "insert into brokers(company, manager, contact, address, busi_license) values(%s, %s, %s, %s, %s)"
            db.executemany(query, db_format)
    except Exception as e:
        print(e)


def check_each_house_info(navigation, browser, browser2):
    for navi in navigation:
        browser.get(navi)
        print(navi)
        browser.switch_to.frame("cafe_main")
        album = browser.find_element(By.CLASS_NAME, "article-album-sub")
        houses = album.find_elements(By.TAG_NAME, "li")
        # check house, broker info
        for house in houses:
            broker_info = {}
            house_link = house.find_element(By.CLASS_NAME, "album-img").get_attribute(
                "href"
            )
            browser2.get(house_link)
            browser2.switch_to.default_content()

            # iframe is loading...
            WebDriverWait(browser2, 5).until(
                ec.presence_of_element_located((By.ID, "cafe_main"))
            )
            browser2.switch_to.frame("cafe_main")
            WebDriverWait(browser2, 5).until(
                ec.presence_of_element_located((By.CLASS_NAME, "article_viewer"))
            )
            try:
                broker_info["company"] = (
                    browser2.find_element(
                        By.XPATH,
                        "//*[contains(text(),'업체명:') or contains(text(),'업체명 :')]",
                    )
                    .text.split(":")[-1]
                    .strip()
                )
                broker_info["manager"] = (
                    browser2.find_element(
                        By.XPATH,
                        "//*[contains(text(),'대표자명:') or contains(text(),'대표자명 :')]",
                    )
                    .text.split(":")[-1]
                    .strip()
                )
                broker_info["contact"] = (
                    browser2.find_element(
                        By.XPATH,
                        "//*[contains(text(),'대표 번호:') or contains(text(),'대표 번호 :')]",
                    )
                    .text.split(":")[-1]
                    .strip()
                )
                broker_info["address"] = (
                    browser2.find_element(
                        By.XPATH,
                        "//*[contains(text(),'소재지:') or contains(text(),'소재지 :')]",
                    )
                    .text.split(":")[-1]
                    .strip()
                )
                broker_info["license"] = (
                    browser2.find_element(
                        By.XPATH,
                        "//*[contains(text(),'등록번호:') or contains(text(),'등록번호 :')]",
                    )
                    .text.split(":")[-1]
                    .strip()
                )
                if not broker_info["license"] in license_check:
                    brokers_info.append(broker_info)
            except Exception as e:
                print(e)

    return brokers_info


def get_board_house_list(board, browser, browser2):
    browser.get(BASE_URL)
    board_link = browser.find_element(By.LINK_TEXT, board).get_attribute("href")
    browser.get(board_link)
    browser.switch_to.frame("cafe_main")

    navigation = browser.find_element(By.CLASS_NAME, "prev-next").find_elements(
        By.TAG_NAME, "a"
    )
    navigation = [navi.get_attribute("href") for navi in navigation]
    while len(navigation) > 10:
        check_each_house_info(navigation, browser, browser2)

        next_link = navigation[-1].get_attribute("href")
        browser.get(next_link)
        browser.switch_to.frame("cafe_main")
        WebDriverWait(browser, 3).until(
            ec.presence_of_element_located((By.ID, "cafe_main"))
        )
        navigation = browser.find_element(By.CLASS_NAME, "prev-next").find_elements(
            By.TAG_NAME, "a"
        )
    else:
        check_each_house_info(navigation, browser, browser2)

    insert_db(brokers_info)
    return


BASE_URL = "https://cafe.naver.com/kig"
response = requests.get(BASE_URL)

if response.status_code == 200:
    s = Service(DRIVER_PATH)
    browser = webdriver.Chrome(service=s)
    browser2 = webdriver.Chrome(service=s)

    board_group = [
        "✅[찐 중개 매물]서울",
        "✅[찐 중개 매물]경기",
        "✅[찐 중기청 가능]서울",
        "✅[찐 중기청 가능]경기",
        "✅[찐 LH전세 가능]서울",
        "✅[찐 LH전세 가능]경기",
    ]
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

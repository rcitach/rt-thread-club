#-*- coding:utf8 -*-
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

LOGIN_URL = ("https://www.rt-thread.org/account/user/index.html"
             "?response_type=code&authorized=yes&scope=basic&state=1588816557615"
             "&client_id=30792375&redirect_uri=https://club.rt-thread.org/index/user/login.html")

def safe_get(driver, url, retries=3, wait_sec=3):
    for i in range(retries):
        try:
            logging.info(f"Trying to get URL (attempt {i + 1}): {url}")
            driver.get(url)
            return True
        except WebDriverException as e:
            logging.warning("Failed to load page: %s", e)
            time.sleep(wait_sec)
    return False

def login_club(driver, user_name, pass_word):
    logging.info("Attempting to log in with username: %s", user_name)

    if not safe_get(driver, LOGIN_URL, retries=3):
        logging.error("Failed to load login page.")
        return False    

    try:
        # 填写用户名和密码
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(user_name)
        driver.find_element(By.ID, "password").send_keys(pass_word)
        driver.find_element(By.ID, "login").click()
    except Exception as e:
        logging.exception("Error during login attempt: %s", e)
        return False

    try:
        # 等待“立即跳转”按钮出现并点击
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
        )
        href = link.get_attribute("href")
        if not href or not href.startswith("https://club.rt-thread.org"):
            logging.error("Login redirect URL invalid: %s", href)
            return False
        link.click()

        # 等待跳转后的页面加载
        WebDriverWait(driver, 10).until(
            EC.url_contains("https://club.rt-thread.org")
        )
    except Exception as e:
        logging.exception("Exception during redirect/login flow: %s", e)
        logging.debug("Current URL: %s", driver.current_url)
        logging.debug("Page content (truncated): %s", driver.page_source[:1000])
        return False

    logging.info("Successfully logged in! Current URL: %s", driver.current_url)
    return True

def login_in_club(user_name, pass_word):
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    option.add_argument('no-sandbox')
    option.add_argument('disable-dev-shm-usage')

    driver = webdriver.Chrome(options=option)
    driver.maximize_window()

    try:
        # 尝试登录最多5次
        for i in range(5):
            if login_club(driver, user_name, pass_word):
                break
            else:
                logging.info("Login attempt %d failed. Refreshing and retrying...", i + 1)
                driver.refresh()
        else:
            logging.error("Failed to log in after 5 attempts.")
            return None

        # 等待页面加载并尝试签到
        try:
            sign_in_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.LINK_TEXT, "立即签到"))
            )
            sign_in_btn.click()
            logging.info("Sign in success!")
            time.sleep(1)
        except Exception:
            logging.info("No '立即签到' button found — maybe already signed in.")

        # 获取签到天数
        try:
            day_text = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "今日已签到"))
            )
            day_num = day_text.text
            logging.info("Signed in today: %s", day_num)
        except Exception as e:
            logging.warning("Could not determine sign-in day count: %s", e)
            day_num = None

        # 截图排行榜
        try:
            driver.find_element(By.LINK_TEXT, '排行榜').click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            driver.save_screenshot("/home/runner/paihang.png")
        except Exception as e:
            logging.warning("Failed to open or screenshot leaderboard: %s", e)

    finally:
        driver.quit()

    return day_num

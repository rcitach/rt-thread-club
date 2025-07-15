#-*- coding:utf-8 -*-
import os
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL = ("https://www.rt-thread.org/account/user/index.html"
             "?response_type=code&authorized=yes&scope=basic&state=1588816557615"
             "&client_id=30792375&redirect_uri=https://club.rt-thread.org/index/user/login.html")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

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

    if not safe_get(driver, LOGIN_URL):
        logging.error("Failed to load login page.")
        return False

    try:
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(user_name)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(pass_word)

        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_btn.click()
        logging.info("Clicked login button")

    except Exception as e:
        logging.error("Login error: %s", e)
        driver.save_screenshot("login_error.png")
        return False

    # 点击授权跳转
    try:
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
        )
        href = link.get_attribute("href")
        if not href.startswith("https://club.rt-thread.org"):
            logging.error("Login redirect URL invalid: %s", href)
            return False
        link.click()
        WebDriverWait(driver, 10).until(EC.url_contains("club.rt-thread.org"))
    except Exception as e:
        logging.error("Redirect click error: %s", e)
        driver.save_screenshot("/home/runner/redirect_error.png")
        return False

    logging.info("Successfully logged in! Current URL: %s", driver.current_url)
    return True

def login_in_club(user_name, pass_word):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        for i in range(5):
            if login_club(driver, user_name, pass_word):
                break
            logging.warning("Retry login: attempt %d", i + 1)
            driver.refresh()
            time.sleep(2)
        else:
            logging.error("Login failed after 5 attempts.")
            return None

        # 签到
        try:
            sign_in_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "立即签到"))
            )
            sign_in_btn.click()
            logging.info("Sign in success.")
        except TimeoutException:
            logging.info("No '立即签到' button found (maybe already signed in).")

        # 今日已签到信息
        try:
            day_text = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "今日已签到"))
            )
            logging.info("Sign-in status: %s", day_text.text)
        except:
            logging.info("未能读取签到状态")

        # 截图排行榜
        try:
            driver.find_element(By.LINK_TEXT, "排行榜").click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            driver.save_screenshot("paihang.png")
            logging.info("排行榜截图成功")
        except Exception as e:
            logging.warning("排行榜截图失败: %s", e)

    finally:
        driver.quit()

if __name__ == "__main__":

    username = os.environ["CLUB_USERNAME"]
    password = os.environ["CLUB_PASSWORD"]

    login_in_club(username, password)

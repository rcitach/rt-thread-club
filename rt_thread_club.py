# -*- coding:utf-8 -*-
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# ===== 日志配置 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)

# ===== 常量定义 =====
LOGIN_URL = (
    "https://www.rt-thread.org/account/user/index.html"
    "?response_type=code&authorized=yes&scope=basic&state=1588816557615"
    "&client_id=30792375&redirect_uri=https://club.rt-thread.org/index/user/login.html"
)

# ===== 通用等待函数 =====
def wait_for_dom_ready(driver, timeout=15):
    """等待页面加载完成，含 jQuery 状态判断"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return typeof jQuery == 'undefined' || jQuery.active == 0")
        )
    except:
        pass  # 非致命错误

# ===== 页面加载器（带重试） =====
def safe_get(driver, url, retries=3, wait_sec=3):
    for i in range(retries):
        try:
            logging.info(f"Trying to get URL (attempt {i + 1}): {url}")
            driver.get(url)
            wait_for_dom_ready(driver)
            return True
        except WebDriverException as e:
            logging.warning("Failed to load page: %s", e)
            time.sleep(wait_sec)
    return False

# ===== 登录主函数 =====
def login_club(driver, user_name, pass_word):
    logging.info("Attempting to log in with username: %s", user_name)

    if not safe_get(driver, LOGIN_URL, retries=3):
        logging.error("Failed to load login page.")
        return False

    try:
        # 模拟人类逐字输入
        username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        password_input = driver.find_element(By.ID, "password")

        for c in user_name:
            username_input.send_keys(c)
            time.sleep(0.1)

        for c in pass_word:
            password_input.send_keys(c)
            time.sleep(0.1)

        # 模拟按键方式登录
        password_input.send_keys(Keys.TAB)
        driver.find_element(By.ID, "login").send_keys(Keys.ENTER)

        # 等待跳转页面按钮
        link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary"))
        )
        href = link.get_attribute("href")
        if not href or not href.startswith("https://club.rt-thread.org"):
            logging.error("Login redirect URL invalid: %s", href)
            return False
        link.click()

        # 等待跳转完成
        WebDriverWait(driver, 10).until(lambda d: "club.rt-thread.org" in d.current_url)
        wait_for_dom_ready(driver)
    except Exception as e:
        logging.error("Login error: %s", e)
        driver.save_screenshot("login_failed.png")
        logging.error("Screenshot saved to login_failed.png")
        return False

    logging.info("Successfully logged in! Current URL: %s", driver.current_url)
    return True

# ===== 登录并执行签到 + 截图任务 =====
def login_in_club(user_name, pass_word):
    option = webdriver.ChromeOptions()
    option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    option.add_argument('--disable-dev-shm-usage')
    option.add_argument('--window-size=1920,1080')
    option.add_argument('--lang=zh-CN,zh')
    option.add_argument('--disable-gpu')
    option.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36')
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=option)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        for i in range(5):
            if login_club(driver, user_name, pass_word):
                break
            else:
                logging.info("Login attempt %d failed. Refreshing and retrying...", i + 1)
                driver.refresh()
        else:
            logging.error("Failed to log in after 5 attempts.")
            return None

        # 签到
        try:
            sign_in_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.LINK_TEXT, "立即签到"))
            )
            sign_in_btn.click()
            logging.info("Sign in success!")
            time.sleep(1)
        except Exception:
            logging.info("No '立即签到' button found — maybe already signed in.")

        # 今日签到信息
        try:
            day_text = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "今日已签到"))
            )
            logging.info("Signed in today: %s", day_text.text)
            day_num = day_text.text
        except Exception as e:
            logging.warning("Could not determine sign-in day count: %s", e)
            day_num = None

        # 排行榜截图
        try:
            driver.find_element(By.LINK_TEXT, '排行榜').click()
            wait_for_dom_ready(driver)
            driver.save_screenshot("paihang.png")
            logging.info("Leaderboard screenshot saved: paihang.png")
        except Exception as e:
            logging.warning("Failed to capture leaderboard: %s", e)

    finally:
        driver.quit()

    return day_num

# ===== 主入口 =====
if __name__ == "__main__":
    username = os.environ["CLUB_USERNAME"]
    password = os.environ["CLUB_PASSWORD"]

    day_info = login_in_club(username, password)
    if day_info:
        print("✅ 签到成功：", day_info)
    else:
        print("❌ 签到失败")

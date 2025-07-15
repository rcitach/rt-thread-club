#-*- coding:utf-8 -*-
import os
import time
import logging
import random
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

LOGIN_URL = ("https://www.rt-thread.org/account/user/index.html"
             "?response_type=code&authorized=yes&scope=basic&state=1588816557615"
             "&client_id=30792375&redirect_uri=https://club.rt-thread.org/index/user/login.html")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def safe_get(driver, url, retries=3, wait_sec=3):
    for i in range(retries):
        try:
            logging.info(f"Trying to get URL (attempt {i + 1}): {url}")
            driver.get(url)
            time.sleep(random.uniform(1, 2))  # 随机延迟模拟人类行为
            return True
        except WebDriverException as e:
            logging.warning("Failed to load page: %s", e)
            time.sleep(wait_sec)
    return False

def simulate_human_behavior(driver):
    """模拟人类行为：鼠标移动、滚动等"""
    try:
        # 随机鼠标移动
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(50, 200), random.randint(50, 200)).perform()
        time.sleep(random.uniform(0.5, 1.5))
        
        # 随机滚动页面
        driver.execute_script("window.scrollBy(0, " + str(random.randint(100, 500)) + ");")
        time.sleep(random.uniform(0.3, 1))
        
        # 模拟鼠标悬停在某个元素上
        try:
            element = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element(element).perform()
        except:
            logging.warning("No element found for hover simulation")
    except Exception as e:
        logging.warning("Error in simulating human behavior: %s", e)

def handle_sliding_verification(driver):
    """处理可能的滑动验证"""
    try:
        slider = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sl-slider"))
        )
        logging.info("Detected sliding verification, attempting to slide...")
        
        actions = ActionChains(driver)
        actions.click_and_hold(slider).perform()
        time.sleep(random.uniform(0.2, 0.5))
        
        # 模拟人类滑动轨迹
        for x in range(0, 200, 5):  # 假设滑动距离为200像素
            actions.move_by_offset(5, random.randint(-2, 2)).perform()
            time.sleep(random.uniform(0.01, 0.05))
        actions.release().perform()
        logging.info("Sliding completed, waiting for verification...")
        
        # 等待验证结果
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "sl-slider"))
        )
        logging.info("Sliding verification passed")
        return True
    except TimeoutException:
        logging.info("No sliding verification detected")
        return False
    except Exception as e:
        logging.error("Error in sliding verification: %s", e)
        return False

def bypass_human_check(driver):
    """处理 SafeLine WAF 人机验证"""
    try:
        # 模拟人类行为
        simulate_human_behavior(driver)
        
        # 检查是否存在人机验证
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "sl-box"))
        )
        sl_box = driver.find_element(By.ID, "sl-box")
        if "Confirm You Are Human" in sl_box.text:
            logging.info("Detected human verification prompt, attempting to bypass...")

            # 尝试处理滑动验证
            if handle_sliding_verification(driver):
                return True

            # 尝试点击确认按钮
            confirm_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sl-check"))
            )
            confirm_btn.click()
            logging.info("Confirm button clicked, waiting for verification to complete...")

            # 等待验证页面消失
            WebDriverWait(driver, 15).until_not(
                EC.presence_of_element_located((By.ID, "sl-box"))
            )
            logging.info("Human verification passed")
            return True
        else:
            logging.info("No human verification prompt detected")
            return True
    except TimeoutException:
        logging.info("No human verification detected or already passed")
        return True
    except Exception as e:
        logging.error("Error in human verification: %s", e)
        driver.save_screenshot("/home/runner/human_check_error.png")
        return False

def login_club(driver, user_name, pass_word):
    logging.info("Attempting to log in with username: %s", user_name)

    if not safe_get(driver, LOGIN_URL):
        logging.error("Failed to load login page.")
        return False

    # 处理人机验证
    if not bypass_human_check(driver):
        logging.error("Failed to bypass human verification")
        return False

    try:
        # 输入用户名和密码
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(user_name)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(pass_word)

        # 点击登录按钮
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_btn.click()
        logging.info("Clicked login button")

        # 再次检查人机验证（登录后可能触发）
        if not bypass_human_check(driver):
            logging.error("Failed to bypass human verification after login")
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
            logging.info("Successfully redirected to club.rt-thread.org")
        except Exception as e:
            logging.error("Redirect click error: %s", e)
            driver.save_screenshot("/home/runner/redirect_error.png")
            return False

        logging.info("Successfully logged in! Current URL: %s", driver.current_url)
        return True
    except Exception as e:
        logging.error("Login error: %s", e)
        driver.save_screenshot("/home/runner/login_error.png")
        return False

def login_in_club(user_name, pass_word):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # 添加用户代理，模拟真实浏览器
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)

    try:
        for i in range(5):
            if login_club(driver, user_name, pass_word):
                break
            logging.warning("Retry login: attempt %d", i + 1)
            driver.refresh()
            time.sleep(random.uniform(2, 4))
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

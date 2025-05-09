from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

def test_view_article():
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        # 1. Login
        print("Logging in...")
        driver.get("http://localhost:8000/login/")
        
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username.send_keys("june@gmail.com")
        
        password = driver.find_element(By.NAME, "password")
        password.send_keys("june567c" + Keys.RETURN)
        
        # 2. Verify login success
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Profile"))
        )
        
        # 3. View an article
        print("Viewing article...")
        articles = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".article a"))
        )
        articles[0].click()
        
        # 4. Verify article page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "article-content"))
        )
        print("✅ View Article Test Passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        driver.save_screenshot("view_article_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_view_article()
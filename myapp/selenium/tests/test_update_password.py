from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

def test_update_password():
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        # 1. Login
        print("Logging in...")
        driver.get("http://localhost:8000/login/")
        
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username.send_keys("testuser")
        
        password = driver.find_element(By.NAME, "password")
        password.send_keys("oldpassword123" + Keys.RETURN)
        
        # 2. Go to profile
        print("Accessing profile...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Profile"))
        ).click()
        
        # 3. Update password
        print("Updating password...")
        current_pass = driver.find_element(By.NAME, "current_password")
        new_pass = driver.find_element(By.NAME, "new_password")
        confirm_pass = driver.find_element(By.NAME, "confirm_password")
        
        current_pass.send_keys("oldpassword123")
        new_pass.send_keys("newpassword123")
        confirm_pass.send_keys("newpassword123" + Keys.RETURN)
        
        # 4. Verify success
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success"))
        )
        print("✅ Password Update Test Passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        driver.save_screenshot("update_password_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_update_password()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

def test_edit_draft():
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
        
        # 2. Go to drafts
        print("Accessing drafts...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Drafts"))
        ).click()
        
        # 3. Select first draft
        print("Selecting draft...")
        drafts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".draft a"))
        )
        drafts[0].click()
        
        # 4. Edit content
        print("Editing draft...")
        content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_content"))
        )
        content.clear()
        content.send_keys("Edited draft content - " + str(time.time()))
        
        # 5. Save changes
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # 6. Verify success
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success"))
        )
        print("✅ Edit Draft Test Passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        driver.save_screenshot("edit_draft_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_edit_draft()
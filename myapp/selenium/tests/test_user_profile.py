import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class UserLoginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--start-maximized')
        
        # Initialize driver
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.base_url = "http://127.0.0.1:8000"
        cls.wait = WebDriverWait(cls.driver, 10)

    def test_01_login(self):
        """Test successful user login"""
        try:
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login/")
            
            # Fill login form
            email = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email.send_keys("june@gmail.com")
            
            password = self.driver.find_element(By.NAME, "password")
            password.send_keys("june5678")
            
            # Click login button (try different selectors)
            login_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign In')]")))
            login_btn.click()
            
            # Verify successful login
            self.wait.until(
                lambda driver: "dashboard" in driver.current_url.lower() or 
                "welcome" in driver.page_source.lower() or
                driver.find_elements(By.PARTIAL_LINK_TEXT, "Logout"))
            
            print("Login test passed successfully")
            
        except Exception as e:
            self.driver.save_screenshot("login_fail.png")
            raise AssertionError(f"Login failed: {str(e)}")

    def test_02_profile(self):
        """Test user profile page"""
        try:
            # First ensure we're logged in
            self.test_01_login()
            
            # Navigate to profile
            profile_link = self.wait.until(EC.element_to_be_clickable(
                (By.LINK_TEXT, "Profile")))
            profile_link.click()
            
            # Wait for profile page to load
            self.wait.until(EC.url_contains("profile"))
            
            # Verify profile info
            name_element = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(@class,'name') or contains(@id,'name')]")))
            email_element = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(@class,'email') or contains(@id,'email')]"))
            )
            
            self.assertIn("June", name_element.text)
            self.assertEqual("june@gmail.com", email_element.text)
            print("Profile test passed successfully")
            
        except Exception as e:
            self.driver.save_screenshot("profile_fail.png")
            print(f"Exception occurred: {str(e)}")
            print(self.driver.page_source)
            raise AssertionError(f"Profile test failed: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

if __name__ == "__main__":
    unittest.main()
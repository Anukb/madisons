from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class LoginTests(LiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.implicitly_wait(10)

    def tearDown(self):
        self.driver.quit()

    def test_login(self):
        self.driver.get(f"{self.live_server_url}/login/")
        time.sleep(1)  # Wait for the page to load

        # Fill in the login form
        self.driver.find_element(By.NAME, 'email').send_keys('testuser@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        time.sleep(2)  # Wait for the login to complete

        # Check that the user is redirected to the home page
        self.assertIn("home", self.driver.current_url)

# Repeat similar structure for other tests

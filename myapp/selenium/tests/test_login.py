import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.service import Service

class UserLoginTestCase(unittest.TestCase):

    def setUp(self):
        # Set up the WebDriver with the Service class
        self.driver = webdriver.Chrome()
        self.driver.get('http://localhost:8000/login')  # Update with your login URL

    def test_user_login(self):
        driver = self.driver
        
        # Find the email and password input fields and the login button
        email_input = driver.find_element(By.NAME, 'email')  # Adjust the selector as necessary
        password_input = driver.find_element(By.NAME, 'password')  # Adjust the selector as necessary
        login_button = driver.find_element(By.XPATH, '//button[text()="Login"]')  # Adjust the selector as necessary

        # Input email and password
        email_input.send_keys('june@gmail.com')  # Replace with a valid test email
        password_input.send_keys('june5678')  # Replace with a valid test password

        # Click the login button
        login_button.click()

        # Wait for a moment to allow the page to load
        time.sleep(2)  # You can use WebDriverWait for a more robust solution

        # Check if login was successful (you can adjust the condition based on your application)
        self.assertIn("Welcome", driver.page_source)  # Adjust the condition as necessary

    def tearDown(self):
        # Close the browser window
        self.driver.quit()

if __name__ == '__main__':
    unittest.main()

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.url = "http://localhost:8000"  # Update with your actual URL
    
    def load(self):
        self.driver.get(self.url)
    
    def get_title(self):
        return self.driver.title
    
    def get_heading(self):
        return self.driver.find_element(By.TAG_NAME, "h1").text
    
    def get_subheading(self):
        return self.driver.find_element(By.TAG_NAME, "h2").text
    
    def enter_email(self, email):
        email_field = self.driver.find_element(By.ID, "email")
        email_field.clear()
        email_field.send_keys(email)
    
    def enter_password(self, password):
        password_field = self.driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
    
    def click_login_button(self):
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn")
        login_button.click()
    
    def click_register_link(self):
        register_link = self.driver.find_element(By.CLASS_NAME, "register-link")
        register_link.click()
    
    def click_forgot_password_link(self):
        forgot_link = self.driver.find_element(By.CSS_SELECTOR, ".forgot-password a")
        forgot_link.click()
    
    def click_admin_login_link(self):
        admin_link = self.driver.find_element(By.CLASS_NAME, "admin-link")
        admin_link.click()
    
    def get_error_messages(self):
        try:
            error_list = self.driver.find_element(By.CLASS_NAME, "error-messages")
            return [error.text for error in error_list.find_elements(By.TAG_NAME, "li")]
        except:
            return []
    
    def is_loaded(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            return True
        except:
            return False
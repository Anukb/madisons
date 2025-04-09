from .test_base import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class HomepageLoginTests(BaseTest):
    def test_homepage_load(self):
        """Test if homepage loads within 3 seconds and contains title"""
        try:
            start_time = time.time()
            self.driver.get(self.live_server_url)
            load_time = time.time() - start_time
            
            # Check load time
            load_time_ok = load_time < 3
            
            # Check for title or logo
            title_element = self.wait_for_element(By.TAG_NAME, 'h1')
            title_ok = 'Madison' in title_element.text
            
            # Log results
            self.log_test_result(
                'Homepage Load Test',
                load_time_ok and title_ok,
                None if (load_time_ok and title_ok) else f'Load time: {load_time:.2f}s, Title found: {title_ok}'
            )
            
            # Assertions
            self.assertTrue(load_time_ok, f'Page load time ({load_time:.2f}s) exceeded 3 seconds')
            self.assertTrue(title_ok, 'Homepage title not found')
            
        except Exception as e:
            self.log_test_result('Homepage Load Test', False, str(e))
            raise
    
    def test_login_page_render(self):
        """Test if login page renders correctly with required fields"""
        try:
            self.driver.get(f'{self.live_server_url}/login/')
            
            # Check for email field
            email_field = self.wait_for_element(By.NAME, 'email')
            email_ok = email_field.is_displayed()
            
            # Check for password field
            password_field = self.wait_for_element(By.NAME, 'password')
            password_ok = password_field.is_displayed()
            
            # Check for login button
            login_button = self.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"]')
            button_ok = login_button.is_displayed()
            
            # Log results
            self.log_test_result(
                'Login Page Render Test',
                all([email_ok, password_ok, button_ok]),
                None if all([email_ok, password_ok, button_ok]) else 'Missing required form elements'
            )
            
            # Assertions
            self.assertTrue(email_ok, 'Email field not found')
            self.assertTrue(password_ok, 'Password field not found')
            self.assertTrue(button_ok, 'Login button not found')
            
        except Exception as e:
            self.log_test_result('Login Page Render Test', False, str(e))
            raise
    
    def test_user_login_flow(self):
        """Test the complete login flow with valid credentials"""
        try:
            # Perform login
            self.login_user()
            
            # Check if redirected to home page
            current_url = self.driver.current_url
            is_home = self.live_server_url in current_url
            
            # Check for notification icon and badge
            notification_icon = self.wait_for_element(By.ID, 'notificationIcon')
            notification_badge = None
            if notification_icon:
                # Click notification icon to show notifications
                notification_icon.click()
                time.sleep(1)  # Wait for notifications to load
                
                # Look for notification badge or notification item
                notification_badge = self.wait_for_element(By.ID, 'notificationBadge')
                notification_item = self.wait_for_element(By.CLASS_NAME, 'notification-item')
                has_welcome = notification_item and ('Welcome back' in notification_item.text or 'Welcome to Madison' in notification_item.text)
            else:
                has_welcome = False
            
            # Log results
            self.log_test_result(
                'User Login Flow Test',
                is_home and has_welcome,
                None if (is_home and has_welcome) else 'Failed to redirect to home or show welcome notification'
            )
            
            # Assertions
            self.assertTrue(is_home, 'Not redirected to home page after login')
            self.assertTrue(has_welcome, 'Welcome notification not displayed after login')
            
        except Exception as e:
            self.log_test_result('User Login Flow Test', False, str(e))
            raise 
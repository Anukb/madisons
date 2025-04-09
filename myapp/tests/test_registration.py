from .test_base import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class RegistrationTests(BaseTest):
    def test_registration_page_render(self):
        """Test if registration page loads with all required fields"""
        try:
            self.driver.get(f'{self.live_server_url}/register/')
            
            # Check for all required fields
            username_field = self.wait_for_element(By.NAME, 'username')
            email_field = self.wait_for_element(By.NAME, 'email')
            password_field = self.wait_for_element(By.NAME, 'password')
            confirm_field = self.wait_for_element(By.NAME, 'confirm_password')
            first_name_field = self.wait_for_element(By.NAME, 'first_name')
            last_name_field = self.wait_for_element(By.NAME, 'last_name')
            submit_button = self.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"]')
            
            # Check if all elements are present
            fields_ok = all([
                username_field, email_field, password_field, confirm_field,
                first_name_field, last_name_field, submit_button
            ])
            
            # Log results
            self.log_test_result(
                'Registration Page Render Test',
                fields_ok,
                None if fields_ok else 'One or more registration form fields missing'
            )
            
            # Assertions
            self.assertTrue(fields_ok, 'Registration form fields not found')
            
        except Exception as e:
            self.log_test_result('Registration Page Render Test', False, str(e))
            raise
    
    def test_successful_registration(self):
        """Test successful user registration flow"""
        try:
            self.driver.get(f'{self.live_server_url}/register/')
            
            # Fill in registration form
            username_field = self.wait_for_element(By.NAME, 'username')
            email_field = self.wait_for_element(By.NAME, 'email')
            password_field = self.wait_for_element(By.NAME, 'password')
            confirm_field = self.wait_for_element(By.NAME, 'confirm_password')
            first_name_field = self.wait_for_element(By.NAME, 'first_name')
            last_name_field = self.wait_for_element(By.NAME, 'last_name')
            submit_button = self.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"]')
            
            if all([username_field, email_field, password_field, confirm_field, 
                   first_name_field, last_name_field, submit_button]):
                # Fill form
                username_field.send_keys('testuser2')
                email_field.send_keys('testuser2@example.com')
                password_field.send_keys('testpass123')
                confirm_field.send_keys('testpass123')
                first_name_field.send_keys('Test')
                last_name_field.send_keys('User')
                
                # Submit form
                submit_button.click()
                
                # Wait for redirect to login page
                time.sleep(2)
                is_login_page = '/login/' in self.driver.current_url
                
                # Check for success message
                success_message = self.wait_for_element(By.CLASS_NAME, 'alert-success')
                registration_success = success_message and 'successfully' in success_message.text.lower()
            else:
                is_login_page = False
                registration_success = False
            
            # Log results
            self.log_test_result(
                'Successful Registration Test',
                is_login_page and registration_success,
                None if (is_login_page and registration_success) else 'Registration failed or no success message'
            )
            
            # Assertions
            self.assertTrue(is_login_page, 'Not redirected to login page after registration')
            self.assertTrue(registration_success, 'No success message shown after registration')
            
        except Exception as e:
            self.log_test_result('Successful Registration Test', False, str(e))
            raise
    
    def test_duplicate_username_registration(self):
        """Test registration with existing username"""
        try:
            # First register a user successfully
            self.test_successful_registration()
            
            # Try registering with same username
            self.driver.get(f'{self.live_server_url}/register/')
            
            # Fill in registration form with same username
            username_field = self.wait_for_element(By.NAME, 'username')
            email_field = self.wait_for_element(By.NAME, 'email')
            password_field = self.wait_for_element(By.NAME, 'password')
            confirm_field = self.wait_for_element(By.NAME, 'confirm_password')
            first_name_field = self.wait_for_element(By.NAME, 'first_name')
            last_name_field = self.wait_for_element(By.NAME, 'last_name')
            submit_button = self.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"]')
            
            if all([username_field, email_field, password_field, confirm_field,
                   first_name_field, last_name_field, submit_button]):
                # Fill form with duplicate username
                username_field.send_keys('testuser2')
                email_field.send_keys('different@example.com')
                password_field.send_keys('testpass123')
                confirm_field.send_keys('testpass123')
                first_name_field.send_keys('Another')
                last_name_field.send_keys('User')
                
                # Submit form
                submit_button.click()
                
                # Check for error message
                time.sleep(1)
                error_message = self.wait_for_element(By.CLASS_NAME, 'alert-error')
                has_error = error_message and 'username already exists' in error_message.text.lower()
                
                # Should stay on registration page
                still_register_page = '/register/' in self.driver.current_url
            else:
                has_error = False
                still_register_page = False
            
            # Log results
            self.log_test_result(
                'Duplicate Username Test',
                has_error and still_register_page,
                None if (has_error and still_register_page) else 'No error message or wrong redirect'
            )
            
            # Assertions
            self.assertTrue(still_register_page, 'Left registration page after duplicate submission')
            self.assertTrue(has_error, 'No error message shown for duplicate username')
            
        except Exception as e:
            self.log_test_result('Duplicate Username Test', False, str(e))
            raise 
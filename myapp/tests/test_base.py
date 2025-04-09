from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from django.contrib.auth.models import User
from myapp.models import Category
import time
import logging
import os
import sys

class BaseTest(StaticLiveServerTestCase):
    def setUp(self):
        """Set up test environment before each test method"""
        # Set up logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.logger.info("🚀 Starting Selenium test setup...")
        
        # Set up Chrome options
        chrome_options = Options()
        
        # Check if we want to run in headless mode (can be controlled via environment variable)
        headless = os.environ.get('SELENIUM_HEADLESS', 'false').lower() == 'true'
        if headless:
            self.logger.info("Running in headless mode")
            chrome_options.add_argument('--headless')
        else:
            self.logger.info("Running in visible mode - you should see the browser window")
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1420,1080')
        chrome_options.add_argument('--log-level=1')  # Only show severe logs
        
        # Initialize Chrome WebDriver
        self.logger.info("🌐 Initializing Chrome WebDriver...")
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            # Set a reasonable page load timeout
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(2)  # Short implicit wait
            self.logger.info("✅ Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Chrome WebDriver: {str(e)}")
            raise
        
        # Create test user
        self.logger.info("👤 Creating test user...")
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.test_user.first_name = 'Test'
        self.test_user.last_name = 'User'
        self.test_user.save()
        self.logger.info("✅ Test user created successfully")
        
        # Create test category
        self.logger.info("📁 Creating test category...")
        self.test_category = Category.objects.create(
            name='Test Category',
            description='A test category'
        )
        self.logger.info("✅ Test category created successfully")
        
        # Store the base URL
        self.live_server_url = self.live_server_url
        self.logger.info(f"🌍 Test server URL: {self.live_server_url}")
        
        # Create screenshots directory if it doesn't exist
        os.makedirs('test_failures', exist_ok=True)
        
        self.logger.info("✅ Test setup completed successfully")
        
    def tearDown(self):
        """Clean up after each test method"""
        self.logger.info("🧹 Starting test cleanup...")
        
        if self.driver:
            self.logger.info("Closing browser...")
            try:
                self.driver.quit()
                self.logger.info("✅ Browser closed successfully")
            except Exception as e:
                self.logger.error(f"❌ Error closing browser: {str(e)}")
            
        # Clean up test user and category
        self.logger.info("Cleaning up test data...")
        self.test_user.delete()
        self.test_category.delete()
        self.logger.info("✅ Test data cleaned up successfully")
    
    def wait_for_element(self, by, value, timeout=10, condition="visible"):
        """Wait for an element with improved error handling and logging"""
        self.logger.info(f"⏳ Waiting for element: {by}={value} (timeout: {timeout}s, condition: {condition})")
        try:
            if condition == "visible":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, value))
                )
            elif condition == "clickable":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
            elif condition == "present":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            
            self.logger.info(f"✅ Element found: {by}={value}")
            # Add a small delay after finding element for stability
            time.sleep(0.5)
            return element
            
        except TimeoutException:
            self.logger.error(f"❌ Timeout waiting for element: {by}={value}")
            self.take_screenshot(f"timeout_{by}_{value}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error finding element {by}={value}: {str(e)}")
            self.take_screenshot(f"error_{by}_{value}")
            return None
    
    def take_screenshot(self, name):
        """Take a screenshot with timestamp"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = f"test_failures/{name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {str(e)}")
    
    def slow_type(self, element, text, delay=0.1):
        """Type text slowly to simulate human typing"""
        for char in text:
            element.send_keys(char)
            time.sleep(delay)
    
    def login_user(self):
        """Helper method to log in the test user with improved reliability"""
        self.logger.info("🔐 Attempting user login...")
        
        try:
            # Navigate to login page
            self.logger.info(f"Navigating to login page: {self.live_server_url}/login/")
            self.driver.get(f'{self.live_server_url}/login/')
            time.sleep(1)  # Wait for page load
            
            # Wait for and find form elements
            self.logger.info("Looking for login form elements...")
            email_input = self.wait_for_element(By.NAME, 'email', timeout=10, condition="visible")
            password_input = self.wait_for_element(By.NAME, 'password', timeout=5, condition="visible")
            submit_button = self.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"]', timeout=5, condition="clickable")
            
            if all([email_input, password_input, submit_button]):
                self.logger.info("Found all form elements, proceeding with login...")
                
                # Type credentials slowly
                self.logger.info("Entering email...")
                self.slow_type(email_input, 'testuser@example.com')
                
                self.logger.info("Entering password...")
                self.slow_type(password_input, 'testpass123')
                
                self.logger.info("Clicking submit button...")
                submit_button.click()
                
                # Wait for login to complete
                self.logger.info("Waiting for login to complete...")
                time.sleep(2)
                
                # Check for successful login
                success = '/login/' not in self.driver.current_url
                if success:
                    self.logger.info("✅ Login successful")
                    # Wait for home page to load
                    time.sleep(1)
                else:
                    self.logger.error("❌ Login failed - still on login page")
                    self.take_screenshot("login_failed")
                return success
            
            self.logger.error("❌ One or more login form elements not found")
            self.take_screenshot("login_form_missing")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Login attempt failed with error: {str(e)}")
            self.take_screenshot("login_error")
            return False
    
    def log_test_result(self, test_name, success, error_message=None):
        """Log test results with improved formatting"""
        result = '✅ PASSED' if success else '❌ FAILED'
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"Test: {test_name}")
        self.logger.info(f"Result: {result}")
        
        if error_message:
            self.logger.error(f"Error: {error_message}")
            
        if not success:
            self.take_screenshot(f"failed_{test_name}")
        
        self.logger.info(f"{'='*50}\n") 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def wait_for_element(driver, locator, timeout=10):
    """Wait for an element to be present and return it"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator))
    except TimeoutException:
        raise Exception(f"Element not found: {locator}")

def slow_type(element, text, delay=0.1):
    """Type text slowly into an element"""
    for character in text:
        element.send_keys(character)
        time.sleep(delay)
def take_screenshot(driver, filename):
    """Take screenshot and save to file"""
    driver.save_screenshot(filename)

def generate_test_email():
    """Generate a unique test email address"""
    import time
    return f"test_{int(time.time())}@example.com"
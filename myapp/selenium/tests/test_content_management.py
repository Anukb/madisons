from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_add_new_article():
    # Set Chrome options
    options = Options()
    # options.add_argument('--headless')  # Uncomment if you want headless
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialize Chrome WebDriver
    driver = webdriver.Chrome(options=options)

    try:
        # Test data
        login_url = "http://127.0.0.1:8000/login/"
        admin_email = "june@gmail.com"
        admin_password = "june5678"
        article_title = "Test Article"
        article_content = "This is a test article content."
        expected_title = "Madison Online Magazine"  # Correct title after login

        # Open login page
        driver.get(login_url)

        # Log in
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(admin_email)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(admin_password)
        password_field.submit()

        # Wait for the dashboard to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboard"))
        )

        # Navigate to add article page
        driver.get("http://127.0.0.1:8000/admin/articles/add/")  # Adjust URL as necessary

        # Fill in article details
        title_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "title"))
        )
        title_field.send_keys(article_title)

        content_field = driver.find_element(By.NAME, "content")
        content_field.send_keys(article_content)

        # Submit the article form
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Verify if article was added successfully
        assert "Article added successfully" in driver.page_source, "Failed to add article."

        logging.info("✅ Article added successfully!")

    except Exception as e:
        logging.error(f"❌ Failed to add article: {str(e)}")
        driver.save_screenshot("add_article_failure.png")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_add_new_article()
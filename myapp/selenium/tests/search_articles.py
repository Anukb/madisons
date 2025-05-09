import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class ArticleSearchTestCase(unittest.TestCase):

    def setUp(self):
        # Set up the WebDriver
        self.driver = webdriver.Chrome()
        self.driver.get('http://localhost:8000/')  # Home page URL
        self.wait = WebDriverWait(self.driver, 10)

    def test_search_articles(self):
        driver = self.driver
        
        try:
            # Find the search input field
            search_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, 'query'))
            )
            
            # Input search query and submit
            search_term = "kj"  # Test search term
            search_input.send_keys(search_term)
            search_input.send_keys(Keys.RETURN)
            
            # Wait for search results page to load
            self.wait.until(
                EC.title_contains("Search Results")
            )
            
            # Verify search results header
            results_header = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//h2[contains(text(), "Search Results for")]')
                )
            )
            self.assertIn(search_term, results_header.text)
            
            # Check if articles are displayed or no results message
            try:
                # Check for articles
                articles = driver.find_elements(By.CLASS_NAME, 'article-card')
                if articles:
                    print(f"Found {len(articles)} articles for search term: {search_term}")
                    # Verify at least one article contains the search term in title or description
                    first_article = articles[0]
                    article_text = first_article.text.lower()
                    self.assertTrue(
                        search_term.lower() in article_text,
                        f"Search term '{search_term}' not found in first article"
                    )
                else:
                    # Check for no results message
                    no_results = driver.find_element(By.CLASS_NAME, 'no-results')
                    self.assertIn("No articles found", no_results.text)
                    print("No results found for search term (expected behavior)")
                    
            except Exception as e:
                self.driver.save_screenshot("search_results_error.png")
                raise AssertionError(f"Error verifying search results: {str(e)}")
                
            print("Article search test completed successfully")
            
        except Exception as e:
            self.driver.save_screenshot("search_test_failure.png")
            raise AssertionError(f"Search test failed: {str(e)}")

    def tearDown(self):
        # Close the browser window
        self.driver.quit()

if __name__ == '__main__':
    unittest.main()
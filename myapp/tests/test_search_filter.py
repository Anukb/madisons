from .test_base import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class SearchFilterTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.login_user()
        
        # Create some test articles for searching
        self.create_test_articles()
    
    def create_test_articles(self):
        """Helper method to create test articles"""
        # Navigate to add article page
        self.driver.get(f'{self.live_server_url}/add-article/')
        
        # Create test articles with different titles and categories
        articles = [
            {
                'title': 'Test Python Article',
                'description': 'An article about Python programming',
                'category': 'Technology'
            },
            {
                'title': 'Fashion Trends 2024',
                'description': 'Latest fashion trends',
                'category': 'Fashion'
            },
            {
                'title': 'Healthy Recipes',
                'description': 'Collection of healthy recipes',
                'category': 'Food'
            }
        ]
        
        for article in articles:
            # Fill in article details
            title_input = self.wait_for_element(By.ID, 'title')
            description_input = self.wait_for_element(By.ID, 'description')
            category_select = self.wait_for_element(By.ID, 'category')
            publish_btn = self.wait_for_element(By.ID, 'publish')
            
            if all([title_input, description_input, category_select, publish_btn]):
                title_input.send_keys(article['title'])
                description_input.send_keys(article['description'])
                
                # Select category
                category_select.click()
                category_option = self.wait_for_element(
                    By.XPATH, 
                    f"//option[contains(text(), '{article['category']}')]"
                )
                if category_option:
                    category_option.click()
                
                # Publish article
                publish_btn.click()
                time.sleep(1)
    
    def test_search_functionality(self):
        """Test article search functionality"""
        try:
            self.driver.get(f'{self.live_server_url}/')
            
            # Find search input
            search_input = self.wait_for_element(By.CLASS_NAME, 'search-input')
            
            if search_input:
                # Search for Python article
                search_input.send_keys('Python')
                search_input.send_keys(Keys.RETURN)
                
                # Wait for search results
                time.sleep(2)
                
                # Check search results
                results = self.driver.find_elements(By.CLASS_NAME, 'article-card')
                has_results = len(results) > 0
                
                if has_results:
                    # Check if Python article is in results
                    first_result_title = results[0].find_element(By.TAG_NAME, 'h3').text
                    correct_result = 'Python' in first_result_title
                    
                    # Check if other articles are not in results
                    no_irrelevant = not any(
                        'Fashion' in result.find_element(By.TAG_NAME, 'h3').text
                        for result in results
                    )
                else:
                    correct_result = False
                    no_irrelevant = False
            else:
                has_results = False
                correct_result = False
                no_irrelevant = False
            
            # Log results
            self.log_test_result(
                'Search Functionality Test',
                all([has_results, correct_result, no_irrelevant]),
                None if all([has_results, correct_result, no_irrelevant]) 
                else 'Search results not found or incorrect'
            )
            
            # Assertions
            self.assertTrue(has_results, 'No search results found')
            self.assertTrue(correct_result, 'Expected article not found in search results')
            self.assertTrue(no_irrelevant, 'Irrelevant articles found in search results')
            
        except Exception as e:
            self.log_test_result('Search Functionality Test', False, str(e))
            raise
    
    def test_category_filter(self):
        """Test category filtering functionality"""
        try:
            self.driver.get(f'{self.live_server_url}/')
            
            # Find category filter
            category_select = self.wait_for_element(By.ID, 'categoryFilter')
            
            if category_select:
                # Select Technology category
                category_select.click()
                tech_option = self.wait_for_element(
                    By.XPATH,
                    "//option[contains(text(), 'Technology')]"
                )
                
                if tech_option:
                    tech_option.click()
                    
                    # Wait for filtered results
                    time.sleep(2)
                    
                    # Check filtered results
                    results = self.driver.find_elements(By.CLASS_NAME, 'article-card')
                    has_results = len(results) > 0
                    
                    if has_results:
                        # Check if Python article is in results
                        first_result_title = results[0].find_element(By.TAG_NAME, 'h3').text
                        correct_result = 'Python' in first_result_title
                        
                        # Check if other category articles are not in results
                        no_irrelevant = not any(
                            'Fashion' in result.find_element(By.TAG_NAME, 'h3').text or
                            'Healthy' in result.find_element(By.TAG_NAME, 'h3').text
                            for result in results
                        )
                    else:
                        correct_result = False
                        no_irrelevant = False
                else:
                    has_results = False
                    correct_result = False
                    no_irrelevant = False
            else:
                has_results = False
                correct_result = False
                no_irrelevant = False
            
            # Log results
            self.log_test_result(
                'Category Filter Test',
                all([has_results, correct_result, no_irrelevant]),
                None if all([has_results, correct_result, no_irrelevant]) 
                else 'Category filter not working correctly'
            )
            
            # Assertions
            self.assertTrue(has_results, 'No filtered results found')
            self.assertTrue(correct_result, 'Expected article not found in filtered results')
            self.assertTrue(no_irrelevant, 'Irrelevant category articles found in results')
            
        except Exception as e:
            self.log_test_result('Category Filter Test', False, str(e))
            raise
    
    def test_combined_search_filter(self):
        """Test combined search and category filter"""
        try:
            self.driver.get(f'{self.live_server_url}/')
            
            # Find search and filter elements
            search_input = self.wait_for_element(By.CLASS_NAME, 'search-input')
            category_select = self.wait_for_element(By.ID, 'categoryFilter')
            
            if all([search_input, category_select]):
                # Select Technology category
                category_select.click()
                tech_option = self.wait_for_element(
                    By.XPATH,
                    "//option[contains(text(), 'Technology')]"
                )
                
                if tech_option:
                    tech_option.click()
                    time.sleep(1)
                    
                    # Search for Python
                    search_input.send_keys('Python')
                    search_input.send_keys(Keys.RETURN)
                    
                    # Wait for results
                    time.sleep(2)
                    
                    # Check results
                    results = self.driver.find_elements(By.CLASS_NAME, 'article-card')
                    has_results = len(results) == 1  # Should only find one result
                    
                    if has_results:
                        # Check if correct article is found
                        result_title = results[0].find_element(By.TAG_NAME, 'h3').text
                        correct_result = 'Python' in result_title
                    else:
                        correct_result = False
                else:
                    has_results = False
                    correct_result = False
            else:
                has_results = False
                correct_result = False
            
            # Log results
            self.log_test_result(
                'Combined Search and Filter Test',
                has_results and correct_result,
                None if (has_results and correct_result) 
                else 'Combined search and filter not working correctly'
            )
            
            # Assertions
            self.assertTrue(has_results, 'No results found for combined search and filter')
            self.assertTrue(correct_result, 'Incorrect article found for combined search and filter')
            
        except Exception as e:
            self.log_test_result('Combined Search and Filter Test', False, str(e))
            raise 
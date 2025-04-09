from .test_base import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class ArticleManagementTests(BaseTest):
    def setUp(self):
        super().setUp()
        # Log in before running tests
        self.login_user()
    
    def test_create_article_draft(self):
        """Test creating a new article draft"""
        try:
            # Navigate to add article page
            self.driver.get(f'{self.live_server_url}/add-article/')
            
            # Fill in article details
            title_input = self.wait_for_element(By.ID, 'title')
            description_input = self.wait_for_element(By.ID, 'description')
            category_select = self.wait_for_element(By.ID, 'category')
            save_draft_btn = self.wait_for_element(By.ID, 'save-draft')
            
            # Check if all elements are found
            elements_ok = all([title_input, description_input, category_select, save_draft_btn])
            
            if elements_ok:
                # Fill in the form
                title_input.send_keys('Test Article Draft')
                description_input.send_keys('This is a test article description')
                
                # Select first category
                category_select.click()
                category_option = self.wait_for_element(By.CSS_SELECTOR, '#category option:not([value=""])')
                if category_option:
                    category_option.click()
                
                # Click save draft
                save_draft_btn.click()
                
                # Wait for redirect to drafts page
                time.sleep(2)
                is_drafts_page = '/user/drafts/' in self.driver.current_url
                
                # Check if draft appears in the list
                draft_title = self.wait_for_element(By.CLASS_NAME, 'draft-title')
                draft_saved = draft_title and 'Test Article Draft' in draft_title.text
            else:
                is_drafts_page = False
                draft_saved = False
            
            # Log results
            self.log_test_result(
                'Create Article Draft Test',
                is_drafts_page and draft_saved,
                None if (is_drafts_page and draft_saved) else 'Failed to create or find draft article'
            )
            
            # Assertions
            self.assertTrue(is_drafts_page, 'Not redirected to drafts page after saving')
            self.assertTrue(draft_saved, 'Draft article not found in drafts list')
            
        except Exception as e:
            self.log_test_result('Create Article Draft Test', False, str(e))
            raise
    
    def test_edit_article(self):
        """Test editing an existing article"""
        try:
            # First create a draft article
            self.test_create_article_draft()
            
            # Find and click edit button
            edit_btn = self.wait_for_element(By.CLASS_NAME, 'edit-btn')
            edit_btn_ok = edit_btn and edit_btn.is_displayed()
            
            if edit_btn_ok:
                edit_btn.click()
                
                # Wait for edit form to load
                title_input = self.wait_for_element(By.ID, 'title')
                description_input = self.wait_for_element(By.ID, 'description')
                
                # Update article content
                title_input.clear()
                title_input.send_keys('Updated Test Article')
                description_input.clear()
                description_input.send_keys('This is an updated test article')
                
                # Save changes
                save_btn = self.wait_for_element(By.ID, 'save-draft')
                save_btn.click()
                
                # Wait for save and check notification
                time.sleep(2)
                success_notification = self.wait_for_element(By.CLASS_NAME, 'notification.success')
                save_success = success_notification and 'successfully' in success_notification.text.lower()
            else:
                save_success = False
            
            # Log results
            self.log_test_result(
                'Edit Article Test',
                edit_btn_ok and save_success,
                None if (edit_btn_ok and save_success) else 'Failed to edit article'
            )
            
            # Assertions
            self.assertTrue(edit_btn_ok, 'Edit button not found')
            self.assertTrue(save_success, 'Article update not successful')
            
        except Exception as e:
            self.log_test_result('Edit Article Test', False, str(e))
            raise
    
    def test_publish_article(self):
        """Test publishing an article"""
        try:
            # First create a draft article
            self.test_create_article_draft()
            
            # Find and click edit button
            edit_btn = self.wait_for_element(By.CLASS_NAME, 'edit-btn')
            if edit_btn:
                edit_btn.click()
                
                # Wait for edit form and click publish
                publish_btn = self.wait_for_element(By.ID, 'publish')
                publish_btn.click()
                
                # Wait for publish and redirect
                time.sleep(2)
                is_dashboard = '/articles/dashboard/' in self.driver.current_url
                
                # Check if article appears in published list
                published_title = self.wait_for_element(By.CLASS_NAME, 'article-title')
                article_published = published_title and 'Test Article' in published_title.text
            else:
                is_dashboard = False
                article_published = False
            
            # Log results
            self.log_test_result(
                'Publish Article Test',
                is_dashboard and article_published,
                None if (is_dashboard and article_published) else 'Failed to publish article'
            )
            
            # Assertions
            self.assertTrue(is_dashboard, 'Not redirected to dashboard after publishing')
            self.assertTrue(article_published, 'Published article not found in dashboard')
            
        except Exception as e:
            self.log_test_result('Publish Article Test', False, str(e))
            raise 
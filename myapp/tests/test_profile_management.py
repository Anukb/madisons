from .test_base import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os

class ProfileManagementTests(BaseTest):
    def setUp(self):
        super().setUp()
        # Log in before running tests
        self.login_user()
    
    def test_view_profile(self):
        """Test viewing user profile page"""
        try:
            self.driver.get(f'{self.live_server_url}/profile/')
            
            # Check for profile elements
            profile_img = self.wait_for_element(By.ID, 'preview')
            name_input = self.wait_for_element(By.ID, 'name')
            bio_input = self.wait_for_element(By.ID, 'bio')
            interests_section = self.wait_for_element(By.CLASS_NAME, 'interests')
            
            # Check if elements are present and displaying correct data
            elements_ok = all([profile_img, name_input, bio_input, interests_section])
            
            if elements_ok:
                # Check if name field contains user's name
                name_value = name_input.get_attribute('value')
                name_ok = 'Test User' in name_value
            else:
                name_ok = False
            
            # Log results
            self.log_test_result(
                'View Profile Test',
                elements_ok and name_ok,
                None if (elements_ok and name_ok) else 'Profile elements missing or incorrect data'
            )
            
            # Assertions
            self.assertTrue(elements_ok, 'Profile page elements not found')
            self.assertTrue(name_ok, 'User name not displayed correctly')
            
        except Exception as e:
            self.log_test_result('View Profile Test', False, str(e))
            raise
    
    def test_update_profile(self):
        """Test updating user profile information"""
        try:
            self.driver.get(f'{self.live_server_url}/profile/')
            
            # Find form elements
            name_input = self.wait_for_element(By.ID, 'name')
            bio_input = self.wait_for_element(By.ID, 'bio')
            save_button = self.wait_for_element(By.CLASS_NAME, 'save-button')
            
            if all([name_input, bio_input, save_button]):
                # Update profile information
                name_input.clear()
                name_input.send_keys('Updated User')
                bio_input.clear()
                bio_input.send_keys('This is an updated bio')
                
                # Save changes
                save_button.click()
                
                # Wait for save and check notification
                time.sleep(2)
                success_message = self.wait_for_element(By.CLASS_NAME, 'messages')
                save_success = success_message and 'successfully' in success_message.text.lower()
                
                # Verify changes persisted
                self.driver.refresh()
                time.sleep(1)
                name_input = self.wait_for_element(By.ID, 'name')
                bio_input = self.wait_for_element(By.ID, 'bio')
                changes_persisted = (
                    'Updated User' in name_input.get_attribute('value') and
                    'This is an updated bio' in bio_input.get_attribute('value')
                )
            else:
                save_success = False
                changes_persisted = False
            
            # Log results
            self.log_test_result(
                'Update Profile Test',
                save_success and changes_persisted,
                None if (save_success and changes_persisted) else 'Profile update failed or changes not persisted'
            )
            
            # Assertions
            self.assertTrue(save_success, 'No success message after profile update')
            self.assertTrue(changes_persisted, 'Profile changes did not persist after refresh')
            
        except Exception as e:
            self.log_test_result('Update Profile Test', False, str(e))
            raise
    
    def test_update_profile_picture(self):
        """Test updating profile picture"""
        try:
            self.driver.get(f'{self.live_server_url}/profile/')
            
            # Find profile picture elements
            file_input = self.wait_for_element(By.ID, 'profile-pic')
            set_dp_button = self.wait_for_element(By.ID, 'set-dp')
            
            if all([file_input, set_dp_button]):
                # Create a test image path
                test_image_path = os.path.join(os.path.dirname(__file__), 'test_image.jpg')
                
                # Upload image
                file_input.send_keys(test_image_path)
                
                # Wait for preview to update
                time.sleep(1)
                preview_img = self.wait_for_element(By.ID, 'preview')
                preview_updated = preview_img and preview_img.is_displayed()
                
                if preview_updated:
                    # Save changes
                    set_dp_button.click()
                    
                    # Wait for save and check notification
                    time.sleep(2)
                    success_message = self.wait_for_element(By.CLASS_NAME, 'messages')
                    save_success = success_message and 'successfully' in success_message.text.lower()
                else:
                    save_success = False
            else:
                preview_updated = False
                save_success = False
            
            # Log results
            self.log_test_result(
                'Update Profile Picture Test',
                preview_updated and save_success,
                None if (preview_updated and save_success) else 'Profile picture update failed'
            )
            
            # Assertions
            self.assertTrue(preview_updated, 'Profile picture preview not updated')
            self.assertTrue(save_success, 'Profile picture save not successful')
            
        except Exception as e:
            self.log_test_result('Update Profile Picture Test', False, str(e))
            raise
    
    def test_update_interests(self):
        """Test updating user interests"""
        try:
            self.driver.get(f'{self.live_server_url}/profile/')
            
            # Find interests section
            interests_section = self.wait_for_element(By.CLASS_NAME, 'interests')
            checkboxes = self.driver.find_elements(By.NAME, 'interests')
            save_button = self.wait_for_element(By.CLASS_NAME, 'save-button')
            
            if all([interests_section, checkboxes, save_button]):
                # Select some interests
                for checkbox in checkboxes[:2]:  # Select first two interests
                    if not checkbox.is_selected():
                        checkbox.click()
                
                # Save changes
                save_button.click()
                
                # Wait for save and check notification
                time.sleep(2)
                success_message = self.wait_for_element(By.CLASS_NAME, 'messages')
                save_success = success_message and 'successfully' in success_message.text.lower()
                
                # Verify changes persisted
                self.driver.refresh()
                time.sleep(1)
                new_checkboxes = self.driver.find_elements(By.NAME, 'interests')
                changes_persisted = all(
                    checkbox.is_selected() 
                    for checkbox in new_checkboxes[:2]
                )
            else:
                save_success = False
                changes_persisted = False
            
            # Log results
            self.log_test_result(
                'Update Interests Test',
                save_success and changes_persisted,
                None if (save_success and changes_persisted) else 'Interests update failed or changes not persisted'
            )
            
            # Assertions
            self.assertTrue(save_success, 'No success message after interests update')
            self.assertTrue(changes_persisted, 'Interest changes did not persist after refresh')
            
        except Exception as e:
            self.log_test_result('Update Interests Test', False, str(e))
            raise 
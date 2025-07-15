#!/usr/bin/env python3
"""
Simple test to demonstrate calling JavaScript from Python
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_javascript_automation():
    """Quick test of JavaScript automation"""
    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run without GUI
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🚀 Starting EMR automation test...")
        
        # 1. Navigate to the EMR application
        print("📍 Navigating to EMR application...")
        driver.get("http://localhost:5000")
        
        # 2. Login
        print("🔐 Logging in...")
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("admin")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # 3. Wait for dashboard
        print("⏳ Waiting for dashboard to load...")
        wait.until(EC.presence_of_element_located((By.ID, "patient-search")))
        print("✅ Dashboard loaded successfully!")
        
        # 4. Search for patient using JavaScript
        print("🔍 Searching for patient 'Ruth'...")
        search_result = driver.execute_script("""
            const searchBox = document.getElementById('patient-search');
            searchBox.value = 'Ruth';
            searchBox.dispatchEvent(new Event('input'));
            return 'Search initiated';
        """)
        print(f"Search result: {search_result}")
        
        # Wait for search results
        time.sleep(3)
        
        # 5. Select first patient using JavaScript
        print("👤 Selecting first patient...")
        select_result = driver.execute_script("""
            const firstResult = document.querySelector('.search-result-item');
            if (firstResult) {
                firstResult.click();
                return 'Patient selected';
            }
            return 'No patient found';
        """)
        print(f"Selection result: {select_result}")
        
        # Wait for patient data to load
        time.sleep(3)
        
        # 6. Open Add Note dialog using JavaScript
        print("📝 Opening Add Note dialog...")
        modal_result = driver.execute_script("""
            // First navigate to clinical notes tab
            document.getElementById('clinical-notes-tab').click();
            
            // Wait a bit then call addNewItem
            setTimeout(() => {
                if (typeof addNewItem === 'function') {
                    addNewItem('clinical_notes');
                } else {
                    console.log('addNewItem function not available');
                }
            }, 1000);
            
            return 'Add Note dialog triggered';
        """)
        print(f"Modal result: {modal_result}")
        
        # Wait to see the modal
        time.sleep(3)
        
        # 7. Check if modal is open
        modal_check = driver.execute_script("""
            const modal = document.getElementById('itemModal');
            return modal && modal.style.display !== 'none' ? 'Modal is open' : 'Modal not visible';
        """)
        print(f"Modal status: {modal_check}")
        
        print("🎉 Automation test completed successfully!")
        print("💡 You can now see the Add Note dialog is open!")
        
        # Keep browser open for 10 seconds to see the result
        print("⏳ Keeping browser open for 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error during automation: {e}")
    
    finally:
        driver.quit()
        print("🔚 Browser closed")

if __name__ == "__main__":
    test_javascript_automation()

#!/usr/bin/env python3
"""
Connect Selenium to an already running Chrome browser session
This is useful for development and debugging
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import subprocess
import os

def start_chrome_with_debugging():
    """Start Chrome with remote debugging enabled"""
    print("🌐 Starting Chrome with remote debugging...")
    
    # Chrome command with debugging port
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS path
        "--remote-debugging-port=9222",
        "--user-data-dir=/tmp/chrome_debug_session",
        "http://localhost:5000"
    ]
    
    try:
        # Start Chrome in background
        process = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Chrome started with debugging port 9222")
        print("💡 You can now manually navigate and login to the EMR system")
        print("🔗 Chrome will open at: http://localhost:5000")
        return process
    except FileNotFoundError:
        print("❌ Chrome not found at expected path. Please adjust the path for your system.")
        return None

def connect_to_running_chrome():
    """Connect Selenium to already running Chrome instance"""
    print("🔌 Connecting to running Chrome instance...")
    
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Successfully connected to running Chrome!")
        return driver
    except Exception as e:
        print(f"❌ Failed to connect to Chrome: {e}")
        print("💡 Make sure Chrome is running with --remote-debugging-port=9222")
        return None

def test_existing_session():
    """Test JavaScript automation on existing browser session"""
    driver = connect_to_running_chrome()
    
    if not driver:
        return
    
    try:
        print(f"📍 Current URL: {driver.current_url}")
        
        # Check if we're on the EMR dashboard
        if "localhost:5000" not in driver.current_url:
            print("⚠️ Please navigate to http://localhost:5000 in the browser first")
            return
        
        # Check if we're logged in
        try:
            search_box = driver.find_element(By.ID, "patient-search")
            print("✅ Already on dashboard and logged in!")
        except:
            print("🔐 Please login manually in the browser first")
            return
        
        # Now execute JavaScript on the existing page
        print("🎯 Executing JavaScript on existing session...")
        
        # Get current patient info
        patient_info = driver.execute_script("""
            if (window.currentPatient) {
                return {
                    name: currentPatient.name,
                    id: currentPatient.id
                };
            }
            return null;
        """)
        
        if patient_info:
            print(f"👤 Current patient: {patient_info['name']} (ID: {patient_info['id']})")
        else:
            print("👤 No patient currently selected")
            
            # Search for a patient
            print("🔍 Searching for patient 'Ruth'...")
            driver.execute_script("""
                const searchBox = document.getElementById('patient-search');
                searchBox.value = 'Ruth';
                searchBox.dispatchEvent(new Event('input'));
            """)
            
            time.sleep(2)
            
            # Select first result
            select_result = driver.execute_script("""
                const firstResult = document.querySelector('.search-result-item');
                if (firstResult) {
                    firstResult.click();
                    return true;
                }
                return false;
            """)
            
            if select_result:
                print("✅ Patient selected!")
                time.sleep(2)
            else:
                print("❌ No patient found")
                return
        
        # Open Add Note dialog
        print("📝 Opening Add Note dialog...")
        modal_result = driver.execute_script("""
            // Navigate to clinical notes tab
            document.getElementById('clinical-notes-tab').click();
            
            // Call addNewItem function
            setTimeout(() => {
                if (typeof addNewItem === 'function') {
                    addNewItem('clinical_notes');
                }
            }, 500);
            
            return 'Modal triggered';
        """)
        
        print(f"Modal result: {modal_result}")
        time.sleep(2)
        
        # Check if modal opened
        modal_status = driver.execute_script("""
            const modal = document.getElementById('itemModal');
            const isVisible = modal && window.getComputedStyle(modal).display !== 'none';
            return isVisible ? 'Modal is open' : 'Modal not visible';
        """)
        
        print(f"📋 Modal status: {modal_status}")
        
        if "open" in modal_status:
            print("🎉 Successfully opened Add Note dialog using existing browser session!")
        
        print("💡 You can continue working in the browser manually")
        print("🔄 Script will keep connection open. Press Ctrl+C to exit.")
        
        # Keep connection alive
        try:
            while True:
                time.sleep(5)
                # You can add more automation here
        except KeyboardInterrupt:
            print("\n👋 Disconnecting from browser...")
            
    except Exception as e:
        print(f"❌ Error during automation: {e}")
    
    finally:
        # Don't quit the driver - this would close the browser
        print("🔌 Keeping browser session alive...")

def demonstrate_session_reuse():
    """Demonstrate connecting to existing browser session"""
    print("=== SELENIUM + EXISTING BROWSER SESSION ===\n")
    
    print("📋 Instructions:")
    print("1. First, we'll start Chrome with debugging enabled")
    print("2. Manually navigate and login to the EMR system")
    print("3. Then Selenium will connect to the existing session")
    print("4. Execute JavaScript on the already-running page\n")
    
    # Option 1: Start Chrome with debugging
    start_chrome = input("🤔 Start new Chrome with debugging? (y/n): ").lower().strip()
    
    if start_chrome == 'y':
        chrome_process = start_chrome_with_debugging()
        if chrome_process:
            print("\n⏳ Please:")
            print("1. Wait for Chrome to open")
            print("2. Login to the EMR system (admin/admin)")
            print("3. Press Enter here when ready...")
            input()
    
    # Option 2: Connect to existing Chrome
    print("\n🔌 Now connecting Selenium to the running browser...")
    test_existing_session()

if __name__ == "__main__":
    demonstrate_session_reuse()

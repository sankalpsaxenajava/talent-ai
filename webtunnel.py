from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import os
import random
import traceback

# Set up Chrome WebDriver with anti-detection
options = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
wait = WebDriverWait(driver, 60)

def is_device_connected():
    """Check if any device is connected via ADB"""
    devices = os.popen("adb devices").read().strip().split("\n")
    if len(devices) <= 1:
        print("No mobile device found. Please connect your phone via USB.")
        return False
    return True

# **Check if Internet is Active on Mobile**
def is_internet_available():
    try:
        """Check if mobile internet is active"""
        print("Checking mobile internet connection...")
        if not is_device_connected():
            driver.quit()
            print("Browser closed")
            return False

        print("Checking mobile internet connection...")
        # status = os.popen("adb shell dumpsys connectivity | grep 'Active default'").read()
        status = os.popen('adb shell dumpsys connectivity | findstr "Active default"').read()

        if "Active default" in status:
            print("Internet is active on mobile.")
            return True
        else:
            print("No internet detected on mobile. Please enable mobile data.")
            driver.quit()
            print("Browser closed") 
            return False
    except Exception as e:
        print(f"Error checking internet connection: {e}")
        driver.quit()
        print("Browser closed")
        return False

# **Enable USB Tethering**
def enable_usb_tethering():
    print("Enabling USB Tethering...")
    try:
        os.system("adb shell svc usb setFunctions rndis")
        os.system("adb shell settings put global tether_dun_required 0")
        print("USB Tethering Enabled!")
    except Exception as e:
        print(f"Error enabling USB tethering: {e}")

# **Check if Website is Reachable**
def is_website_accessible(url):
    try:
        driver.set_page_load_timeout(10)  # Wait max 10 seconds
        driver.get(url)
        print(f"Website {url} loaded successfully!")
        return True
    except TimeoutException:
        print("Website is taking too long to load! Possible VPN issue.")
        return False
    except WebDriverException:
        print("Website is blocked or unreachable. Try using a VPN.")
        return False

# **Handle Popups**
def close_popups():
    try:
        while True:
            popup_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'popup-close')]")
            if popup_buttons:
                for btn in popup_buttons:
                    driver.execute_script("arguments[0].click();", btn)
                    print("Closed a popup.")
                time.sleep(2)  # Small wait to check for more popups
            else:
                break  # No more popups
    except Exception as e:
        print(f"Error handling popups: {e}")

def check_vpn_block():
    """Check if the website is blocked due to VPN restriction"""
    try:
        print("🔄 Checking if the website is VPN blocked...")
        driver.get("https://www.mistycasino2.com/")
        time.sleep(5)

        vpn_block_js = driver.execute_script(
            'return document.querySelector("body > div > div.country-block-info") !== null;'
        )

        if vpn_block_js:
            print("❌ Country Blocked: Please use VPN, this site is blocked outside Turkey.")
            driver.quit()
            exit()  

        root_element_js = driver.execute_script(
            'return document.querySelector("#root") !== null;'
        )

        if root_element_js:
            print("✅ Website loaded successfully!")
            return True
        else:
            print("⚠️ Website failed to load properly!")
            print("❌ Please use VPN, this site is blocked outside Turkey.")
            driver.quit()
            exit()

    except Exception as e:
        print(f"⚠️ Error checking VPN block: {e}")
        driver.quit()
        exit()



# **Main Script Execution**
if is_internet_available():
    enable_usb_tethering()
    
    website_url = "https://www.mistycasino2.com/"
    if check_vpn_block():
        
        if is_website_accessible(website_url):
            try:
                print("Navigating to the website...")
                driver.get(website_url)

                # Handle Popups at start
                close_popups()

                print("Starting signup process...")
                signup_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'brand-btn') and .//span[text()='Kaydol']]")
                ))
                driver.execute_script("arguments[0].click();", signup_button)
                print("Signup button clicked.")
                time.sleep(5)

                # Fill the form
                username = f"test{random.randint(100, 999)}"
                username_field = wait.until(EC.element_to_be_clickable((By.ID, "userName")))
                username_field.clear()
                username_field.send_keys(username)
                print(f"Entered username: {username}")

                password_field = wait.until(EC.element_to_be_clickable((By.ID, "password")))
                password_field.clear()
                password_field.send_keys("Test@1234")
                print("Entered password.")

                confirm_password_field = wait.until(EC.element_to_be_clickable((By.ID, "confirmPassword")))
                confirm_password_field.clear()
                confirm_password_field.send_keys("Test@1234")
                print("Entered confirm password.")

                # Click the submit button
                submit_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[5]/div/div/div/div[2]/div[2]/div[1]/button")
                ))
                driver.execute_script("arguments[0].click();", submit_button)
                print("Signup completed!")

                # Handle popups after signup
                print("Checking for popups after signup...")
                try:
                    last_popup = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div/button/i")))
                    driver.execute_script("arguments[0].click();", last_popup)
                    print("Closed the last popup after signup.")
                except TimeoutException:
                    print("No final popup detected after signup.")

                time.sleep(2)
                # close_popups()

                # Check if user is logged in
                # try:
                #     wait.until(EC.presence_of_element_located(
                #         (By.XPATH, "//span[contains(text(), 'Welcome') or contains(text(), 'Dashboard')]")
                #     ))
                #     print("Login successful. Main page loaded.")
                # except TimeoutException:
                #     print("Login failed or page did not load correctly.")
                
            except TimeoutException:
                print("Error: Page took too long to load!")
            except Exception as e:
                print(f"Unexpected error: {e}")
                print(traceback.format_exc())

        else:
            print("Exiting script due to website issue.")

else:
    print("Exiting script due to no internet connection.")

driver.quit()
print("Browser closed")

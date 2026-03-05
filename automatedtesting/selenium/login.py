#!/usr/bin/env python
"""
Selenium Functional UI Test Suite for SauceDemo
Performs login tests and outputs logs to selenium-test.log
"""

import logging
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# Configure logging to output to both file and console
def setup_logging():
    """Configure logging to write to selenium-test.log file"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_dir = 'log'
    
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'selenium-test-{timestamp}.log')
    
    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


# Initialize logger
logger = setup_logging()


def get_driver(headless=False):
    """
    Initialize and return Chrome WebDriver
    
    Args:
        headless (bool): Run in headless mode for CI/CD environments
    
    Returns:
        webdriver.Chrome: Configured Chrome driver instance
    """
    logger.info('Initializing Chrome WebDriver...')
    
    options = ChromeOptions()
    
    # Always add CI-safe flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-networking")

    if headless:
        logger.info('Running in headless mode')
        options.add_argument("--headless=new")  # Chrome 112+ requires --headless=new
    
    try:
        driver = webdriver.Chrome(options=options)
        logger.info('Chrome WebDriver initialized successfully')
        return driver
    except Exception as e:
        logger.error(f'Failed to initialize Chrome WebDriver: {str(e)}')
        raise


def login(driver, username, password):
    """
    Perform login operation
    
    Args:
        driver: Selenium WebDriver instance
        username (str): Username for login
        password (str): Password for login
    
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        logger.info(f'Attempting to login with username: {username}')
        
        # Navigate to login page
        url = 'https://www.saucedemo.com/'
        logger.info(f'Navigating to {url}')
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Find and fill username field
        logger.info('Locating username field...')
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, 'user-name'))
        )
        username_field.clear()
        username_field.send_keys(username)
        logger.info(f'Username "{username}" entered successfully')
        
        # Find and fill password field
        logger.info('Locating password field...')
        password_field = driver.find_element(By.ID, 'password')
        password_field.clear()
        password_field.send_keys(password)
        logger.info('Password entered successfully')
        
        # Click login button
        logger.info('Locating and clicking login button...')
        login_button = driver.find_element(By.ID, 'login-button')
        login_button.click()
        logger.info('Login button clicked')
        
        # Wait for products page to load (indicates successful login)
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'inventory_list'))
        )
        logger.info('Login successful - Products page loaded')
        
        return True
        
    except TimeoutException:
        logger.error('Timeout: Page elements took too long to load')
        return False
    except NoSuchElementException as e:
        logger.error(f'Element not found: {str(e)}')
        return False
    except Exception as e:
        logger.error(f'Login failed with error: {str(e)}')
        return False


def test_successful_login():
    """Test Case 1: Successful login with valid credentials"""
    logger.info('=' * 80)
    logger.info('TEST CASE 1: Successful Login with Valid Credentials')
    logger.info('=' * 80)
    
    driver = None
    try:
        # Use environment variable to determine headless mode (set in CI/CD)
        headless = os.getenv('HEADLESS', '0') in ('1', 'true', 'True', 'TRUE')
        driver = get_driver(headless=headless)
        
        # Perform login
        result = login(driver, 'standard_user', 'secret_sauce')
        
        if result:
            # Verify we're on products page
            current_url = driver.current_url
            logger.info(f'Current URL: {current_url}')
            
            if 'inventory.html' in current_url:
                logger.info('✓ TEST PASSED: Successfully logged in and redirected to products page')
                
                # Get page title
                page_title = driver.title
                logger.info(f'Page title: {page_title}')
                
                # Count products
                products = driver.find_elements(By.CLASS_NAME, 'inventory_item')
                logger.info(f'Number of products displayed: {len(products)}')
                
                return True
            else:
                logger.error('✗ TEST FAILED: Not redirected to products page')
                return False
        else:
            logger.error('✗ TEST FAILED: Login unsuccessful')
            return False
            
    except Exception as e:
        logger.error(f'✗ TEST FAILED: Exception occurred - {str(e)}')
        return False
    finally:
        if driver:
            logger.info('Closing browser...')
            driver.quit()
            logger.info('Browser closed')


def test_invalid_login():
    """Test Case 2: Login attempt with invalid credentials"""
    logger.info('=' * 80)
    logger.info('TEST CASE 2: Login with Invalid Credentials')
    logger.info('=' * 80)
    
    driver = None
    try:
        headless = os.getenv('HEADLESS', '0') in ('1', 'true', 'True', 'TRUE')
        driver = get_driver(headless=headless)
        
        logger.info('Navigating to login page...')
        driver.get('https://www.saucedemo.com/')
        
        wait = WebDriverWait(driver, 10)
        
        # Enter invalid credentials
        logger.info('Entering invalid credentials...')
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, 'user-name'))
        )
        username_field.send_keys('invalid_user')
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys('invalid_password')
        
        login_button = driver.find_element(By.ID, 'login-button')
        login_button.click()
        
        # Check for error message
        logger.info('Checking for error message...')
        error_message = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="error"]'))
        )
        
        error_text = error_message.text
        logger.info(f'Error message displayed: {error_text}')
        
        if 'Username and password do not match' in error_text:
            logger.info('✓ TEST PASSED: Appropriate error message displayed for invalid credentials')
            return True
        else:
            logger.error('✗ TEST FAILED: Unexpected error message')
            return False
            
    except Exception as e:
        logger.error(f'✗ TEST FAILED: Exception occurred - {str(e)}')
        return False
    finally:
        if driver:
            logger.info('Closing browser...')
            driver.quit()
            logger.info('Browser closed')


def test_locked_user():
    """Test Case 3: Login attempt with locked out user"""
    logger.info('=' * 80)
    logger.info('TEST CASE 3: Login with Locked Out User')
    logger.info('=' * 80)
    
    driver = None
    try:
        headless = os.getenv('HEADLESS', '0') in ('1', 'true', 'True', 'TRUE')
        driver = get_driver(headless=headless)
        
        logger.info('Navigating to login page...')
        driver.get('https://www.saucedemo.com/')
        
        wait = WebDriverWait(driver, 10)
        
        # Enter locked user credentials
        logger.info('Entering locked user credentials...')
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, 'user-name'))
        )
        username_field.send_keys('locked_out_user')
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys('secret_sauce')
        
        login_button = driver.find_element(By.ID, 'login-button')
        login_button.click()
        
        # Check for locked out error message
        logger.info('Checking for locked out error message...')
        error_message = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="error"]'))
        )
        
        error_text = error_message.text
        logger.info(f'Error message displayed: {error_text}')
        
        if 'locked out' in error_text.lower():
            logger.info('✓ TEST PASSED: User locked out message displayed correctly')
            return True
        else:
            logger.error('✗ TEST FAILED: Expected locked out message not found')
            return False
            
    except Exception as e:
        logger.error(f'✗ TEST FAILED: Exception occurred - {str(e)}')
        return False
    finally:
        if driver:
            logger.info('Closing browser...')
            driver.quit()
            logger.info('Browser closed')


def test_add_to_cart():
    """Test Case 4: Add product to cart after successful login"""
    logger.info('=' * 80)
    logger.info('TEST CASE 4: Add Product to Cart')
    logger.info('=' * 80)
    
    driver = None
    try:
        headless = os.getenv('HEADLESS', '0') in ('1', 'true', 'True', 'TRUE')
        driver = get_driver(headless=headless)
        
        # Login first
        if not login(driver, 'standard_user', 'secret_sauce'):
            logger.error('✗ TEST FAILED: Could not login')
            return False
        
        wait = WebDriverWait(driver, 15)
        
        # Wait for inventory list to be fully loaded
        logger.info('Waiting for inventory list...')
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'inventory_list')))
        
        # Try data-test attribute first (most stable), fall back to id prefix, then class
        logger.info('Locating "Add to cart" button for first product...')
        add_to_cart_button = None
        for selector, by in [
            ('[data-test^="add-to-cart"]', By.CSS_SELECTOR),
            ('[id^="add-to-cart"]',        By.CSS_SELECTOR),
            ('.btn_inventory',             By.CSS_SELECTOR),
            ('.inventory_item button',     By.CSS_SELECTOR),
        ]:
            try:
                add_to_cart_button = wait.until(EC.element_to_be_clickable((by, selector)))
                logger.info(f'Found add-to-cart button with selector: {selector}')
                break
            except TimeoutException:
                logger.info(f'Selector {selector!r} not found, trying next...')
        
        if add_to_cart_button is None:
            logger.error('✗ TEST FAILED: Could not locate any add-to-cart button')
            return False
        
        # Get product name (optional — don't fail if not found)
        try:
            product_name = driver.find_element(By.CSS_SELECTOR, '.inventory_item_name').text
            logger.info(f'Adding product to cart: {product_name}')
        except NoSuchElementException:
            logger.info('Adding first inventory item to cart (name element not found)')
        
        add_to_cart_button.click()
        logger.info('Product added to cart')
        
        # Verify cart badge shows 1 item — try data-test first, fall back to class name
        logger.info('Verifying cart badge...')
        cart_badge = None
        for selector, by in [
            ('[data-test="shopping-cart-badge"]', By.CSS_SELECTOR),
            ('.shopping_cart_badge',              By.CSS_SELECTOR),
            ('.shopping_cart_badge',              By.CLASS_NAME),
        ]:
            try:
                cart_badge = wait.until(EC.visibility_of_element_located((by, selector)))
                logger.info(f'Found cart badge with selector: {selector}')
                break
            except TimeoutException:
                logger.info(f'Badge selector {selector!r} not found, trying next...')
        
        if cart_badge is None:
            logger.error('✗ TEST FAILED: Cart badge did not appear after adding item')
            return False
        
        cart_count = cart_badge.text
        logger.info(f'Cart badge count: {cart_count}')
        
        if cart_count == '1':
            logger.info('✓ TEST PASSED: Product successfully added to cart')
            return True
        else:
            logger.error(f'✗ TEST FAILED: Expected cart count 1, but got {cart_count}')
            return False
            
    except Exception as e:
        logger.error(f'✗ TEST FAILED: Exception occurred - {str(e)}')
        return False
    finally:
        if driver:
            logger.info('Closing browser...')
            driver.quit()
            logger.info('Browser closed')


def run_all_tests():
    """Execute all test cases and report results"""
    logger.info('*' * 80)
    logger.info('SELENIUM FUNCTIONAL UI TEST SUITE - STARTING')
    logger.info(f'Test execution started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info('*' * 80)
    
    test_results = []
    
    # Run all test cases
    test_results.append(('Test Successful Login', test_successful_login()))
    test_results.append(('Test Invalid Login', test_invalid_login()))
    test_results.append(('Test Locked User', test_locked_user()))
    test_results.append(('Test Add to Cart', test_add_to_cart()))
    
    # Summary report
    logger.info('*' * 80)
    logger.info('TEST EXECUTION SUMMARY')
    logger.info('*' * 80)
    
    passed = sum(1 for _, result in test_results if result)
    failed = len(test_results) - passed
    
    for test_name, result in test_results:
        status = '✓ PASSED' if result else '✗ FAILED'
        logger.info(f'{test_name}: {status}')
    
    logger.info('-' * 80)
    logger.info(f'Total Tests: {len(test_results)}')
    logger.info(f'Passed: {passed}')
    logger.info(f'Failed: {failed}')
    logger.info(f'Success Rate: {(passed/len(test_results)*100):.2f}%')
    logger.info('*' * 80)
    logger.info(f'Test execution completed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info('*' * 80)
    
    # Exit with appropriate status code
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    run_all_tests()


import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import logging
import os
import sys
import platform

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CheeseScraper:
    def __init__(self):
        self.url = "https://shop.kimelo.com/department/cheese/3365"
        # Get the project root directory
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.products = []

    def setup_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Get the Chrome driver path
            try:
                driver_path = ChromeDriverManager().install()
                logger.info(f"Chrome driver path: {driver_path}")

                # Verify the driver file exists
                if not os.path.exists(driver_path):
                    raise FileNotFoundError(f"Chrome driver not found at: {driver_path}")

                # Create service with explicit path
                service = Service(executable_path="C:/Users/admin/Downloads/chromedriver-win64/chromedriver.exe")

                # Initialize Chrome with explicit service
                driver = webdriver.Chrome(
                    service=service,
                    options=chrome_options
                )

                driver.implicitly_wait(10)
                logger.info("Chrome WebDriver initialized successfully")
                return driver

            except Exception as e:
                logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
                logger.error(f"Python version: {sys.version}")
                logger.error(f"Current working directory: {os.getcwd()}")
                raise

        except Exception as e:
            logger.error(f"Error in setup_driver: {str(e)}")
            raise

    def wait_for_element(self, driver, by, value, timeout=10):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.warning(f"Element not found: {value}. Error: {str(e)}")
            return None

    def scrape_product(self, product_element):
        try:
            # Extract product details with explicit waits
            title = self.wait_for_element(product_element, By.CSS_SELECTOR, "p.chakra-text.css-pbtft")
            if not title:
                logger.warning("Could not find product title")
                return None
            title = title.text.strip()

            # Get price information
            price_container = self.wait_for_element(product_element, By.CSS_SELECTOR, "div.css-j6qzfh")
            if not price_container:
                logger.warning("Could not find price container")
                return None

            price = self.wait_for_element(price_container, By.CSS_SELECTOR, "b.chakra-text.css-1vhzs63")
            if not price:
                logger.warning("Could not find product price")
                return None
            price = price.text.strip()

            # Get price per unit
            price_per_unit = self.wait_for_element(price_container, By.CSS_SELECTOR, "span.chakra-badge.css-ff7g47")
            price_per_unit = price_per_unit.text.strip() if price_per_unit else ""

            # Get brand/manufacturer
            brand = self.wait_for_element(product_element, By.CSS_SELECTOR, "p.chakra-text.css-w6ttxb")
            brand = brand.text.strip() if brand else ""

            # Get product URL
            product_url = product_element.get_attribute("href")
            if not product_url:
                logger.warning("Could not find product URL")
                return None

            # Get product image
            image_url = ""
            try:
                img_element = self.wait_for_element(product_element, By.CSS_SELECTOR, "img.object-contain")
                if img_element:
                    image_url = img_element.get_attribute("src")
            except Exception as e:
                logger.warning(f"Could not find product image: {str(e)}")

            # Create product metadata
            metadata = {
                "title": title,
                "price": price,
                "price_per_unit": price_per_unit,
                "brand": brand,
                "image_url": image_url,
                "product_url": product_url,
                "category": "Cheese",
            }

            logger.info(f"Successfully scraped product: {title}")
            return metadata

        except Exception as e:
            logger.error(f"Error scraping product: {str(e)}")
            return None

    def scrape(self):
        try:
            self.driver = self.setup_driver()
            logger.info(f"Starting to scrape: {self.url}")

            self.driver.get(self.url)
            time.sleep(3)  # Wait for initial page load

            # Scroll to load all products
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Get all product elements - updated selector
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.css-0 a[role='link']"))
            )
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.css-0 a[role='link']")
            logger.info(f"Found {len(product_elements)} product elements")

            for product_element in product_elements:
                product_data = self.scrape_product(product_element)
                if product_data:
                    self.products.append(product_data)
                    logger.info(f"Scraped: {product_data['title']}")

            # Save raw data
            output_file = self.data_dir / "cheese_raw.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)

            logger.info(f"Successfully scraped {len(self.products)} products")
            logger.info(f"Data saved to: {output_file}")

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise
        finally:
            if hasattr(self, 'driver'):
                try:
                    logger.info("Closing Chrome WebDriver")
                    self.driver.quit()  # Try to quit gracefully
                except Exception as e:
                    logger.error(f"Error during WebDriver shutdown: {str(e)}")
                logger.info("Chrome WebDriver closed")

if __name__ == "__main__":
    try:
        scraper = CheeseScraper()
        scraper.scrape()
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise

print(platform.architecture())
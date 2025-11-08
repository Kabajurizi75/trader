import time
import logging
from datetime import datetime
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException
)
import json
import re

logger = logging.getLogger(__name__)

class MarketDataAgent:
    """
    Autonomous browser agent for scraping market data from various sources
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait = None
        
        # Initialize Chrome options for Docker compatibility
        self.chrome_options = self._setup_chrome_options()
        
    def _setup_chrome_options(self) -> Options:
        """Setup Chrome options for headless operation and Docker compatibility"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Docker-compatible options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_argument('--window-size=1920,1080')
        
        # Anti-detection measures
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--accept-language=en-US,en;q=0.9')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options
    
    def _initialize_driver(self):
        """Initialize the Chrome WebDriver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, self.timeout)
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _close_driver(self):
        """Close the WebDriver safely"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def _handle_captcha_detection(self) -> bool:
        """Detect if a CAPTCHA is present on the page"""
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "cloudflare",
            "verify you are human",
            "security check"
        ]
        
        try:
            page_source = self.driver.page_source.lower()
            for indicator in captcha_indicators:
                if indicator in page_source:
                    logger.warning(f"CAPTCHA detected: {indicator}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {e}")
            return False
    
    def scrape_coinmarketcap_bitcoin(self) -> Dict:
        """
        Scrape Bitcoin price and volume data from CoinMarketCap
        """
        url = "https://coinmarketcap.com/currencies/bitcoin/"
        
        try:
            if not self.driver:
                self._initialize_driver()
            
            logger.info(f"Navigating to CoinMarketCap: {url}")
            self.driver.get(url)
            
            # Check for CAPTCHA
            if self._handle_captcha_detection():
                raise Exception("CAPTCHA detected - scraping blocked")
            
            # Wait for price element to load
            price_selector = "span.sc-65e7f566-0.clvjgF.base-text"
            try:
                price_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, price_selector))
                )
                price_text = price_element.text
                price = self._extract_price(price_text)
            except TimeoutException:
                # Fallback selectors
                fallback_selectors = [
                    "[data-role='coin-price']",
                    ".priceValue",
                    "[class*='price']",
                    "span[class*='price']"
                ]
                
                price = None
                for selector in fallback_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        price_text = element.text
                        price = self._extract_price(price_text)
                        if price:
                            break
                    except NoSuchElementException:
                        continue
                
                if not price:
                    raise Exception("Could not find price element with any selector")
            
            # Try to get volume data
            volume = None
            volume_selectors = [
                "[data-role='coin-volume']",
                ".statsValue",
                "[class*='volume']"
            ]
            
            for selector in volume_selectors:
                try:
                    volume_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    volume_text = volume_element.text
                    volume = self._extract_volume(volume_text)
                    if volume:
                        break
                except NoSuchElementException:
                    continue
            
            # Get market cap if available
            market_cap = None
            try:
                market_cap_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='market-cap']")
                if market_cap_elements:
                    market_cap = self._extract_price(market_cap_elements[0].text)
            except Exception:
                pass
            
            return {
                'symbol': 'BTC',
                'price': price,
                'volume_24h': volume,
                'market_cap': market_cap,
                'source': 'coinmarketcap',
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error scraping CoinMarketCap: {e}")
            return {
                'symbol': 'BTC',
                'price': None,
                'volume_24h': None,
                'market_cap': None,
                'source': 'coinmarketcap',
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def scrape_tradingview_data(self, symbol: str = "BTCUSDT") -> Dict:
        """
        Scrape trading data from TradingView using XPath and dynamic loading
        """
        url = f"https://www.tradingview.com/symbols/{symbol}/"
        
        try:
            if not self.driver:
                self._initialize_driver()
            
            logger.info(f"Navigating to TradingView: {url}")
            self.driver.get(url)
            
            # Wait for dynamic content to load
            time.sleep(5)
            
            # Check for CAPTCHA
            if self._handle_captcha_detection():
                raise Exception("CAPTCHA detected - scraping blocked")
            
            # Try multiple XPath selectors for price
            price_xpaths = [
                "//span[@class='tv-symbol-price-quote__value js-symbol-last']",
                "//div[@class='tv-symbol-header__short-title']//span[contains(@class, 'js-symbol-last')]",
                "//span[contains(@class, 'tv-symbol-price-quote__value')]",
                "//*[@data-field='last_price']",
                "//span[contains(@class, 'last-price')]"
            ]
            
            price = None
            for xpath in price_xpaths:
                try:
                    price_element = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    price_text = price_element.text
                    price = self._extract_price(price_text)
                    if price:
                        break
                except TimeoutException:
                    continue
            
            # Try to get change percentage
            change_percent = None
            change_xpaths = [
                "//span[contains(@class, 'tv-symbol-price-quote__change-percent')]",
                "//span[contains(@class, 'change-percent')]",
                "//*[@data-field='change_percent']"
            ]
            
            for xpath in change_xpaths:
                try:
                    change_element = self.driver.find_element(By.XPATH, xpath)
                    change_text = change_element.text
                    change_percent = self._extract_percentage(change_text)
                    if change_percent is not None:
                        break
                except NoSuchElementException:
                    continue
            
            # Try to get volume
            volume = None
            volume_xpaths = [
                "//span[@data-field='volume']",
                "//span[contains(@class, 'volume')]",
                "//*[contains(text(), 'Volume')]//following-sibling::*"
            ]
            
            for xpath in volume_xpaths:
                try:
                    volume_element = self.driver.find_element(By.XPATH, xpath)
                    volume_text = volume_element.text
                    volume = self._extract_volume(volume_text)
                    if volume:
                        break
                except NoSuchElementException:
                    continue
            
            return {
                'symbol': symbol,
                'price': price,
                'change_percent': change_percent,
                'volume': volume,
                'source': 'tradingview',
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error scraping TradingView: {e}")
            return {
                'symbol': symbol,
                'price': None,
                'change_percent': None,
                'volume': None,
                'source': 'tradingview',
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text string"""
        if not text:
            return None
        
        try:
            # Remove currency symbols and commas
            clean_text = re.sub(r'[$,€£¥₿]', '', text)
            # Find price pattern
            price_match = re.search(r'([\d,]+\.?\d*)', clean_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                return float(price_str)
        except (ValueError, AttributeError) as e:
            logger.error(f"Error extracting price from '{text}': {e}")
        
        return None
    
    def _extract_volume(self, text: str) -> Optional[str]:
        """Extract volume from text string"""
        if not text:
            return None
        
        try:
            # Look for volume patterns (e.g., "1.23B", "456.78M", "12,345,678")
            volume_match = re.search(r'([\d,]+\.?\d*[BMK]?)', text.upper())
            if volume_match:
                return volume_match.group(1)
        except AttributeError as e:
            logger.error(f"Error extracting volume from '{text}': {e}")
        
        return text.strip()
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage from text string"""
        if not text:
            return None
        
        try:
            # Find percentage pattern
            percent_match = re.search(r'([+-]?[\d.]+)%?', text)
            if percent_match:
                return float(percent_match.group(1))
        except (ValueError, AttributeError) as e:
            logger.error(f"Error extracting percentage from '{text}': {e}")
        
        return None
    
    def get_comprehensive_data(self, symbols: List[str] = ['BTC']) -> Dict:
        """
        Get comprehensive market data from multiple sources
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        try:
            # Initialize driver once for all operations
            self._initialize_driver()
            
            # Get CoinMarketCap data for Bitcoin
            if 'BTC' in symbols:
                cmc_data = self.scrape_coinmarketcap_bitcoin()
                results['sources']['coinmarketcap'] = cmc_data
                
                # Small delay between requests
                time.sleep(2)
            
            # Get TradingView data
            for symbol in symbols:
                tv_symbol = f"{symbol}USDT" if symbol != 'BTC' else "BTCUSDT"
                tv_data = self.scrape_tradingview_data(tv_symbol)
                
                if 'tradingview' not in results['sources']:
                    results['sources']['tradingview'] = {}
                results['sources']['tradingview'][symbol] = tv_data
                
                # Small delay between requests
                time.sleep(2)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive data collection: {e}")
            results['error'] = str(e)
            return results
        
        finally:
            self._close_driver()
    
    def __enter__(self):
        """Context manager entry"""
        self._initialize_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._close_driver()

# Convenience function for quick testing
def get_bitcoin_price() -> Dict:
    """Quick function to get Bitcoin price from CoinMarketCap"""
    with MarketDataAgent() as agent:
        return agent.scrape_coinmarketcap_bitcoin()

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    print("Testing MarketDataAgent...")
    
    # Test CoinMarketCap scraping
    with MarketDataAgent(headless=False) as agent:
        btc_data = agent.scrape_coinmarketcap_bitcoin()
        print("\nCoinMarketCap Bitcoin Data:")
        print(json.dumps(btc_data, indent=2))
        
        # Test TradingView scraping
        tv_data = agent.scrape_tradingview_data("BTCUSDT")
        print("\nTradingView Data:")
        print(json.dumps(tv_data, indent=2)) 
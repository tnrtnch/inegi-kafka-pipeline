import scrapy
import yaml
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from inegi.items import InegiItem

class InegiSpider(scrapy.Spider):
    name = "inegi_spider"
    allowed_domains = ["www3.inegi.org.mx"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("scraper.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.output_file = self.config.get("output_file", "sanctions.json")


        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)

    # async def start(self):
    #     yield scrapy.Request(
    #         url=self.config["target_url"], 
    #         callback=self.parse_with_selenium,
    #             headers={
    #             "Accept-Language": "en-US,en;q=0.9",
    #             "Accept": "text/html,application/xhtml+xml",
    #         }
    # )

    def start_requests(self):
            yield scrapy.Request(
                url=self.config["target_url"],
                callback=self.parse_with_selenium,
                headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml",
                }
            )


    def parse_with_selenium(self, response):
        self.driver.get(response.url)
        self.driver.maximize_window()

        self.wait.until(EC.element_to_be_clickable((By.ID, "cphContenido_rbtNombre"))).click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "cphContenido_txtNombre")))
        self.wait.until(EC.element_to_be_clickable((By.ID, "cphContenido_txtNombre"))).send_keys(
            self.config["search_query"]
        )
        self.wait.until(EC.element_to_be_clickable((By.ID, "cphContenido_lnkbtnTotal"))).click()
        self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "(//tbody)[5]//a")))

        yield from self.parse_page()

    def parse_page(self):
        profile_xpath = "(//tbody)[5]//a[contains(@id,'lnkSancionar')]"

        while True:

            profiles_count = len(
                self.driver.find_elements(By.XPATH, profile_xpath)
            )

            for i in range(profiles_count):
                try:
                    profiles = self.driver.find_elements(By.XPATH, profile_xpath)

                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);",
                        profiles[i]
                    )

                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, profile_xpath))
                    )

                    profiles[i].click()

                    name_part = self.wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//caption//span[@class='Etiqueta']")
                        )
                    ).text

                    name = re.split(
                        r'\bproveedor \b',
                        name_part
                    )[-1].strip()

                    numbers = []

                    elements = self.driver.find_elements(
                        By.XPATH,
                        "//tr[@style='background-color:#EFEFEF;']/td[2]"
                    )

                    for el in elements:
                        try:
                            text = el.text.strip()

                            if text:
                                numbers.append(text)

                        except Exception as e:
                            self.logger.warning(f"text read failed: {e}")

                    item = InegiItem()
                    item["Entity_name"] = name
                    item["Sanction_numbers"] = numbers

                    yield item

                except Exception as e:
                    self.logger.error(f"profile failed: {e}")

                    self.driver.save_screenshot(
                        f"error_{i}.png"
                    )

                finally:

                    try:
                        self.driver.back()

                        self.wait.until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, profile_xpath)
                            )
                        )

                    except Exception as e:
                        self.logger.error(f"back failed: {e}")
                        return

            break
                    

    def closed(self, reason):
        if hasattr(self, "driver") and self.driver:
            self.driver.quit()
            self.logger.info("WebDriver closed.") 

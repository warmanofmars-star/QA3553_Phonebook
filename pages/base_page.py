from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def find(self, locator):
        return self.driver.find_element(*locator)

    def click(self, locator):
        self.find(locator).click()

    def fill(self, locator, value):
        self.find(locator).clear()
        self.find(locator).send_keys(value)

    # Универсальные методы работы с алертами для всех страниц
    def get_alert_text(self, timeout=5):
        alert = WebDriverWait(self.driver, timeout=timeout).until(
            EC.alert_is_present()
        )
        return alert.text

    def accept_alert(self, timeout=5):
        alert = WebDriverWait(self.driver, timeout=timeout).until(
            EC.alert_is_present()
        )
        alert.accept()

    def is_disappeared(self, locator, timeout=5):
        """Ждет, пока элемент не исчезнет со страницы. Возвращает True, если исчез."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
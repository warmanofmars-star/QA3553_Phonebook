import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from pages.base_page import BasePage


class ContactsPage(BasePage):
    PAGE_URL = "https://telranedu.web.app/contacts"

    # --- ЛОКАТОРЫ ---
    # Из классной работы:
    CONTACT_NAV_LINK = (By.CSS_SELECTOR, "[href='/contacts']")
    CONTACT_CARDS = (By.CLASS_NAME, "contact-item_card__2SOIM")

    # Наши локаторы:
    REMOVE_BTN = (By.XPATH, "//button[text()='Remove']")

    # ==========================================
    # МЕТОДЫ ИЗ КЛАССНОЙ РАБОТЫ
    # ==========================================
    def open_contact_list(self):
        """Открывает список контактов через клик по верхнему меню"""
        self.click(self.CONTACT_NAV_LINK)
        WebDriverWait(self.driver, 5).until(EC.url_contains("/contacts"))
        time.sleep(1)

    def contact_cards_count(self, phone):
        """Считает количество карточек с заданным номером телефона"""
        return len(self.driver.find_elements(By.XPATH, f"//h3[text()='{phone}']"))

    def open_contact_details(self, phone):
        """Кликает по самой карточке (родительскому элементу), чтобы открыть детали"""
        card = self.driver.find_element(By.XPATH, f"//h3[text()='{phone}']/..")
        card.click()

    def contact_card_visible(self, phone):
        """Ждет появления карточки в DOM и проверяет её видимость"""
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(locator))
        return element.is_displayed()

    # ==========================================
    # НАШИ МЕТОДЫ ДЛЯ УДАЛЕНИЯ
    # ==========================================
    def open(self):
        """Открывает страницу напрямую по URL (наш быстрый метод)"""
        self.driver.get(self.PAGE_URL)

    def click_remove_button(self):
        """Кликает на кнопку Remove в правой панели"""
        self.click(self.REMOVE_BTN)

    def is_contact_deleted(self, phone):
        """Проверяет, что карточка с указанным телефоном исчезла со страницы"""
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        return self.is_disappeared(locator)
import time
import platform
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from pages.base_page import BasePage


class ContactsPage(BasePage):
    PAGE_URL = "https://telranedu.web.app/contacts"

    # ==========================================
    # ЛОКАТОРЫ
    # ==========================================
    CONTACT_NAV_LINK = (By.CSS_SELECTOR, "[href='/contacts']")
    CONTACT_CARDS = (By.CLASS_NAME, "contact-item_card__2SOIM")
    CONTACT_DETAILS_CARD = (By.CLASS_NAME, "contact-item-detailed_card__50dTS")

    # Кнопки
    REMOVE_BTN = (By.XPATH, "//button[text()='Remove']")
    EDIT_BTN = (By.XPATH, "//button[text()='Edit']")
    SAVE_BTN = (By.XPATH, "//button[text()='Save']")

    # Словарь локаторов полей для формы редактирования
    # Ключи строго совпадают с названиями атрибутов в классе Contact
    EDIT_FORM_LOCATORS = {
        "name": (By.CSS_SELECTOR, "input[placeholder='Name']"),
        "last_name": (By.CSS_SELECTOR, "input[placeholder='Last Name']"),
        "phone": (By.CSS_SELECTOR, "input[placeholder='Phone']"),
        "email": (By.CSS_SELECTOR, "input[placeholder='email']"),
        "address": (By.CSS_SELECTOR, "input[placeholder='Address']"),
        "description": (By.CSS_SELECTOR, "input[placeholder='desc']")
    }

    # ==========================================
    # БАЗОВЫЕ МЕТОДЫ (Список контактов)
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
        """Кликает по карточке (по номеру телефона), чтобы открыть детали"""
        card = self.driver.find_element(By.XPATH, f"//h3[text()='{phone}']/..")
        card.click()

    def contact_card_visible(self, phone):
        """Ждет появления карточки в DOM и проверяет её видимость"""
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(locator))
        return element.is_displayed()

    # ==========================================
    # МЕТОДЫ УДАЛЕНИЯ
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

    # ==========================================
    # МЕТОДЫ РЕДАКТИРОВАНИЯ
    # ==========================================
    def get_contact_details_text(self):
        """Возвращает весь текст из правой панели деталей контакта"""
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.CONTACT_DETAILS_CARD))
        return self.find(self.CONTACT_DETAILS_CARD).text

    def click_edit_button(self):
        """Кликает по кнопке Edit в правой панели"""
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(self.EDIT_BTN))
        self.click(self.EDIT_BTN)

    def clear_and_fill_input(self, locator, text):
        """Надежно очищает поле в React-приложении и вводит новый текст"""
        element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(locator))
        cmd_ctrl = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
        element.send_keys(cmd_ctrl + "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(text)

    def edit_contact_form(self, updated_contact):
        """Оптимизированный метод заполнения формы.
        Динамически читает данные из объекта Contact и заполняет форму"""
        for attr_name, locator in self.EDIT_FORM_LOCATORS.items():
            value = getattr(updated_contact, attr_name, None)
            if value is not None:
                self.clear_and_fill_input(locator, value)

    def click_save_edit_button(self):
        """Кликает по кнопке Save в режиме редактирования"""
        self.click(self.SAVE_BTN)

    def is_edit_form_open(self):
        """Проверяет, осталась ли открытой форма редактирования (по наличию инпута 'Name')"""
        elements = self.driver.find_elements(*self.EDIT_FORM_LOCATORS["name"])
        return len(elements) > 0
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from pages.base_page import BasePage

from selenium.webdriver.common.keys import Keys
import platform


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

    #Метод, который "читает" тест из правой панели (для тестирования самой странницы контактов)
    def get_contact_details_text(self):
        """Возвращает весь текст из правой панели деталей контакта"""
        # Локатор правой карточки, в которой появляются данные
        locator = (By.CLASS_NAME, "contact-item-detailed_card__50dTS")

        # Ждем, пока карточка прогрузится, и забираем ее текст
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(locator))
        return self.find(locator).text

    #
    #здесь уже идет работа с редактированием карточки контакта
    #

    def click_edit_button(self):
        """Нажимает кнопку Edit в деталях контакта"""
        locator = (By.XPATH, "//button[text()='Edit']")
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(locator))
        self.click(locator)

    def clear_and_fill_input(self, locator, text):
        """Выделяет весь текст в поле и заменяет его на новый (надежно для React)"""
        element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(locator))
        cmd_ctrl = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
        element.send_keys(cmd_ctrl + "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(text)

    def edit_contact_form(self, updated_contact):
        """Заполняет форму редактирования переданными данными"""
        locators = {
            "name": (By.CSS_SELECTOR, "input[placeholder='Name']"),
            "last_name": (By.CSS_SELECTOR, "input[placeholder='Last Name']"),
            "phone": (By.CSS_SELECTOR, "input[placeholder='Phone']"),
            "email": (By.CSS_SELECTOR, "input[placeholder='email']"),
            "address": (By.CSS_SELECTOR, "input[placeholder='Address']"),
            "description": (By.CSS_SELECTOR, "input[placeholder='desc']")
        }

        # Заполняем только те поля, которые переданы (не None)
        if updated_contact.name is not None:
            self.clear_and_fill_input(locators["name"], updated_contact.name)
        if updated_contact.last_name is not None:
            self.clear_and_fill_input(locators["last_name"], updated_contact.last_name)
        if updated_contact.phone is not None:
            self.clear_and_fill_input(locators["phone"], updated_contact.phone)
        if updated_contact.email is not None:
            self.clear_and_fill_input(locators["email"], updated_contact.email)
        if updated_contact.address is not None:
            self.clear_and_fill_input(locators["address"], updated_contact.address)
        if updated_contact.description is not None:
            self.clear_and_fill_input(locators["description"], updated_contact.description)

    def click_save_edit_button(self):
        """Нажимает кнопку Save при редактировании"""
        locator = (By.XPATH, "//button[text()='Save']")
        self.click(locator)

    def is_edit_form_open(self):
        """Проверяет, осталась ли открытой форма редактирования (по наличию инпутов)"""
        locator = (By.CSS_SELECTOR, "input[placeholder='Name']")
        # Используем встроенный метод драйвера find_elements.
        # Если инпут есть на странице, вернется список элементов (длина > 0).
        elements = self.driver.find_elements(*locator)
        return len(elements) > 0
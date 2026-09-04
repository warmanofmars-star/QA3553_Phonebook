import platform
from models.contact import Contact
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from pages.base_page import BasePage
from pages.locators import ContactFormLocators


class ContactsPage(BasePage):
    ENDPOINT = "/contacts"

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

    # ==========================================
    # БАЗОВЫЕ МЕТОДЫ (Список контактов)
    # ==========================================
    def open_contact_list(self):
        """Открывает список контактов через клик по верхнему меню"""
        self.click(self.CONTACT_NAV_LINK)
        WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(EC.url_contains("/contacts"))


    def contact_cards_count(self, phone):
        """Считает количество карточек с заданным номером телефона"""
        return len(self.driver.find_elements(By.XPATH, f"//h3[text()='{phone}']"))

    def open_contact_details(self, phone):
        """Кликает по карточке (по номеру телефона), чтобы открыть детали"""
        locator = (By.XPATH, f"//h3[text()='{phone}']/..")

        # Явно ждем, пока карточка не только появится в DOM, но и станет кликабельной
        card = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(locator)
        )
        card.click()

    def contact_card_visible(self, phone):
        """Ждет появления карточки в DOM и проверяет её видимость"""
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(locator))
        return element.is_displayed()

    # ==========================================
    # МЕТОДЫ УДАЛЕНИЯ
    # ==========================================

    def click_remove_button(self):
        """Кликает на кнопку Remove в правой панели"""
        self.click(self.REMOVE_BTN)

    def is_contact_deleted(self, phone):
        """Проверяет, что карточка с указанным телефоном исчезла со страницы"""
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        return self.is_disappeared(locator)

    def get_all_contacts_count(self):
        """Возвращает общее количество контактов в левом списке"""
        # find_elements возвращает список. Если элементов нет - вернет пустой список []
        return len(self.driver.find_elements(*self.CONTACT_CARDS))

    def delete_all_contacts(self):
        """Удаляет все контакты по одному, избегая ошибки устаревших элементов (StaleElementReference)"""
        while True:
            # Каждый раз заново ищем все карточки на странице
            cards = self.driver.find_elements(*self.CONTACT_CARDS)

            # Если карточек больше нет — прерываем цикл (работа сделана)
            if not cards:
                break

            current_count = len(cards)

            # Кликаем всегда по первой карточке в списке
            cards[0].click()

            # Ждем появления кнопки Remove и кликаем её
            WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable(self.REMOVE_BTN)
            ).click()

            # САМОЕ ВАЖНОЕ: Ждем, пока общее количество карточек не уменьшится на 1
            # Только после этого идем на следующий круг цикла
            WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                lambda driver: len(driver.find_elements(*self.CONTACT_CARDS)) < current_count
            )

    def delete_specific_contacts(self, phone_numbers: list):
        """Удаляет только те контакты, телефоны которых переданы в списке"""
        for phone in phone_numbers:
            self.open_contact_details(phone)
            self.click_remove_button()
            self.is_contact_deleted(phone)

    # ==========================================
    # МЕТОДЫ РЕДАКТИРОВАНИЯ
    # ==========================================
    def get_contact_details_text(self):
        """Возвращает весь текст из правой панели деталей контакта"""
        WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(EC.presence_of_element_located(self.CONTACT_DETAILS_CARD))
        return self.find(self.CONTACT_DETAILS_CARD).text

    def click_edit_button(self):
        """Кликает по кнопке Edit в правой панели"""
        WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(EC.element_to_be_clickable(self.EDIT_BTN))
        self.click(self.EDIT_BTN)

    def clear_and_fill_input(self, locator, text):
        """Надежно очищает поле в React-приложении и вводит новый текст"""
        element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(EC.element_to_be_clickable(locator))
        cmd_ctrl = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
        element.send_keys(cmd_ctrl + "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(text)

    def edit_contact_form(self, updated_contact):
        """Оптимизированный метод заполнения формы.
        Динамически читает данные из объекта Contact и заполняет форму"""
        for attr_name, locator in ContactFormLocators.FIELDS.items():
            value = getattr(updated_contact, attr_name, None)
            if value is not None:
                self.clear_and_fill_input(locator, value)

    def click_save_edit_button(self):
        """Кликает по кнопке Save в режиме редактирования"""
        self.click(self.SAVE_BTN)

    def is_edit_form_open(self):
        """Проверяет, осталась ли открытой форма редактирования (по наличию инпута 'Name')"""
        elements = self.driver.find_elements(*ContactFormLocators.FIELDS["name"])
        return len(elements) > 0

    def get_contact_data_from_form(self) -> Contact:
        """
        МЕГА-ПРОФЕССИОНАЛЬНЫЙ ПОДХОД:
        Читаем значения из конкретных полей формы, чтобы убедиться,
        что данные не 'съехали' в чужие инпуты.
        """
        # Ждем, пока форма точно появится
        WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(ContactFormLocators.FIELDS["name"])
        )

        # Вытаскиваем текст из атрибута 'value' каждого конкретного инпута
        name = self.find(ContactFormLocators.FIELDS["name"]).get_attribute("value")
        last_name = self.find(ContactFormLocators.FIELDS["last_name"]).get_attribute("value")
        phone = self.find(ContactFormLocators.FIELDS["phone"]).get_attribute("value")
        email = self.find(ContactFormLocators.FIELDS["email"]).get_attribute("value")
        address = self.find(ContactFormLocators.FIELDS["address"]).get_attribute("value")
        description = self.find(ContactFormLocators.FIELDS["description"]).get_attribute("value")

        # Возвращаем эти данные в виде красивого объекта Contact
        return Contact(name=name, last_name=last_name, phone=phone, email=email, address=address,
                       description=description)
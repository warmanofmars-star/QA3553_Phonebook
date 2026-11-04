from dataclasses import replace

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from models.contact import Contact
from pages.base_page import BasePage
from pages.locators import ContactFormLocators
from utils.allure_steps import step


class ContactsPage(BasePage):
    ENDPOINT = "/contacts"
    PAGE_NAME = "Список контактов"

    # Приложение использует CSS Modules: классы вида contact-item_card__2SOIM, где
    # суффикс — хэш, который меняется при пересборке фронтенда. Поэтому ищем по
    # стабильному началу класса (^= — "начинается с"), а не по полному имени.
    # В реальной команде правильнее попросить разработчиков добавить data-testid.
    _CARD = (By.CSS_SELECTOR, "[class^='contact-item_card__']")
    _DETAILS = (By.CSS_SELECTOR, "[class^='contact-item-detailed_card__']")

    _EDIT_BTN = (By.XPATH, "//button[text()='Edit']")
    _REMOVE_BTN = (By.XPATH, "//button[text()='Remove']")
    _SAVE_EDIT_BTN = (By.XPATH, "//button[text()='Save']")

    @staticmethod
    def _card_by_phone(phone: str):
        """Карточка в списке слева, найденная по телефону (h3 внутри карточки)."""
        return By.XPATH, f"//div[starts-with(@class, 'contact-item_card__')][h3[text()='{phone}']]"

    # ==========================================
    # Список
    # ==========================================
    def is_card_displayed(self, phone: str, timeout: float | None = None) -> bool:
        """Ждёт появления карточки с телефоном. False — так и не появилась."""
        return self._is_visible(self._card_by_phone(phone), timeout)

    def is_card_gone(self, phone: str, timeout: float | None = None) -> bool:
        """Ждёт исчезновения карточки с телефоном. False — так и осталась в списке."""
        return self._is_gone(self._card_by_phone(phone), timeout)

    def cards_count(self) -> int:
        """Сколько карточек в списке прямо сейчас."""
        return self._count(self._CARD)

    @step("Открыть карточку контакта {phone}")
    def open_details(self, phone: str) -> None:
        self._click(self._card_by_phone(phone))

    def details_text(self) -> str:
        """Весь текст правой панели с деталями контакта."""
        return self._find_visible(self._DETAILS).text

    # ==========================================
    # Удаление
    # ==========================================
    @step("Удалить контакт {phone}")
    def delete_contact(self, phone: str) -> None:
        """Открывает карточку и нажимает Remove. Исчезновение карточки проверяет тест."""
        self.open_details(phone)
        self._click(self._REMOVE_BTN)

    @step("Удалить все контакты по одному")
    def delete_all_contacts(self) -> None:
        """Удаляет контакты, всегда кликая по первой карточке.

        После каждого удаления React перерисовывает список, поэтому карточки ищем
        заново на каждой итерации (иначе StaleElementReferenceException).
        Лимит итераций защищает от бесконечного цикла, если удаление сломано.
        """
        max_iterations = self.cards_count() + 5
        for _ in range(max_iterations):
            count_before = self.cards_count()
            if count_before == 0:
                return
            self.driver.find_elements(*self._CARD)[0].click()
            self._click(self._REMOVE_BTN)
            # before=count_before фиксирует значение на ЭТОЙ итерации. Лямбда без этого
            # видела бы переменную цикла, а не её значение (ловушка "позднего связывания")
            self._wait().until(lambda _driver, before=count_before: self.cards_count() < before)
        raise AssertionError(f"Не удалось удалить все контакты за {max_iterations} попыток")

    # ==========================================
    # Редактирование
    # ==========================================
    # Точки синхронизации — по состоянию интерфейса, а не по времени:
    #   1. после Edit форма открыта И заполнена данными контакта — только тогда вводим
    #      (иначе React может заполнить поля уже после ввода и затереть его);
    #   2. после ввода каждого поля его value равен введённому;
    #   3. после Save форма закрылась, а в карточке — новые значения.
    # Повторных попыток ввода нет намеренно: если состояние не наступило, это ошибка,
    # и она должна быть видна, а не замаскирована вторым вводом.
    def edit_contact(self, contact: Contact, changes: Contact, *, expect_saved: bool = True) -> None:
        """Полный сценарий редактирования: открыть карточку, Edit, изменить поля, Save.

        contact — контакт в том виде, в каком он сейчас сохранён: по нему проверяется,
        что форма заполнилась, а после Save — что карточка показывает новые значения.
        changes — новые значения (None — поле не трогаем, "" — очистить).
        expect_saved=False — для негативных сценариев (невалидные данные, дубликаты):
        после Save интерфейс не проверяется, что сохранилось — проверяет тест через API.
        """
        self.open_details(contact.phone)
        self.start_editing(contact)
        self.fill_edit_form(changes, contact)
        self.save_edit()
        if expect_saved:
            new_values = {f: getattr(changes, f) for f in ContactFormLocators.FIELDS if getattr(changes, f) is not None}
            self._wait_saved(contact, replace(contact, **new_values))

    @step("Нажать Edit и дождаться формы с данными контакта")
    def start_editing(self, contact: Contact) -> None:
        self._click(self._EDIT_BTN)
        if not self._is_visible(ContactFormLocators.FIELDS["name"]):
            self._fail("Форма редактирования не открылась: поле Name не появилось после Edit")

        expected = {f: getattr(contact, f) for f in ContactFormLocators.FIELDS if getattr(contact, f) is not None}
        if not self._wait_for(lambda: self._form_values(expected) == expected):
            mismatch = self._describe_mismatch(expected, self._form_values(expected))
            self._fail(f"Форма редактирования не заполнилась данными контакта: {mismatch}")

    @step("Изменить поля формы редактирования")
    def fill_edit_form(self, changes: Contact, current: Contact) -> None:
        """Меняет поля, у которых в changes задано значение (None — поле не трогаем).
        Пустая строка "" очищает поле. current — значения в форме до ввода."""
        for field in ContactFormLocators.FIELDS:
            value = getattr(changes, field)
            if value is not None:
                self.change_field(field, value, previous=getattr(current, field))

    # Значения полей контакта — не секрет, поэтому их можно показывать в шаге:
    # без этого по отчёту нельзя понять, что именно тест вводил
    @step("Изменить поле {field} на '{value}'")
    def change_field(self, field: str, value: str, previous: str | None = None) -> None:
        locator = ContactFormLocators.FIELDS[field]
        self._replace_text(locator, value)
        if self._wait_for(lambda: self._find(locator).get_attribute("value") == value):
            return

        actual = self._find(locator).get_attribute("value")
        state = f"поле {field}: ожидалось {value!r}, фактически {actual!r}"
        if actual == (previous or ""):
            # В поле вернулось прежнее значение: форма перезаписала ввод (гонка с заполнением
            # формы) или ввод не дошёл до поля. Это сбой синхронизации — UiStateError
            self._fail(f"Форма перезаписала ввод прежним значением: {state}")
        # В поле не введённое и не прежнее значение — приложение само исказило ввод.
        # Это результат действия, а не сбой синхронизации, поэтому AssertionError.
        # Так выглядит известный баг описания: вместо текста — '[object Undefined]'
        self._fail(f"Приложение изменило введённое значение: {state}", AssertionError)

    @step("Нажать Save в форме редактирования")
    def save_edit(self) -> None:
        self._click(self._SAVE_EDIT_BTN)

    def _wait_saved(self, before: Contact, expected: Contact) -> None:
        """После Save: форма закрылась, а в карточке — новые значения изменённых полей."""
        with allure.step("Дождаться закрытия формы и новых значений в карточке"):
            if not self._is_gone(ContactFormLocators.FIELDS["name"]):
                self._fail("После Save форма редактирования не закрылась")

            fields = [f for f in ContactFormLocators.FIELDS if getattr(expected, f) != getattr(before, f)]
            wanted = self._details_view(expected, fields)
            if not self._wait_for(lambda: self._details_shown(fields) == wanted):
                actual = self._details_shown(fields)
                stale = [key for key in wanted if actual.get(key) == self._details_view(before, fields).get(key)]
                prefix = "в карточке осталось старое значение" if stale else "в карточке другое значение"
                # AssertionError, а не UiStateError: ввод уже подтверждён (value полей
                # проверены), значит карточка показывает не то, что сохранил пользователь —
                # это результат действия, а не сбой синхронизации. Так проявляется и
                # известный баг описания (EDIT_DESCRIPTION_BROKEN: '[object Undefined]')
                self._fail(f"После Save {prefix}: {self._describe_mismatch(wanted, actual)}", AssertionError)

    # ---------- чтение формы и карточки ----------
    def _form_values(self, fields) -> dict[str, str]:
        """Текущие value полей формы редактирования."""
        return {f: self._find(ContactFormLocators.FIELDS[f]).get_attribute("value") for f in fields}

    @staticmethod
    def _details_view(contact: Contact, fields: list[str]) -> dict[str, str]:
        """Как поля контакта выглядят в панели деталей: имя и фамилия — один заголовок."""
        view = {}
        for field in fields:
            if field in ("name", "last_name"):
                view["full_name"] = f"{contact.name} {contact.last_name}".strip()
            else:
                view[field] = getattr(contact, field)
        return view

    def _details_shown(self, fields: list[str]) -> dict[str, str]:
        """Что панель деталей показывает сейчас (только для нужных полей).

        Разметка панели: <h2>Имя Фамилия</h2>, затем строки телефона, email и адреса,
        затем <h3>Description: ...</h3> и кнопки Edit / Remove.
        """
        panel = self._find_visible(self._DETAILS)
        full_name = panel.find_element(By.TAG_NAME, "h2").text.strip()
        lines = [line.strip() for line in panel.text.splitlines() if line.strip()]
        description = next(
            (line.removeprefix("Description:").strip() for line in lines if line.startswith("Description:")), ""
        )
        plain = [line for line in lines if line != full_name and not line.startswith("Description:")]
        plain = [line for line in plain if line not in ("Edit", "Remove")]
        values = dict(zip(("phone", "email", "address"), plain, strict=False))
        values.update(full_name=full_name, description=description)
        return {key: values.get(key) for key in self._details_view(Contact(), fields)}

    @staticmethod
    def _describe_mismatch(expected: dict, actual: dict) -> str:
        parts = [
            f"поле {key}: ожидалось {value!r}, фактически {actual.get(key)!r}"
            for key, value in expected.items()
            if actual.get(key) != value
        ]
        return "; ".join(parts) or "расхождений нет (состояние успело измениться)"

    def _replace_text(self, locator, text: str) -> None:
        """Надёжная замена текста в поле React-формы.

        element.clear() в React-формах ненадёжен: поле визуально очищается, но
        состояние компонента не обновляется. Выделение всего текста + Backspace
        имитирует действия пользователя и корректно запускает обработчики React.
        """
        element = self._wait().until(EC.element_to_be_clickable(locator))
        # Сочетание "выделить всё" зависит от ОС, на которой запущен БРАУЗЕР, а не тесты:
        # с Mac через Selenium Grid браузер работает в Linux-контейнере и ждёт Ctrl, а не Cmd
        browser_os = str(self.driver.capabilities.get("platformName", "")).lower()
        select_all = Keys.COMMAND if "mac" in browser_os else Keys.CONTROL
        element.send_keys(select_all + "a")
        element.send_keys(Keys.BACKSPACE)
        if text:
            element.send_keys(text)

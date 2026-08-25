from pages.add_contact_page import ContactPage
from data.data_generator import ContactGenerator


def test_add_contact_success_all_fields(authenticated_driver):
    # 1. Инициализируем страницу
    contact_page = ContactPage(authenticated_driver)

    # 2. Открываем форму добавления контакта
    contact_page.open()

    # 3. Генерируем уникальные тестовые данные через Faker
    contact = ContactGenerator.get_random_contact()

    # 4. Заполняем форму и сохраняем
    contact_page.fill_contact_form(contact)
    contact_page.submit_contact()

    # 5. ПРОВЕРКА: убеждаемся, что карточка появилась.
    # Если метод is_contact_card_visible вернет False, тест упадет и выведет сообщение после запятой.
    assert contact_page.is_contact_card_visible(contact.phone), \
        f"Ошибка: Карточка контакта с телефоном {contact.phone} не появилась в списке!"
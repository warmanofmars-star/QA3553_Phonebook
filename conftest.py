import pytest
from selenium import webdriver


@pytest.fixture
def driver():
    driver = webdriver.Edge()
    driver.get("https://telranedu.web.app/login")

    yield driver  # Передаем драйвер в тест
    driver.quit()
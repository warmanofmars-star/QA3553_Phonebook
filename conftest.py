import pytest
from selenium import webdriver


@pytest.fixture
def driver():
    driver = webdriver.Edge()
    driver.implicitly_wait(5)
    driver.maximize_window()
    driver.get("https://telranedu.web.app/login")

    yield driver  # Передаем драйвер в тест
    driver.quit()
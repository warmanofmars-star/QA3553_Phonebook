# Образ, в котором запускаются тесты (сервис qa-framework в docker-compose.yml).
#
# Версия Python совпадает с локальной (3.14), чтобы не было ситуации
# "у меня локально работает, а в Docker падает".
# bookworm (Debian 12) выбран явно: под него Playwright гарантированно ставит
# системные зависимости браузера (--with-deps). Минорная версия зафиксирована,
# патчи безопасности (3.14.x) подтягиваются при пересборке.
FROM python:3.14-slim-bookworm

# PYTHONDONTWRITEBYTECODE — не создавать .pyc в контейнере (они там бесполезны)
# PYTHONUNBUFFERED — вывод сразу попадает в логи docker, без задержки буфера
# PIP_DISABLE_PIP_VERSION_CHECK — не спрашивать про новую версию pip при каждой сборке
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Сначала ТОЛЬКО зависимости: этот слой Docker кэширует и пересобирает,
# лишь когда меняется requirements.txt. Правка кода тестов его не трогает.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Браузер для Playwright-тестов вместе с системными библиотеками (Selenium-тесты
# идут в Selenium Grid, им локальный браузер не нужен)
RUN playwright install --with-deps chromium

# Код проекта — последним слоем (что не копируется, см. .dockerignore)
COPY . .

# Папка для видео с теми же владельцем и правами, что /videos в образах узлов Grid
# (пользователь seluser = 1200, группа 0, 775). Общий том video-data Docker заполняет
# по папке того контейнера, который смонтирует его первым. Раньше /app/video не было,
# Docker создавал её от root, и если qa-framework стартовал раньше узлов, узлам не
# хватало прав на запись (ffmpeg: Permission denied). Теперь владелец одинаковый
# в обоих образах, и порядок старта не важен.
RUN mkdir -p /app/video && chown 1200:0 /app/video && chmod 775 /app/video

# Команда по умолчанию — весь набор тестов. В docker-compose.yml она переопределяется
# (там добавлены браузер и видео), но и простой `docker run` теперь гоняет всё,
# а не только папку tests/, как раньше
CMD ["pytest", "-n", "2", "--clean-alluredir", "--alluredir=allure-results"]

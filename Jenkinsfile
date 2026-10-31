pipeline {
    agent any

    // ==========================================
    // 1. ОБЩИЕ НАСТРОЙКИ СБОРКИ
    // ==========================================
    options {
        timeout(time: 30, unit: 'MINUTES')               // зависший Selenoid не повесит сборку навсегда
        buildDiscarder(logRotator(numToKeepStr: '20'))   // старые сборки и их отчёты не копятся на диске
        disableConcurrentBuilds()                        // две сборки в одном workspace мешали бы друг другу
    }

    // ==========================================
    // 2. ПАРАМЕТРЫ ЗАПУСКА ("Собрать с параметрами")
    // ==========================================
    parameters {
        // Edge убран: в selenoid/browsers.json его нет, сборка всё равно упала бы
        choice(name: 'BROWSER', choices: ['chrome', 'firefox'], description: 'Браузер для UI-тестов')
        string(name: 'TEST_MARKER', defaultValue: '', description: 'Маркеры pytest: smoke, api, "api and security"... Пусто — все тесты')
    }

    // ==========================================
    // 3. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
    // ==========================================
    environment {
        // Секреты из хранилища Jenkins (Manage Jenkins -> Credentials)
        TG_BOT_TOKEN = credentials('TG_BOT_TOKEN')
        TG_CHAT_ID   = credentials('TG_CHAT_ID')
        // Явное имя проекта Docker Compose: контейнеры, сети и тома этой сборки
        // не пересекаются с локальными запусками docker compose на той же машине
        COMPOSE_PROJECT_NAME = 'phonebook-jenkins'
    }

    // ==========================================
    // 4. ЭТАПЫ
    // ==========================================
    stages {
        stage('Run tests in Docker') {
            steps {
                script {
                    // Workspace Jenkins сохраняется между сборками: убираем результаты прошлой
                    // сборки и старый .env (раньше в него писались логин и пароль — тестам он больше не нужен)
                    sh 'rm -rf allure-results .env && mkdir -p allure-results'

                    // Параметры передаются в контейнер через переменные окружения
                    // (см. блок environment сервиса qa-framework в docker-compose.yml).
                    // PYTEST_ADDOPTS pytest дочитывает сам — маркер не вклеивается в текст команды
                    def marker = params.TEST_MARKER?.trim()
                    def pytestAddopts = marker ? "-m \"${marker}\"" : ''

                    def exitCode = 0
                    withEnv(["BROWSER=${params.BROWSER}", "PYTEST_ADDOPTS=${pytestAddopts}"]) {
                        // returnStatus: не прерываем pipeline сразу — сначала заберём результаты
                        exitCode = sh(script: 'docker compose up --build --exit-code-from qa-framework', returnStatus: true)
                    }

                    // Результаты забираем ВСЕГДА — отчёт нужнее всего именно при упавших тестах.
                    // Раньше копирование стояло после команды, которая падала, и не выполнялось
                    sh 'docker cp "$(docker compose ps -a -q qa-framework)":/app/allure-results/. ./allure-results/ || true'

                    // Коды выхода pytest: 0 — всё прошло; 1 — есть упавшие тесты; остальные — сбой запуска.
                    // По соглашению Jenkins: упавшие тесты = UNSTABLE (жёлтая), сломанная сборка = FAILURE (красная)
                    if (exitCode == 1) {
                        unstable('Есть упавшие тесты — смотри Allure Report')
                    } else if (exitCode != 0) {
                        error("Тесты не удалось запустить (код выхода pytest/docker: ${exitCode})")
                    }
                }
            }
        }
    }

    // ==========================================
    // 5. ПОСЛЕ ЛЮБОГО ИСХОДА
    // ==========================================
    post {
        always {
            // environment.properties пишет сам фреймворк (conftest.py) — дополняем его
            // данными о сборке, а не перезаписываем, как раньше
            sh '''
                mkdir -p allure-results
                echo "CI=Jenkins" >> allure-results/environment.properties
                echo "Build=${BUILD_NUMBER}" >> allure-results/environment.properties
            '''

            // Плагин Allure сам хранит историю сборок — график трендов строится автоматически
            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])

            script {
                def status = currentBuild.currentResult   // SUCCESS / UNSTABLE / FAILURE / ABORTED
                def icon = [SUCCESS: '✅', UNSTABLE: '🟡', FAILURE: '🔴'].get(status, '⚪')
                def text = """${icon} Phonebook — Jenkins
Сборка: ${env.JOB_NAME} #${env.BUILD_NUMBER}
Браузер: ${params.BROWSER}
Маркеры: ${params.TEST_MARKER ?: 'все тесты'}
Статус: ${status}
Отчёт: ${env.BUILD_URL}allure/"""

                // Текст передаём через переменную окружения, а curl кодирует его сам
                // (--data-urlencode): переводы строк, эмодзи и спецсимволы не ломают запрос.
                // Ошибка отправки не должна ронять сборку — отсюда "|| true"
                withEnv(["TG_TEXT=${text}"]) {
                    sh '''
                        curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
                            --data-urlencode "chat_id=${TG_CHAT_ID}" \
                            --data-urlencode "text=${TG_TEXT}" > /dev/null || true
                    '''
                }
            }

            // Уборка. Благодаря COMPOSE_PROJECT_NAME --remove-orphans трогает
            // только контейнеры этой сборки, но не сам Jenkins
            sh 'docker compose down -v --remove-orphans || true'
            sh 'docker image prune -f || true'
        }
    }
}

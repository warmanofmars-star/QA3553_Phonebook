pipeline {
    agent any

    // 1. ПАРАМЕТРЫ ЗАПУСКА
    parameters {
        choice(name: 'BROWSER', choices: ['chrome', 'firefox', 'edge'], description: 'Выберите браузер для тестов')
    }

    // 2. БЕЗОПАСНЫЕ ПЕРЕМЕННЫЕ (Секреты из сейфа Jenkins)
    environment {
        TG_BOT_TOKEN    = credentials('TG_BOT_TOKEN')
        TG_CHAT_ID      = credentials('TG_CHAT_ID')
        TELRAN_PASSWORD = credentials('TELRAN_PASSWORD') // Твой Wwar123456$ в безопасности
    }

    // 3. ОСНОВНЫЕ ШАГИ
    stages {
        stage('Run Docker Tests') {
            steps {
                script {
                    // ВОЗВРАЩАЕМ УТЕРЯННЫЙ БЛОК: Генерация .env на лету со всеми твоими переменными!
                    sh """
                    echo 'USE_SELENOID=true' > .env
                    echo 'HEADLESS_MODE=true' >> .env
                    echo 'ALLOW_MASS_DELETE=false' >> .env
                    echo 'PW_TIMEOUT=10000' >> .env
                    echo 'BASE_URL=https://telranedu.web.app' >> .env
                    echo 'API_URL=https://contactapp-telran-backend.herokuapp.com' >> .env
                    echo 'USER_EMAIL=warman.of.mars.2@gmail.com' >> .env
                    echo 'USER_PASSWORD=${env.TELRAN_PASSWORD}' >> .env
                    """

                    // Запускаем тесты в Докере (без глушилки, чтобы падения были видны)
                    sh """
                    export BROWSER=${params.BROWSER}
                    docker compose up --build --exit-code-from qa-framework
                    """

                    // Страховка: принудительно копируем отчеты из контейнера перед его смертью
                    sh "docker cp \$(docker compose ps -q qa-framework):/app/allure-results/. ./allure-results/ || true"
                }
            }
        }
    }

    // 4. ДЕЙСТВИЯ ПОСЛЕ ТЕСТОВ
    post {
        always {
            // Подготовка папки для Allure и инжект переменной браузера
            sh """
            mkdir -p allure-results
            echo "Browser=${params.BROWSER}" > allure-results/environment.properties
            """

            // Генерация Allure отчета
            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])

            // Отправка безопасного уведомления в Telegram
            script {
                def buildStatus = currentBuild.currentResult ?: 'SUCCESS'
                def statusIcon = buildStatus == 'SUCCESS' ? '✅' : '🔴'

                def msg = "${statusIcon} *Отчет о сборке Jenkins*%0A📦 Проект: ${env.JOB_NAME}%0A🔢 Билд: #${env.BUILD_NUMBER}%0A🌐 Браузер: ${params.BROWSER}%0A🚦 Статус: ${buildStatus}"

                sh """
                curl -s -X POST "https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage" -d "chat_id=${env.TG_CHAT_ID}" -d "parse_mode=Markdown" -d "text=${msg}"
                """
            }

            // Зачистка мусора
            sh 'docker compose down -v --remove-orphans'
            sh 'docker image prune -f'
        }
    }
}
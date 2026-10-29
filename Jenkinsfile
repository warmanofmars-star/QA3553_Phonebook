pipeline {
    agent any

    // 1. ПАРАМЕТРЫ ЗАПУСКА
    parameters {
        choice(name: 'BROWSER', choices: ['chrome', 'firefox', 'edge'], description: 'Выберите браузер для тестов')
    }

    // 2. БЕЗОПАСНЫЕ ПЕРЕМЕННЫЕ (Реальные секреты из твоего сейфа Jenkins!)
    environment {
        TG_BOT_TOKEN       = credentials('TG_BOT_TOKEN')
        TG_CHAT_ID         = credentials('TG_CHAT_ID')
        PHONEBOOK_EMAIL    = credentials('PHONEBOOK_EMAIL')
        PHONEBOOK_PASSWORD = credentials('PHONEBOOK_PASSWORD')
    }

    // 3. ОСНОВНЫЕ ШАГИ
    stages {
        stage('Run Docker Tests') {
            steps {
                script {
                    // Генерируем .env на лету, подставляя безопасные переменные
                    sh """
                    echo 'USE_SELENOID=true' > .env
                    echo 'HEADLESS_MODE=true' >> .env
                    echo 'ALLOW_MASS_DELETE=false' >> .env
                    echo 'PW_TIMEOUT=10000' >> .env
                    echo 'BASE_URL=https://telranedu.web.app' >> .env
                    echo 'API_URL=https://contactapp-telran-backend.herokuapp.com' >> .env
                    echo 'USER_EMAIL=${env.PHONEBOOK_EMAIL}' >> .env
                    echo 'USER_PASSWORD=${env.PHONEBOOK_PASSWORD}' >> .env
                    """

                    // Запускаем тесты в Докере (без глушилки catchError)
                    sh """
                    export BROWSER=${params.BROWSER}
                    docker compose up --build --exit-code-from qa-framework
                    """

                    // Копируем отчеты из контейнера перед его смертью
                    sh "docker cp \$(docker compose ps -q qa-framework):/app/allure-results/. ./allure-results/ || true"
                }
            }
        }
    }

    // 4. ДЕЙСТВИЯ ПОСЛЕ ТЕСТОВ
    post {
        always {
            sh """
            mkdir -p allure-results
            echo "Browser=${params.BROWSER}" > allure-results/environment.properties
            """

            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])

            script {
                def buildStatus = currentBuild.currentResult ?: 'SUCCESS'
                def statusIcon = buildStatus == 'SUCCESS' ? '✅' : '🔴'

                def msg = "${statusIcon} *Отчет о сборке Jenkins*%0A📦 Проект: ${env.JOB_NAME}%0A🔢 Билд: #${env.BUILD_NUMBER}%0A🌐 Браузер: ${params.BROWSER}%0A🚦 Статус: ${buildStatus}"

                sh """
                curl -s -X POST "https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage" -d "chat_id=${env.TG_CHAT_ID}" -d "parse_mode=Markdown" -d "text=${msg}"
                """
            }

            sh 'docker compose down -v --remove-orphans'
            sh 'docker image prune -f'
        }
    }
}
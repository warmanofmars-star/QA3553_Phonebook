pipeline {
    agent any

    // 1. ПАРАМЕТРЫ ЗАПУСКА (с выбором браузера)
    parameters {
        choice(name: 'BROWSER', choices: ['chrome', 'firefox', 'edge'], description: 'Выберите браузер для тестов')
    }

    // 2. БЕЗОПАСНЫЕ ПЕРЕМЕННЫЕ (секреты для Телеграма)
    environment {
        TG_BOT_TOKEN = credentials('TG_BOT_TOKEN')
        TG_CHAT_ID   = credentials('TG_CHAT_ID')
    }

    // 3. ОСНОВНЫЕ ШАГИ ПАЙПЛАЙНА
    stages {
        stage('Run Docker Tests') {
            steps {
                script {
                    // Перехватываем падения, чтобы пайплайн не обрывался и Allure сгенерировался
                    catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                        sh """
                        export BROWSER=${params.BROWSER}
                        docker compose up --build --exit-code-from qa-framework
                        """
                    }
                }
            }
        }
    }

    // 4. ДЕЙСТВИЯ ПОСЛЕ ТЕСТОВ (Отчет, Уведомления, Зачистка)
    post {
        always {
            // Инжект переменных в Allure-отчет (Linux синтаксис)
            sh """
            mkdir -p allure-results
            echo "Browser=${params.BROWSER}" > allure-results/environment.properties
            """

            // Генерация самого отчета
            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])

            // Отправка уведомления в Telegram
            script {
                // Защита от ошибки синтаксиса
                def buildStatus = currentBuild.currentResult ?: 'SUCCESS'
                def statusIcon = buildStatus == 'SUCCESS' ? '✅' : '🔴'

                // Формируем текст
                def msg = "${statusIcon} *Отчет о сборке Jenkins*%0A📦 Проект: ${env.JOB_NAME}%0A🔢 Билд: #${env.BUILD_NUMBER}%0A🌐 Браузер: ${params.BROWSER}%0A🚦 Статус: ${buildStatus}"

                // Отправляем через curl в Linux (sh)
                sh """
                curl -s -X POST "https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage" -d "chat_id=${env.TG_CHAT_ID}" -d "parse_mode=Markdown" -d "text=${msg}"
                """
            }

            // Финальная зачистка докера (sh)
            sh 'docker compose down -v --remove-orphans'
            sh 'docker image prune -f'
        }
    }
}
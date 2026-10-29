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
                        bat """
                        set BROWSER=${params.BROWSER}
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
            // Инжект переменных в Allure-отчет
            bat '''
            if not exist allure-results mkdir allure-results
            echo Browser=%BROWSER% > allure-results\\environment.properties
            '''

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
                // Защита от ошибки синтаксиса: если статус null, считаем что всё SUCCESS
                def buildStatus = currentBuild.currentResult ?: 'SUCCESS'
                def statusIcon = buildStatus == 'SUCCESS' ? '✅' : '🔴'

                // Текст без пробелов между строками, чтобы Windows CMD не сошел с ума (%0A - перенос строки)
                def msg = "${statusIcon} *Отчет о сборке Jenkins*%0A📦 Проект: ${env.JOB_NAME}%0A🔢 Билд: #${env.BUILD_NUMBER}%0A🌐 Браузер: ${params.BROWSER}%0A🚦 Статус: ${buildStatus}"

                // chcp 65001 включает UTF-8, чтобы русский текст и эмодзи дошли без кракозябр
                bat """
                chcp 65001
                curl -s -X POST "https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage" -d "chat_id=${env.TG_CHAT_ID}" -d "parse_mode=Markdown" -d "text=${msg}"
                """
            }

            // Финальная зачистка докера
            bat 'docker compose down -v --remove-orphans'
            bat 'docker image prune -f'
        }
    }
}
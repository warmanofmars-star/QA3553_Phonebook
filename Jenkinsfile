pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timestamps()
    }

    environment {
        // Секреты подтянутся из твоего сейфа Jenkins!
        USER_EMAIL = credentials('PHONEBOOK_EMAIL')
        USER_PASSWORD = credentials('PHONEBOOK_PASSWORD')
        ALLOW_MASS_DELETE = 'false'
        ENABLE_CONSOLE_LOGS = 'true'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests via Docker Compose') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh 'docker compose up --build --exit-code-from qa-framework'
                }
            }
        }
    }

    post {
        always {
            // 1. Вытаскиваем папку allure-results из тестового контейнера прямо в Jenkins
            sh 'docker cp $(docker compose ps -q qa-framework):/app/allure-results ./ || true'

            // 2. Убиваем контейнеры
            sh 'docker compose down -v'

            // 3. Генерируем отчет (теперь Jenkins знает, какой плагин использовать)
            allure([
                commandline: 'Allure',
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])
        }
    }
}
pipeline {
    agent any // Запускаемся прямо на мастере Jenkins

    options {
        buildDiscarder(logRotator(numToKeepStr: '5')) // Храним только 5 последних прогонов
        timestamps() // Добавляем время в логи
    }

    stages {
        stage('Checkout Code') {
            steps {
                // Скачиваем код из твоего GitHub
                checkout scm
            }
        }

        stage('Prepare Environment') {
            steps {
                // Создаем .env файл "на лету" (т.к. в Git его нет)
                sh '''
                echo "USER_EMAIL=warman.of.mars.2@gmail.com" > .env
                echo "USER_PASSWORD=Wwar123456\\$" >> .env
                echo "ALLOW_MASS_DELETE=false" >> .env
                echo "ENABLE_CONSOLE_LOGS=true" >> .env
                '''
            }
        }

        stage('Run Tests via Docker Compose') {
            steps {
                // Jenkins отдает команду твоему Docker Desktop!
                // Используем catchError, чтобы пайплайн не упал сразу, если тесты найдут баги
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh 'docker compose up --build --exit-code-from qa-framework'
                }
            }
        }
    }

    post {
        always {
            // Этап очистки: останавливаем Селеноид и удаляем тестовые контейнеры
            sh 'docker compose down -v'

            // Генерируем красивый Allure-отчет прямо в Jenkins
            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])
        }
    }
}
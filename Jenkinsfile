pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timestamps()
    }

    environment {
        // Секреты подтянутся из сейфа Jenkins
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

        stage('Fix DooD Volume Paradox & Network') {
            steps {
                // 1. Создаем Dockerfile для кастомного Селеноида
                // 2. Делаем override: прокидываем Селеноид в qa-network и ставим тесты в 1 поток (-n 0)
                // 3. Вырезаем конфликтный проброс папок
                sh '''
                cat <<EOF > Dockerfile.selenoid-override
FROM aerokube/selenoid:latest-release
COPY selenoid/browsers.json /etc/selenoid/browsers.json
EOF

                cat <<EOF > docker-compose.override.yml
services:
  selenoid:
    command: ["-conf", "/etc/selenoid/browsers.json", "-video-output-dir", "/opt/selenoid/video", "-container-network", "qa-network", "-service-startup-timeout", "1m"]
    build:
      context: .
      dockerfile: Dockerfile.selenoid-override
  qa-framework:
    command: ["pytest", "-n", "2", "--alluredir=allure-results"]
EOF

                grep -v "/etc/selenoid" docker-compose.yml > clean-compose.yml
                mv clean-compose.yml docker-compose.yml
                '''
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
            // 1. Вытаскиваем файлы из остановленного контейнера
            sh '''
            mkdir -p allure-results
            CONTAINER_ID=$(docker compose ps -q -a qa-framework)
            echo "ID контейнера с тестами: $CONTAINER_ID"

            if [ -n "$CONTAINER_ID" ]; then
                docker cp $CONTAINER_ID:/app/allure-results/. ./allure-results/ || echo "Ошибка при копировании!"
            else
                echo "Контейнер qa-framework не найден!"
            fi
            '''

            // 2. Убиваем контейнеры
            sh 'docker compose down -v'

            // 3. Генерируем отчет Allure
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
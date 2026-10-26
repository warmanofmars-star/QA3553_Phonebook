pipeline {
    agent any

    parameters {
        choice(name: 'BROWSER', choices: ['chrome', 'firefox', 'edge'], description: 'Выберите браузер для запуска тестов')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timestamps()
    }

    environment {
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

        stage('Fix DooD Volume Paradox & Optimize Load') {
            steps {
                sh """
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
    command: ["sh", "-c", "pytest -n 2 --browser_name=${params.BROWSER} --video=on --clean-alluredir --alluredir=allure-results"]
EOF

                grep -v "/etc/selenoid" docker-compose.yml > clean-compose.yml
                mv clean-compose.yml docker-compose.yml
                """
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
            // 1. Убиваем старую папку с результатами прошлых сборок (очистка кэша)
            sh 'rm -rf allure-results || true'

            // 2. Вытаскиваем свежие файлы из остановленного контейнера
            sh '''
            mkdir -p allure-results
            CONTAINER_ID=$(docker compose ps -q -a qa-framework)
            if [ -n "$CONTAINER_ID" ]; then
                docker cp $CONTAINER_ID:/app/allure-results/. ./allure-results/ || echo "Ошибка при копировании!"
            else
                echo "Контейнер qa-framework не найден!"
            fi
            '''

            // 3. Убиваем контейнеры
            sh 'docker compose down -v'

            // 4. Генерируем отчет с пробросом параметров прямо в виджет Environment
            allure([
                commandline: 'Allure',
                includeProperties: true,
                jdk: '',
                properties: [
                    [key: 'Browser', value: "${params.BROWSER}"],
                    [key: 'Environment', value: 'Local Docker Compose']
                ],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])
        }
    }
}
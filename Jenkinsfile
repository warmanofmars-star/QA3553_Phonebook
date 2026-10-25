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

        stage('Fix DooD Volume Paradox') {
            steps {
                // 1. Создаем "на лету" файлы-заплатки для сборки Селеноида
                sh '''
                cat <<EOF > Dockerfile.selenoid-override
FROM aerokube/selenoid:latest-release
COPY selenoid/browsers.json /etc/selenoid/browsers.json
EOF

                cat <<EOF > docker-compose.override.yml
services:
  selenoid:
    build:
      context: .
      dockerfile: Dockerfile.selenoid-override
EOF

                # 2. Вырезаем сломанный проброс папки из оригинального файла.
                # Используем безопасный разделитель | чтобы Groovy не ругался на слеши.
                sed -i '\|/etc/selenoid|d' docker-compose.yml
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

            // 3. Генерируем отчет
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
pipeline {
    agent any

    // 1. Добавляем тот самый "переключатель" (выпадающий список)
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
                // ВАЖНО: Здесь я заменил одинарные кавычки на двойные ("""),
                // чтобы Jenkins мог подставить наш параметр ${params.BROWSER} внутрь bash-скрипта
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
    # 2. Передаем выбранный в меню браузер во флаг --browser_name
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
            sh 'rm -rf allure-results || true'

            // Здесь оставляем одинарные кавычки, так как тут работают переменные самого Linux ($CONTAINER_ID)
            sh '''
            mkdir -p allure-results
            CONTAINER_ID=$(docker compose ps -q -a qa-framework)
            if [ -n "$CONTAINER_ID" ]; then
                docker cp $CONTAINER_ID:/app/allure-results/. ./allure-results/ || echo "Ошибка при копировании!"
            else
                echo "Контейнер qa-framework не найден!"
            fi
            '''

            sh 'docker compose down -v'

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
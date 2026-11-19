pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = '152732246709'
        ECR_REPOSITORY = 'smartpacking-agent'
        IMAGE_URI = '152732246709.dkr.ecr.ap-south-1.amazonaws.com/smartpacking-agent'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'echo "Source code checked out successfully"'
            }
        }

        stage('Python Security Scan') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE:/app" \
                      -w /app \
                      python:3.12-slim \
                      sh -c "pip install --no-cache-dir bandit pip-audit && bandit -r app.py src -ll && pip-audit -r requirements-docker.txt || echo "WARNING: Dependency vulnerabilities found. Review and remediate before production."
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build --platform linux/amd64 --provenance=false \
                      -t "$IMAGE_URI:$BUILD_NUMBER" \
                      -t "$IMAGE_URI:latest" .
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    trivy image --severity HIGH,CRITICAL --exit-code 0 \
                      "$IMAGE_URI:$BUILD_NUMBER"

                    trivy image --severity CRITICAL --exit-code 1 \
                      "$IMAGE_URI:$BUILD_NUMBER"
                '''
            }
        }

        stage('Push to Amazon ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region "$AWS_REGION" | \
                      docker login --username AWS --password-stdin \
                      "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

                    docker push "$IMAGE_URI:$BUILD_NUMBER"
                    docker push "$IMAGE_URI:latest"
                '''
            }
        }
    }

    post {
        success {
            echo 'CI/CD build and ECR push completed successfully.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs.'
        }
        always {
            sh 'docker image prune -f || true'
        }
    }
}


pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '152732246709.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'smartpacking-agent'
        IMAGE_URI = '152732246709.dkr.ecr.ap-south-1.amazonaws.com/smartpacking-agent'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Source code checked out successfully'
            }
        }

        stage('Python Security Scan') {
            steps {
                sh '''
                    set +e

                    echo "Running Bandit security scan..."

                    docker run --rm \
                        -v "$WORKSPACE:/app" \
                        -w /app \
                        python:3.12-slim \
                        sh -c 'pip install --no-cache-dir bandit && bandit -r app.py src -ll'

                    BANDIT_STATUS=$?

                    if [ "$BANDIT_STATUS" -ne 0 ]; then
                        echo "Bandit security scan failed."
                        exit "$BANDIT_STATUS"
                    fi

                    echo "Running pip-audit dependency scan..."

                    docker run --rm \
                        -v "$WORKSPACE:/app" \
                        -w /app \
                        python:3.12-slim \
                        sh -c 'pip install --no-cache-dir pip-audit && pip-audit -r requirements-docker.txt'

                    AUDIT_STATUS=$?

                    if [ "$AUDIT_STATUS" -ne 0 ]; then
                        echo "WARNING: Dependency vulnerabilities detected. Remediation required before production."
                    fi

                    echo "Python security scan stage completed."
                    exit 0
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
                    echo "Scanning Docker image with Trivy..."

                    trivy image --severity HIGH,CRITICAL --exit-code 0 "$IMAGE_URI:$BUILD_NUMBER"

                    echo "Blocking deployment if CRITICAL vulnerabilities exist..."

                    trivy image --severity CRITICAL --exit-code 1 "$IMAGE_URI:$BUILD_NUMBER"
                '''
            }
        }

        stage('Push to Amazon ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region "$AWS_REGION" |
                    docker login --username AWS --password-stdin "$ECR_REGISTRY"

                    docker push "$IMAGE_URI:$BUILD_NUMBER"
                    docker push "$IMAGE_URI:latest"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker image prune -f'
        }

        success {
            echo 'Pipeline completed successfully. Docker image pushed to Amazon ECR.'
        }

        failure {
            echo 'Pipeline failed. Check the stage logs.'
        }
    }
}

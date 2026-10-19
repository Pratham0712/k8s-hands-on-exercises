pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Creating virtual environment and installing dependencies...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip freeze
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running unit tests...'
                sh '''
                    . venv/bin/activate
                    python -m unittest discover -s . -p "test_*.py" -v
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying application...'
                sh '''
                    mkdir -p python-app-deploy
                    cp app.py requirements.txt python-app-deploy/
                    ls -l python-app-deploy
                '''
            }
        }

        stage('Run Application') {
            steps {
                echo 'Starting application in background...'
                sh '''
                    . venv/bin/activate
                    nohup python python-app-deploy/app.py > python-app-deploy/app.log 2>&1 &
                    echo $! > python-app-deploy/app.pid
                    echo "Started app with PID $(cat python-app-deploy/app.pid)"
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                echo 'Hitting the running app over HTTP...'
                sh '''
                    EXPECTED="Hello, Jenkins Multi-Stage Pipeline!"
                    for i in $(seq 1 10); do
                        if RESPONSE=$(curl -fsS http://127.0.0.1:5000/); then
                            echo "Attempt $i -> $RESPONSE"
                            if [ "$RESPONSE" = "$EXPECTED" ]; then
                                echo "Smoke test PASSED"
                                exit 0
                            fi
                            echo "Unexpected response"
                            exit 1
                        fi
                        sleep 1
                    done
                    echo "App never came up. app.log:"
                    cat python-app-deploy/app.log
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            echo 'Stopping application...'
            sh '''
                if [ -f python-app-deploy/app.pid ]; then
                    kill "$(cat python-app-deploy/app.pid)" 2>/dev/null || true
                    rm -f python-app-deploy/app.pid
                fi
            '''
        }
        success { echo 'Pipeline completed successfully!' }
        failure { echo 'Pipeline failed. Check the logs for more details.' }
    }
}

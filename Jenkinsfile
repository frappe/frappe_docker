pipeline {
    agent any
    environment {
        GITHUB_TOKEN = credentials('github')
        IMAGE_NAME = 'ghcr.io/finkash-pty/frappe_docker'
        RELEASE_VERSION = readFile('version').trim()
        IMAGE_REPO = "${IMAGE_NAME}:${RELEASE_VERSION}"
        PLATFORM = 'linux/amd64,linux/arm64'
    }
    stages {
        stage('Login to image Repository') {
            steps {
                sh 'echo $GITHUB_TOKEN_PSW | docker login ghcr.io -u GITHUB_TOKEN_USR --password-stdin'
            }
        }
        stage('Prepare Builder'){
            steps{
                script{
                    sh 'export DOCKER_CLI_EXPERIMENTAL=enabled'
                    sh 'docker buildx use multiplatformbuilder'
                }
            }
        }
        stage('Build Image') {
            steps {
                script {
                    sh "docker buildx build --platform $PLATFORM --cache-from type=local,src=$IMAGE_REPO --cache-to type=local,dest=/tmp/.buildx-cache --push --tag $IMAGE_REPO ."
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}
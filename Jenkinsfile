pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'LightsOn-Metadata-bucket'
        BUCKET_DEST_DIR = env.GIT_BRANCH.tokenize('/').last()
        BUCKET_NAMESPACE = 'bmsfecivotax'
        DOCKER_IMAGE_NAME = 'json-validator:latest'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    stages {

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -f Dockerfile --rm --network=host -t ${DOCKER_IMAGE_NAME} ."
                }
            }
        }

        stage('Validate JSON Files') {
            steps {
                script {
                    def status = sh(script: "docker run --rm ${DOCKER_IMAGE_NAME} python3 validate_json.py", returnStatus: true)
                    if (status != 0) {
                        error 'JSON validation failed.'
                    }
                }
            }
        }

        stage('Archive Artifacts') {
            when {
                expression {
                    def isNotPR = !env.CHANGE_ID || env.CHANGE_ID.trim() == ""
                    def isMasterBranch = env.GIT_BRANCH?.trim().startsWith("origin/master")
                    return isNotPR && isMasterBranch
                }
            }
            steps {
                script {
                    sh "mkdir -p ${BUCKET_DEST_DIR}"
                    sh 'mv *_DBA/ ' + BUCKET_DEST_DIR
                    sh "zip -r ${BUCKET_DEST_DIR}.zip ${BUCKET_DEST_DIR}"
                    def sha256 = sh(script: "sha256sum ${BUCKET_DEST_DIR}.zip | awk '{print \$1}'", returnStdout: true).trim()
                    echo "SHA-256: ${sha256}"
                    env.ZIP_SHA256 = sha256
                }
            }
        }

        stage('Upload to OCI Object Storage') {
            when {
                expression {
                    def isNotPR = !env.CHANGE_ID || env.CHANGE_ID.trim() == ""
                    def isMasterBranch = env.GIT_BRANCH?.trim().startsWith("origin/master")
                    return isNotPR && isMasterBranch
                }
            }
            steps {
                withCredentials([
                    file(credentialsId: 'OCI_SVC_CONFIG', variable: 'OCI_CONFIG_FILE'),
                    file(credentialsId: 'OCI_SVC_KEY', variable: 'OCI_KEY_FILE')
                ]) {
                    script {
                        def ociConfigDir = "${WORKSPACE}/.oci"


                        sh "ls -l ${WORKSPACE}/${BUCKET_DEST_DIR}.zip"

                        sh """
                            docker run --rm \
                                -v "${WORKSPACE}:/app" \
                                -w /app \
                                ${DOCKER_IMAGE_NAME} \
                                ls -lh /app && ls -lh /app/${BUCKET_DEST_DIR}.zip
                        """



                        sh """
                            mkdir -p ${ociConfigDir}
                            cp "${OCI_CONFIG_FILE}" ${ociConfigDir}/config
                            cp "${OCI_KEY_FILE}" ${ociConfigDir}/svc.pem
                            chmod 600 ${ociConfigDir}/config
                            chmod 600 ${ociConfigDir}/svc.pem
                        """

                        sh """
                            docker run --rm \
                                -v "${ociConfigDir}:/root/.oci" \
                                -v "${WORKSPACE}:/app" \
                                -w /app \
                                ${DOCKER_IMAGE_NAME} \
                                oci os object put \
                                    --bucket-name ${OCI_BUCKET_NAME} \
                                    --file /app/${BUCKET_DEST_DIR}.zip \
                                    --name ${BUCKET_DEST_DIR}.zip \
                                    --metadata '{\"sha256\":\"'"${env.ZIP_SHA256}"'\"}'
                        """

                        sh "rm -rf ${ociConfigDir}"
                        echo "Using SHA-256 checksum: ${env.ZIP_SHA256}"
                    }
                }
            }
        }

    } // closes stages

    post {
        always {
            cleanWs()
        }
    }
} // closes pipeline

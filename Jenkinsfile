pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'LightsOn-Metadata-bucket'
        BUCKET_DEST_DIR = 'master-oc2/'
        OCI_CONFIG_FILE_ID = 'OCI_CONFIG_FILE' // Jenkins credential ID for OCI config file
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
                    // Build the Docker image
                    sh "docker build -f Dockerfile --rm --network=host -t ${DOCKER_IMAGE_NAME} ."
                }
            }
        }

        stage('Validate JSON Files') {
            steps {
                script {
                    // Run Docker container to validate JSON files
                    def status = sh(script: "docker run --rm ${DOCKER_IMAGE_NAME}", returnStatus: true)
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
                    def isMasterOc2Branch = env.GIT_BRANCH?.trim() == 'origin/master-oc1'
                    return isNotPR && isMasterOc2Branch
                }
            }
            steps {
                script {
                    // Create a zip file containing the SITE_DBA and SLA_DBA folders
                    sh 'mkdir ${BUCKET_DEST_DIR}'
                    sh 'mv *_DBA/ ${BUCKET_DEST_DIR}'
                    sh 'zip -r LON_METADATA.zip ${BUCKET_DEST_DIR}'
                    // Calculate SHA-256 checksum and store it in a variable
                    def sha256 = sh(script: 'sha256sum LON_METADATA.zip | awk \'{ print $1 }\'', returnStdout: true).trim()
                    echo "SHA-256: ${sha256}"
                    env.ZIP_SHA256 = sha256
                }
            }
        }

        stage('Upload to OCI Object Storage') {
            when {
                expression {
                    def isNotPR = !env.CHANGE_ID || env.CHANGE_ID.trim() == ""
                    def isMasterOc2Branch = env.GIT_BRANCH?.trim() == 'origin/master-oc1'
                    return isNotPR && isMasterOc2Branch
                }
            }
            steps {
                script {
                    // Delete all files from the bucket. This is to ensure any files removed from GIT is also deleted from the bucket
                    withCredentials([file(credentialsId: "${OCI_CONFIG_FILE_ID}", variable: 'OCI_CONFIG_FILE')]) {
                        sh '''
                        export PATH=$PATH:/home/jenkins/bin
                        oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force --config-file ${OCI_CONFIG_FILE}
                        oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${WORKSPACE} --include "*.json" --include "*.zip" --overwrite --config-file ${OCI_CONFIG_FILE}
                        '''
                    }
                }
                // Use the SHA-256 checksum from the previous stage
                echo "Using SHA-256 checksum: ${env.ZIP_SHA256}"
                // Add further steps that require the checksum her
            }



        }

    }

    post {
        always {
            // Clean up workspace after build
            cleanWs()
        }
    }
}
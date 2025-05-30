pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'LightsOn-Metadata-bucket'
        BUCKET_DEST_DIR = 'master-oc2/'
        OCI_CONFIG_FILE_ID = 'OCI_CONFIG' // Jenkins credential ID for OCI config file
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
                withCredentials([
                    file(credentialsId: OCI_CONFIG_FILE_ID, variable: 'OCI_KEY_FILE')
                ]) {
                    withEnv([
                        'file_path=LON_METADATA.zip'
                    ]) {
                        sh 'pip3 install --user oci'
                        sh 'python3 upload_zip_to_oci.py'
                    }
                }
                // here comes the problem
                echo "Using SHA-256 checksum: ${env.ZIP_SHA256}"
                // Add further steps here
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
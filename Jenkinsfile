pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        VENV_DIR = '/home/venv'
        BUCKET_DEST_DIR = 'master-oc2/'
        OCI_CONFIG_FILE_ID = 'OCI_CONFIG_FILE' // Jenkins credential ID for OCI config file
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    stages {
        stage('Setup Virtual Environment and Install OCI CLI') {
            steps {
                script {
                    sh '''
                    apt-get install -y python3 python3-venv python3-pip zip
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install oci-cli
                    '''
                }
            }
        }

        stage('Archive Artifacts') {
            steps {
                // Add your artifact archiving steps here
                script {
                    // Create a zip file containing the SITE_DBA and SLA_DBA folders
                    sh '''
                    zip -r LON_METADATA.zip SITE_DBA SLA_DBA
                    // Calculate SHA-256 checksum and store it in a variable
                    def sha256 = sh(script: 'sha256sum LON_METADATA.zip | awk \'{ print $1 }\'', returnStdout: true).trim()
                    echo "SHA-256: ${sha256}"
                    // Store the checksum in the environment variable
                    env.ZIP_SHA256 = sha256
                    '''
                }
            }
        }
        
        stage('Upload to OCI Object Storage') {
            steps {
                script {
                    // Delete all files from the bucket. This is to ensure any files removed from GIT is also deleted from the bucket
                    withCredentials([file(credentialsId: "${OCI_CONFIG_FILE_ID}", variable: 'OCI_CONFIG_FILE')]) {
                        sh """
                        . ${VENV_DIR}/bin/activate
                        oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force --config-file \${OCI_CONFIG_FILE}
                        oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${WORKSPACE} --prefix ${BUCKET_DEST_DIR} --include '*.zip' --overwrite --config-file \${OCI_CONFIG_FILE}
                        """
                    }
                }
            }
        }


        stage('Trigger SLAPS Scan') {
            steps {
                script {
                    // Use the SHA-256 checksum from the previous stage
                    echo "Using SHA-256 checksum: ${env.ZIP_SHA256}"
                    // Add further steps that require the checksum here
                }
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

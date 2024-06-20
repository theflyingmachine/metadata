pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        VENV_DIR = '/home/venv'
        BUCKET_DEST_DIR = 'master-oc2/'
        OCI_CONFIG_FILE_ID = 'OCI_CONFIG_FILE' // Jenkins credential ID for OCI config file
        OCI_KEY_FILE_ID = 'OCI_KEY_FILE'   // Jenkins credential ID for OCI API key (PEM file)
    }

    stages {
        stage('Upload to OCI Object Storage') {
            steps {
                script {
                    // Echo statements to verify credential IDs
                    echo "OCI_CONFIG_FILE_ID: ${OCI_CONFIG_FILE_ID}"
                    echo "OCI_KEY_FILE_ID: ${OCI_KEY_FILE_ID}"

                    // Load OCI config file and key file from Jenkins credentials
                    withCredentials([file(credentialsId: "${OCI_CONFIG_FILE_ID}", variable: 'OCI_CONFIG_FILE')]) {
                        withCredentials([file(credentialsId: "${OCI_KEY_FILE_ID}", variable: 'OCI_KEY_FILE')]) {
                            sh """
                            . ${VENV_DIR}/bin/activate
                            oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force --config-file \${OCI_CONFIG_FILE} --key-file \${OCI_KEY_FILE}
                            oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${WORKSPACE} --prefix ${BUCKET_DEST_DIR} --include '*.json' --overwrite --config-file \${OCI_CONFIG_FILE} --key-file \${OCI_KEY_FILE}
                            """
                        }
                    }
                }
            }
        }
    }
}

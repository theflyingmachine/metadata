pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        VENV_DIR = '/home/venv'
        BUCKET_DEST_DIR = 'master-oc2/'
    }

    stages {
        stage('Upload to OCI Object Storage') {
            steps {
                script {

                    // Load OCI config file and key file from Jenkins credentials

                            sh """
                            . ${VENV_DIR}/bin/activate
                            oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force --config-file \${OCI_CONFIG_FILE} --key-file \${OCI_KEY_FILE}
                            oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${WORKSPACE} --prefix ${BUCKET_DEST_DIR} --include '*.json' --overwrite
                            """
                       
                }
            }
        }
    }
}

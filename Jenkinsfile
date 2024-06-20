pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        VENV_DIR = '/home/venv'
        BUCKET_DEST_DIR = 'master-oc2/'
        OCI_CLI_CONFIG_FILE = credentials('OCI_CLI_CONFIG_FILE')
    }

    stages {

        stage('Setup Virtual Environment and Install OCI CLI') {
            steps {
                script {
                    sh '''
                    apt-get install -y python3 python3-venv python3-pip
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install oci-cli
                    '''
                }
            }
        }

        stage('Configure OCI CLI') {
            steps {
                sh '''
                mkdir -p ~/.oci
                echo "${OCI_CLI_CONFIG_FILE}" > ~/.oci/config1
                chmod 600 ~/.oci/config1
                '''
            }
        }

        stage('Upload to OCI Object Storage') {
            steps {
                script {
                    // Delete all files from the bucket and upload. This is to ensure any files removed from GIT is also deleted from the bucket
                    sh """
                    . ${VENV_DIR}/bin/activate
                    oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force
                    oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${WORKSPACE} --prefix ${BUCKET_DEST_DIR} --include '*.json' --overwrite
                    """       
                }
            }
        }
    }
}

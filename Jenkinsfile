pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        VENV_DIR = '/home/venv'
        BUCKET_DEST_DIR = 'master-oc2/'
        OCI_CONFIG_FILE = credentials('OCI_CONFIG_FILE')
        SECRET_FILE_ID = 'OCI_CONFIG_FILE'  // Jenkins credential ID for the secret file
        TARGET_FILE_PATH = '~/.oci/config1'  // Path where you want to create the file
  
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

        // stage('Configure OCI CLI') {
        //     steps {
        //         sh '''
        //         mkdir -p ~/.oci
        //         echo "${OCI_CONFIG_FILE}" > ~/.oci/config1
        //         chmod 600 ~/.oci/config1
        //         '''
        //     }
        // }

        stage('Create File from Secret') {
            steps {
                script {
                    // Load the secret file from Jenkins credentials
                    withCredentials([file(credentialsId: "${SECRET_FILE_ID}", variable: 'SECRET_FILE')]) {
                        // Read the content of the secret file
                        def secretContent = readFile(file: "${SECRET_FILE}")

                        // Write the content to the target file
                        writeFile(file: "${TARGET_FILE_PATH}", text: secretContent)

                        // Print a message to indicate the file was created successfully
                        echo "File created successfully at ${TARGET_FILE_PATH}"
                    }
                }
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


pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        VENV_DIR = '/home/venv'
    }
    stages {
         stage('Cleanup Bucket') {
            steps {
                // Delete all files from the bucket. This is to ensure any files removed from GIT is also deleted from the bucket
                sh '''
                . ${VENV_DIR}/bin/activate

               	oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force
                '''    
            }
        }

        stage('Upload to OCI Object Storage') {
            steps {
                script {
                    // Do a bulk upload
                    sh '''
                    . ${VENV_DIR}/bin/activate

                    oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${WORKSPACE} --prefix master-oc2/ --include '*.json' --overwrite
                    '''      
                }
            }
        }

    }
}

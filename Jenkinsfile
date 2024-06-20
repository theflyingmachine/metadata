
pipeline {
    agent any

    environment {
        OCI_BUCKET_NAME = 'MetadataSync'
        OCI_REGION = 'ap-mumbai-1' // Update with your OCI region
        VENV_DIR = 'venv' // Directory for the virtual environment
        SOURCE_DIR = '/var/jenkins_home/workspace/MetadataSyncPipeline'
    }
    stages {
        stage('Checkout') {
            steps {
                // Mark the workspace as a safe directory for Git
                
               	sh 'git config --global --add safe.directory /var/jenkins_home/workspace/MetadataSyncPipeline'
                git branch: 'master-oc2', url: 'https://github.com/theflyingmachine/metadata.git'
            }
        }

         stage('Cleanup Bucket') {
            steps {
                // Delete all files from the bucket. This is to ensure any files removed from GIT is also deleted from the bucket
                sh '''
                . /home/venv/bin/activate
               	oci os object bulk-delete -bn ${OCI_BUCKET_NAME} --force
                '''    
            }
        }

        stage('Upload to OCI Object Storage') {
            steps {
                script {
                    // Activate the virtual environment
                    sh '''
                    cd /var/jenkins_home/workspace/MetadataSyncPipeline
                    . /home/venv/bin/activate

                    oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${SOURCE_DIR} --prefix master-oc2/ --include '*.json' --overwrite
                    '''      
                }
            }
        }

    }
}


pipeline {
    agent any

    environment {
        OCI_CLI_CONFIG_FILE = credentials('OCI_CLI_CONFIG_FILE')
        OCI_BUCKET_NAME = 'MetadataSync'
        OCI_CLI_PROFILE = 'DEFAULT' // Update with your OCI CLI profile name
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
                
               	sh 'oci os object bulk-delete --profile ${OCI_CLI_PROFILE} -bn ${OCI_BUCKET_NAME}'
                
            }
        }

        stage('Upload to OCI Object Storage') {
            steps {
                script {
                    // Activate the virtual environment
                    sh '''
                    cd /var/jenkins_home/workspace/MetadataSyncPipeline
                    . /home/venv/bin/activate

                    oci os object bulk-upload -bn ${OCI_BUCKET_NAME} --src-dir ${SOURCE_DIR} --config-file /root/.oci/config --profile ${OCI_CLI_PROFILE} --region ${OCI_REGION} --include '*.json' --overwrite
                    '''      
                }
            }
        }

    }
}

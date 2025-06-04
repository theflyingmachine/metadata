pipeline {
    agent {
              dockerfile {
                    filename 'Dockerfile'
                    additionalBuildArgs '--network=host --rm'
                }
            }

    environment {
        OCI_BUCKET_NAME = 'LightsOn-Metadata-bucket'
        BUCKET_DEST_DIR = env.GIT_BRANCH.tokenize('/').last()
        BUCKET_NAMESPACE = 'bmsfecivotax'
        DOCKER_IMAGE_NAME = 'json-validator:latest'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    stages {

//         stage('Build Docker Image') {
//             steps {
//                 script {
//                     sh "docker build -f Dockerfile --rm --network=host -t ${DOCKER_IMAGE_NAME} ."
//                 }
//             }
//         }

        stage('Validate JSON Files') {
            steps {
                script {
                    def status = sh(script: "python3 validate_json.py", returnStatus: true)
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
                    def isMasterBranch = env.GIT_BRANCH?.trim().startsWith("origin/master")
                    return isNotPR && isMasterBranch
                }
            }
            steps {
                script {
                    sh "mkdir -p ${BUCKET_DEST_DIR}"
                    sh 'mv *_DBA/ ' + BUCKET_DEST_DIR
                    sh "zip -r ${BUCKET_DEST_DIR}.zip ${BUCKET_DEST_DIR}"
                    def sha256 = sh(script: "sha256sum ${BUCKET_DEST_DIR}.zip | awk '{print \$1}'", returnStdout: true).trim()
                    echo "SHA-256: ${sha256}"
                    env.ZIP_SHA256 = sha256
//                     stash includes: "${BUCKET_DEST_DIR}.zip", name: "oci_zip"
                }
            }
        }

        stage('Upload to OCI Object Storage') {
            when {
                expression {
                    def isNotPR = !env.CHANGE_ID || env.CHANGE_ID.trim() == ""
                    def isMasterBranch = env.GIT_BRANCH?.trim().startsWith("origin/master")
                    return isNotPR && isMasterBranch
                }
            }
            steps {
                withCredentials([
                    file(credentialsId: 'OCI_SVC_CONFIG', variable: 'OCI_CONFIG_FILE'),
                    file(credentialsId: 'OCI_SVC_KEY', variable: 'OCI_KEY_FILE')
                ]) {
                    script {

                        sh """
                            id
                            pwd
                            cp "${OCI_CONFIG_FILE}" ${WORKSPACE}/config
                            cp "${OCI_KEY_FILE}" ${WORKSPACE}/svc.pem
                            chmod 600 ${WORKSPACE}/config
                            chmod 600 ${WORKSPACE}/svc.pem
                        """

                         sh """
                            oci os object put \
                                       --bucket-name ${OCI_BUCKET_NAME} \
                                       --file ${BUCKET_DEST_DIR}.zip \
                                       --name ${BUCKET_DEST_DIR}.zip \
                                       --config-file ${WORKSPACE}/config \
                                      --metadata '{\"sha256\":\"'"${env.ZIP_SHA256}"'\
                        """
//                         unstash "oci_zip"
//                         sh """
//                             docker run --rm \
//                                 -v "${ociConfigDir}:/root/.oci" \
//                                 -v "${WORKSPACE}:/app" \
//                                 ${DOCKER_IMAGE_NAME} \
//                                 oci os object put \
//                                     --bucket-name ${OCI_BUCKET_NAME} \
//                                     --file /root/.oci/${BUCKET_DEST_DIR}.zip \
//                                     --name ${BUCKET_DEST_DIR}.zip \
//                                     --metadata '{\"sha256\":\"'"${env.ZIP_SHA256}"'\"}'
//                         """

//                         sh "rm -rf ${ociConfigDir}"
                        echo "Using SHA-256 checksum: ${env.ZIP_SHA256}"
                    }
                }
            }
        }

    } // closes stages

    post {
        always {
            cleanWs()
        }
    }
} // closes pipeline

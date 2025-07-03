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
        OCI_SVC_CONFIG_ID = 'OCI_SVC_CONFIG'
        OCI_SVC_KEY_ID = 'OCI_SVC_KEY'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    stages {

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
                    file(credentialsId: OCI_SVC_CONFIG_ID, variable: 'OCI_CONFIG_FILE'),
                    file(credentialsId: OCI_SVC_KEY_ID, variable: 'OCI_KEY_FILE')
                ]) {
                    script {

                        sh """
                            cp "${OCI_CONFIG_FILE}" ${WORKSPACE}/config
                            cp "${OCI_KEY_FILE}" ${WORKSPACE}/svc.pem
                            chmod 700 ${WORKSPACE}/config
                            echo 'key_file = ${WORKSPACE}/svc.pem' >> ${WORKSPACE}/config
                            chmod 600 ${WORKSPACE}/config
                            chmod 600 ${WORKSPACE}/svc.pem
                        """

                        sh """
                            oci os object put \
                                       --bucket-name ${OCI_BUCKET_NAME} \
                                       --file ${BUCKET_DEST_DIR}.zip \
                                       --name ${BUCKET_DEST_DIR}.zip \
                                       --config-file ${WORKSPACE}/config \
                                       --force
                        """
                        echo "Using SHA-256 checksum: ${env.ZIP_SHA256}"
//                         ------------------------------------------------------------------------------------------------------
//                         If Jenkins instance has access to OCI corporate network, Uncomment below steps to automate SLAPS scan.
//                         For now, since we can not automate SLAPS scan, please execute the next command to initiate SLAPS
//                         scan on the ZIP file. The command will be printed on the Jenkins console.
//                         ------------------------------------------------------------------------------------------------------
                        sh """
                            oci --config-file ${WORKSPACE}/config \
                            raw-request --http-method POST \
                            --target-uri "https://slaps.oci.oraclecorp.com/slaps/v1/casperToCasper/receiver/notification?manifestResourceCompartmentId=ocid1.compartment.oc1..aaaaaaaa2vuehpa3dkshwjkg2lzmlmp55mjkzqdvbht5rsxlf3olm4pzgtna" \
                            --request-body '{
                                "bucketName": "${OCI_BUCKET_NAME}",
                                "objectName": "${BUCKET_DEST_DIR}.zip",
                                "checksum": "SHA256:${env.ZIP_SHA256}",
                                "name": "${BUCKET_DEST_DIR}.zip",
                                "version": "${env.BUILD_NUMBER}",
                                "type": "generic",
                                "description": "LightsOn Metadata",
                                "tenancyId": "ocid1.tenancy.oc1..aaaaaaaamh7v4d6y5nfciy26ofaqmdyrkj3u277qiaemdwqif6oeoqvzkdbq",
                                "namespace": "idjqh1xkxljy",
                                "region": "us-ashburn-1",
                                "phonebookId": "ohai_lightsonnetwork",
                                "isReportFindings": false
                            }'
                        """

                        echo """--- IMPORTANT --- SLAPS SCAN ----
=====================================================================================================
Before deploying any artifact to the OC2 realm, it must be scanned using SLAPS. If the associated metadata is intended for the OC2 realm, please execute the following command to initiate the SLAPS scan on the ZIP file.

Important Notes:
 -The SLAPS scan can only be triggered from within the Oracle corporate network.
 -Ensure that you are connected to the Oracle VPN before initiating the scan.
 -Due to this network restriction, this step cannot be automated via Jenkins.

For further details, please refer to the following documentation:
Reference: https://confluence.oraclecorp.com/confluence/display/ISD/OCI+ISD+Operations+-+SLAPS+Scanning+and+Artifacts+Push+Service
=====================================================================================================

oci raw-request --http-method POST --target-uri "https://slaps.oci.oraclecorp.com/slaps/v1/casperToCasper/receiver/notification?manifestResourceCompartmentId=ocid1.compartment.oc1..aaaaaaaa2vuehpa3dkshwjkg2lzmlmp55mjkzqdvbht5rsxlf3olm4pzgtna" --request-body '{"bucketName": "${OCI_BUCKET_NAME}","objectName": "${BUCKET_DEST_DIR}.zip","checksum": "SHA256:${env.ZIP_SHA256}","name": "${BUCKET_DEST_DIR}.zip","version": "${env.BUILD_NUMBER}","type": "generic","description": "LightsOn Metadata","tenancyId": "ocid1.tenancy.oc1..aaaaaaaamh7v4d6y5nfciy26ofaqmdyrkj3u277qiaemdwqif6oeoqvzkdbq","namespace": "idjqh1xkxljy","region": "us-ashburn-1","phonebookId": "ohai_lightsonnetwork","isReportFindings": false}'

                        """
                    }
                }
            }
        }

    }

    post {
        always {
            cleanWs()
        }
    }
}

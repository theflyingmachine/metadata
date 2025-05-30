import oci
import os

# Read private key content from file
with open(os.environ["OCI_KEY_FILE"], "r") as f:
    WEB_CONFIG = f.read()

# === USER INPUT ===
bucket_name = 'LightsOn-Metadata-bucket'
namespace = 'bmsfecivotax'  # Replace with your actual namespace
file_path = os.environ["file_path"]
object_name = os.path.basename(file_path)

# === INITIATE OBJECT STORAGE CLIENT ===
object_storage = oci.object_storage.ObjectStorageClient(WEB_CONFIG)

# === UPLOAD FILE ===
try:
    with open(file_path, 'rb') as f:
        put_object_response = object_storage.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name,
            put_object_body=f
        )
    print(f"Upload successful: {object_name}")
except Exception as e:
    print(f"Error uploading file: {e}")

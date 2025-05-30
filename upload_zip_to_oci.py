import ast
import oci
import os

with open(os.environ["OCI_KEY_FILE"], "r") as f:
    WEB_CONFIG = f.read()

namespace = os.environ["namespace"]
file_path = os.environ["file_path"]
bucket_name = os.environ["bucket_name"]
object_name = os.path.basename(file_path)
object_storage = oci.object_storage.ObjectStorageClient(ast.literal_eval(WEB_CONFIG))

with open(file_path, 'rb') as f:
    put_object_response = object_storage.put_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name,
        put_object_body=f
    )
print(f"Upload successful: {object_name}")

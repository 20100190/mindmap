from google.cloud import storage
import os
import json

def upload_result_to_gcs(result_dict: dict, filename: str):
    client = storage.Client()
    bucket = client.bucket(os.getenv("RESULTS_BUCKET", "mindmap-results"))
    blob = bucket.blob(f"query_results/{filename}")
    blob.upload_from_string(json.dumps(result_dict, indent=2), content_type="application/json")
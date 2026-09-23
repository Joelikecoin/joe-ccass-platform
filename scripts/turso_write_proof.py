"""Runtime-only caller for the temporary Turso write proof route."""
import json
import os
import time
import urllib.request

base = "http://127.0.0.1:" + os.getenv("PORT", "10000")
for attempt in range(90):
    request = urllib.request.Request(
        base + "/internal/access-migration/turso-proof",
        method="POST",
        headers={"X-API-Key": os.getenv("API_KEY", "")},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.load(response)
            print("TURSO_ACCESS_MIGRATION_PROOF " + json.dumps({
                "status": response.status,
                "result": body.get("result"),
                "write": body.get("write"),
                "readback": body.get("readback"),
                "cleaned": body.get("cleaned"),
                "test_key_prefix": body.get("test_key_prefix"),
            }), flush=True)
            break
    except Exception as exc:
        if attempt == 89:
            print("TURSO_ACCESS_MIGRATION_PROOF " + json.dumps({
                "status": 0, "result": "ERROR", "exception_type": type(exc).__name__
            }), flush=True)
        else:
            time.sleep(2)

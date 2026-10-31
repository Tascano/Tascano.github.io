"""Checks for the lab: the laptop path end to end, and the AWS path against moto's fake DynamoDB and S3.

    pip install pytest moto
    python -m pytest -q test_lab.py
"""
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def run_batch(tmp, *args):
    out = subprocess.run([sys.executable, str(HERE / "precompute.py"), "--data", str(tmp), *args],
                         capture_output=True, text=True, cwd=HERE)
    return out.returncode, out.stdout + out.stderr


def load_service(monkeypatch, **env):
    for key in ("DATA_DIR", "BUCKET", "CACHE_SIZE", "BLOOM", "DB_DELAY_MS"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import service
    return importlib.reload(service)


def test_laptop_end_to_end(tmp_path, monkeypatch):
    code, out = run_batch(tmp_path, "--day", "2026-10-30")
    assert code == 0, out
    manifest = json.loads((tmp_path / "current.json").read_text())
    service = load_service(monkeypatch, DATA_DIR=str(tmp_path))
    service.refresh()
    client = TestClient(service.app)

    import sqlite3
    db = sqlite3.connect(tmp_path / manifest["store"]["path"])
    known_key, known_score = db.execute("SELECT k, v FROM scores LIMIT 1").fetchone()
    asin, creative = known_key.split("|")
    body = client.post("/relevance", json={"asin": asin, "creatives": [creative, "cr-does-not-exist"]}).json()
    assert body["version"] == "2026-10-30"
    assert body["scores"][creative] == known_score
    assert body["scores"]["cr-does-not-exist"] == 0.0
    metrics = client.get("/metrics").json()
    assert metrics["bloom_no"] >= 1 and metrics["db_keys"] >= 1

    # Publishing the next day swaps the whole snapshot.
    code, out = run_batch(tmp_path, "--day", "2026-10-31")
    assert code == 0, out
    service.refresh()
    assert client.get("/healthz").json()["version"] == "2026-10-31"


def test_publish_is_refused_when_data_looks_broken(tmp_path):
    assert run_batch(tmp_path, "--day", "2026-10-30")[0] == 0
    code, out = run_batch(tmp_path, "--day", "2026-10-31", "--threshold", "0.95")  # far fewer rows
    assert code != 0 and "refusing to publish" in out
    assert json.loads((tmp_path / "current.json").read_text())["version"] == "2026-10-30"  # still live


def test_aws_path_with_moto(tmp_path, monkeypatch):
    moto = pytest.importorskip("moto")
    import boto3
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(key, "testing")
    with moto.mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="scores", BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": "k", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "k", "KeyType": "HASH"}])
        boto3.client("s3").create_bucket(Bucket="lab-data")
        sys.argv = ["precompute.py", "--day", "2026-10-30", "--data", str(tmp_path / "batch"),
                    "--threshold", "0.95", "--table", "scores", "--bucket", "lab-data"]
        import precompute
        importlib.reload(precompute).main()
        manifest = json.loads(boto3.client("s3").get_object(Bucket="lab-data", Key="current.json")["Body"].read())
        assert manifest["store"] == {"kind": "dynamodb", "table": "scores"}
        item = boto3.client("dynamodb").scan(TableName="scores", Limit=1)["Items"][0]
        version, asin, creative = item["k"]["S"].split("|")
        assert version == "2026-10-30"

        service = load_service(monkeypatch, BUCKET="lab-data", DATA_DIR=str(tmp_path / "host"))
        service.refresh()
        body = TestClient(service.app).post("/relevance", json={"asin": asin, "creatives": [creative]}).json()
        assert body["version"] == "2026-10-30"
        assert body["scores"][creative] == float(item["v"]["N"])

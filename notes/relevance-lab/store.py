"""Where the precomputed scores live: SQLite on your laptop, DynamoDB on AWS.

Both stores keep every version side by side (the version is part of the key or the file name), so a host
reading version N never sees rows from version N+1. That is the "publish as one version" rule from the post.
"""
import sqlite3
import threading
import time

DELAY_S = 0.0  # set by the service to make the database artificially slow (experiment 4)


class SqliteStore:
    """One SQLite file per version: data/scores-<version>.db."""

    def __init__(self, path):
        self.path = path
        self.local = threading.local()  # SQLite connections are per thread

    def _conn(self):
        if not hasattr(self.local, "conn"):
            self.local.conn = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, check_same_thread=False)
        return self.local.conn

    def get_many(self, keys):
        """One round trip for all the keys a request needs."""
        if DELAY_S:
            time.sleep(DELAY_S)
        marks = ",".join("?" * len(keys))
        rows = self._conn().execute(f"SELECT k, v FROM scores WHERE k IN ({marks})", list(keys)).fetchall()
        return dict(rows)

    @staticmethod
    def write(path, scores):
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE scores (k TEXT PRIMARY KEY, v REAL) WITHOUT ROWID")
        conn.executemany("INSERT INTO scores VALUES (?, ?)", scores.items())
        conn.commit()
        conn.close()


class DynamoStore:
    """One DynamoDB table; keys are '<version>|<asin>|<creative>', and old versions expire via TTL."""

    def __init__(self, table, version, region=None):
        import boto3
        self.client = boto3.client("dynamodb", region_name=region)
        self.table, self.version = table, version

    def get_many(self, keys):
        if DELAY_S:
            time.sleep(DELAY_S)
        found, pending = {}, [{"k": {"S": f"{self.version}|{k}"}} for k in keys]
        while pending:  # BatchGetItem takes at most 100 keys and may return some unprocessed
            batch, pending = pending[:100], pending[100:]
            resp = self.client.batch_get_item(RequestItems={self.table: {"Keys": batch}})
            for item in resp["Responses"].get(self.table, []):
                found[item["k"]["S"].split("|", 1)[1]] = float(item["v"]["N"])
            pending += resp.get("UnprocessedKeys", {}).get(self.table, {}).get("Keys", [])
        return found

    @staticmethod
    def write(table, version, scores, region=None, ttl_days=3):
        import boto3
        from decimal import Decimal  # DynamoDB numbers go in as Decimal, never float
        expires = int(time.time()) + ttl_days * 86_400
        resource = boto3.resource("dynamodb", region_name=region)
        with resource.Table(table).batch_writer() as batch:
            for k, v in scores.items():
                batch.put_item(Item={"k": f"{version}|{k}", "v": Decimal(str(v)), "expires_at": expires})

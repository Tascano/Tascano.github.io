"""The relevance API: POST an ASIN and its candidate creatives, get a score for each.

    uvicorn service:app --port 8000

Each request walks the layers from the post: Bloom filter (definitely not? answer from memory), the
host's hot-key cache, then ONE batched database read for whatever is left. Every piece belongs to a
snapshot of one data version, and a background thread swaps in a new snapshot when current.json moves.

Environment (all optional):
    DATA_DIR=data        where current.json, the Bloom filter and SQLite files live (laptop)
    BUCKET=...           read current.json and the Bloom filter from S3 instead (AWS)
    CACHE_SIZE=50000     hot-key cache entries per snapshot (0 turns the cache off)
    BLOOM=on             'off' skips the Bloom filter (experiment 1)
    DB_DELAY_MS=0        add latency to every database read (experiment 4)
    POLL_SECONDS=5       how often to look for a new version
"""
import json
import os
import threading
import time
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import store as store_module
from bloom import BloomFilter
from store import DynamoStore, SqliteStore

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
BUCKET = os.environ.get("BUCKET")
CACHE_SIZE = int(os.environ.get("CACHE_SIZE", "50000"))
USE_BLOOM = os.environ.get("BLOOM", "on") != "off"
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "5"))
store_module.DELAY_S = float(os.environ.get("DB_DELAY_MS", "0")) / 1000
NOT_RELEVANT = 0.0


class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.data, self.lock = capacity, OrderedDict(), threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.data:
                return None
            self.data.move_to_end(key)
            return self.data[key]

    def put(self, key, value):
        if not self.capacity:
            return
        with self.lock:
            self.data[key] = value
            self.data.move_to_end(key)
            if len(self.data) > self.capacity:
                self.data.popitem(last=False)


class Snapshot:
    """Everything one data version needs. Requests grab one snapshot and use it to the end."""

    def __init__(self, manifest):
        self.version = manifest["version"]
        bloom_path = DATA_DIR / manifest["bloom"]["path"]
        if BUCKET:
            import boto3
            DATA_DIR.mkdir(exist_ok=True)
            boto3.client("s3").download_file(BUCKET, manifest["bloom"]["path"], str(bloom_path))
        self.bloom = BloomFilter.load(bloom_path, manifest["bloom"]["m"], manifest["bloom"]["k"])
        kind = manifest["store"]["kind"]
        self.store = (SqliteStore(DATA_DIR / manifest["store"]["path"]) if kind == "sqlite"
                      else DynamoStore(manifest["store"]["table"], self.version))
        self.cache = LRUCache(CACHE_SIZE)  # a new version starts with an empty cache: no stale answers


class Metrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.counts = dict(requests=0, lookups=0, bloom_no=0, cache_hits=0, db_reads=0, db_keys=0, swaps=0)
        self.latencies = deque(maxlen=50_000)

    def add(self, **kw):
        with self.lock:
            for k, v in kw.items():
                self.counts[k] += v

    def snapshot(self):
        with self.lock:
            lat = sorted(self.latencies)
            counts = dict(self.counts)
        pct = lambda q: round(lat[int(q * (len(lat) - 1))], 3) if lat else None
        return counts | {"latency_ms": {"p50": pct(0.5), "p99": pct(0.99), "p999": pct(0.999),
                                        "max": round(lat[-1], 3) if lat else None, "window": len(lat)}}


metrics = Metrics()
live = {"snapshot": None}


def read_manifest():
    if BUCKET:
        import boto3
        body = boto3.client("s3").get_object(Bucket=BUCKET, Key="current.json")["Body"].read()
        return json.loads(body)
    return json.loads((DATA_DIR / "current.json").read_text())


def refresh():
    """Load a new snapshot if current.json moved, then swap one reference."""
    manifest = read_manifest()
    current = live["snapshot"]
    if current is None or manifest["version"] != current.version:
        live["snapshot"] = Snapshot(manifest)  # built fully first, then swapped in one assignment
        metrics.add(swaps=1)
        print(f"serving version {manifest['version']} ({manifest['rows']:,} rows)", flush=True)


def poll_forever():
    while True:
        try:
            refresh()
        except Exception as err:  # no data yet, or a publish in flight: keep the old snapshot
            print(f"refresh skipped: {err}", flush=True)
        time.sleep(POLL_SECONDS)


@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=poll_forever, daemon=True).start()
    yield


app = FastAPI(title="Relevance API lab", lifespan=lifespan)


class RelevanceRequest(BaseModel):
    asin: str
    creatives: list[str]


@app.post("/relevance")
def relevance(req: RelevanceRequest):
    t = time.perf_counter()
    snap = live["snapshot"]  # one version for the whole request
    if snap is None:
        raise HTTPException(503, "no data version loaded yet")
    scores, missing = {}, []
    bloom_no = cache_hits = 0
    for cr in req.creatives:
        key = f"{req.asin}|{cr}"
        if USE_BLOOM and not snap.bloom.might_contain(key):
            scores[cr] = NOT_RELEVANT  # 1. definitely not in the dataset: no I/O
            bloom_no += 1
            continue
        hit = snap.cache.get(key)
        if hit is not None:
            scores[cr] = hit  # 2. hot key: memory only
            cache_hits += 1
        else:
            missing.append(key)
    if missing:
        found = snap.store.get_many(missing)  # 3. one batched read for everything left
        for key in missing:
            score = found.get(key, NOT_RELEVANT)
            snap.cache.put(key, score)  # negative results are cached too
            scores[key.split("|", 1)[1]] = score
    metrics.add(requests=1, lookups=len(req.creatives), bloom_no=bloom_no, cache_hits=cache_hits,
                db_reads=1 if missing else 0, db_keys=len(missing))
    metrics.latencies.append((time.perf_counter() - t) * 1000)
    return {"version": snap.version, "scores": {cr: scores[cr] for cr in req.creatives}}  # request order


@app.get("/healthz")
def healthz():
    if live["snapshot"] is None:
        raise HTTPException(503, "no data version loaded yet")
    return {"ok": True, "version": live["snapshot"].version}


@app.get("/metrics")
def get_metrics():
    snap = live["snapshot"]
    return {"version": snap and snap.version, "bloom": USE_BLOOM, "cache_size": CACHE_SIZE} | metrics.snapshot()


@app.post("/admin/reset-metrics")
def reset_metrics():
    global metrics
    metrics = Metrics()
    return {"ok": True}

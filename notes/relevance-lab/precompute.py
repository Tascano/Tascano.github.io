"""The daily batch: build one complete, validated version of the relevance data, then publish it.

    python precompute.py --day 2026-10-30                      # laptop: SQLite + files in data/
    python precompute.py --day 2026-10-30 --table T --bucket B # AWS: DynamoDB + S3

Steps: similarities (ASIN-to-ASIN, creative-to-creative) -> (ASIN, creative) scores above a threshold ->
validate against the live version -> write the scores and a Bloom filter for this version -> point
current.json at it, last, so readers switch versions in one step.
"""
import argparse
import datetime as dt
import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np

from bloom import BloomFilter
from data import make_world
from store import DynamoStore, SqliteStore


def unit(m):
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def score_pairs(day_number, threshold):
    asins, asin_vec, creatives, creative_vec, creative_asins, _ = make_world(day=day_number)
    index = {a: i for i, a in enumerate(asins)}
    A = unit(asin_vec)
    scores, by_creative = {}, {}
    # Mapped creatives: relevance to a page ASIN = best ASIN-to-ASIN similarity over the ASINs they advertise.
    for cr in creatives:
        if creative_asins[cr]:
            cols = A[[index[a] for a in creative_asins[cr]]]
            by_creative[cr] = (A @ cols.T).max(axis=1)
    # Brand-new creatives (nothing mapped): borrow from the most similar mapped creative.
    mapped = [cr for cr in creatives if creative_asins[cr]]
    C = unit(creative_vec)
    cpos = {cr: i for i, cr in enumerate(creatives)}
    M = C[[cpos[cr] for cr in mapped]]
    for cr in creatives:
        if not creative_asins[cr]:
            sims = M @ C[cpos[cr]]
            best = int(sims.argmax())
            by_creative[cr] = sims[best] * by_creative[mapped[best]]
    for cr, col in by_creative.items():
        for i in np.nonzero(col >= threshold)[0]:
            scores[f"{asins[i]}|{cr}"] = round(float(col[i]), 3)
    return scores


def validate(scores, previous_rows, max_drift=0.2):
    if not scores:
        raise SystemExit("refusing to publish: empty dataset")
    if previous_rows:
        drift = abs(len(scores) - previous_rows) / previous_rows
        if drift > max_drift:
            raise SystemExit(f"refusing to publish: row count moved {drift:.0%} "
                             f"({previous_rows:,} -> {len(scores):,}); rerun with --force if that is expected")


def atomic_write_json(path, payload):
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)  # readers see the old file or the new one, never half of each


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day", default=dt.date.today().isoformat(), help="the version to build, YYYY-MM-DD")
    ap.add_argument("--data", default="data", help="local folder for files (default: data)")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--table", help="DynamoDB table (AWS mode)")
    ap.add_argument("--bucket", help="S3 bucket for the Bloom filter and current.json (AWS mode)")
    ap.add_argument("--region", default=os.environ.get("AWS_REGION"))
    ap.add_argument("--force", action="store_true", help="publish even if validation would block it")
    args = ap.parse_args()
    aws = bool(args.table and args.bucket)
    data = Path(args.data)
    data.mkdir(exist_ok=True)
    version = args.day
    day_number = dt.date.fromisoformat(version).toordinal()

    t = time.perf_counter()
    scores = score_pairs(day_number, args.threshold)
    print(f"[{version}] scored pairs: {len(scores):,} relevant (ASIN, creative) pairs "
          f"in {time.perf_counter() - t:.1f}s")

    previous = None
    if aws:
        import boto3
        s3 = boto3.client("s3", region_name=args.region)
        try:
            previous = json.loads(s3.get_object(Bucket=args.bucket, Key="current.json")["Body"].read())
        except s3.exceptions.NoSuchKey:
            pass
    elif (data / "current.json").exists():
        previous = json.loads((data / "current.json").read_text())
    if previous and previous["version"] == version and not args.force:
        raise SystemExit(f"version {version} is already live; pick another --day or use --force")
    if not args.force:
        validate(scores, previous and previous["rows"])
    print(f"[{version}] validation passed"
          + (f" (live version {previous['version']} has {previous['rows']:,} rows)" if previous else " (first version)"))

    bloom = BloomFilter(len(scores), 0.01)
    for key in scores:
        bloom.add(key)
    bloom_file = data / f"bloom-{version}.bin"
    params = bloom.save(bloom_file)
    print(f"[{version}] Bloom filter: {params['m']:,} bits ({bloom_file.stat().st_size / 1024:,.0f} KiB), k={params['k']}")

    t = time.perf_counter()
    if aws:
        DynamoStore.write(args.table, version, scores, region=args.region)
        s3.upload_file(str(bloom_file), args.bucket, f"bloom-{version}.bin")
        store = {"kind": "dynamodb", "table": args.table}
    else:
        db_file = data / f"scores-{version}.db"
        db_file.unlink(missing_ok=True)
        SqliteStore.write(db_file, scores)
        store = {"kind": "sqlite", "path": db_file.name}
    print(f"[{version}] wrote {len(scores):,} rows to {store['kind']} in {time.perf_counter() - t:.1f}s")

    manifest = {"version": version, "rows": len(scores), "store": store,
                "bloom": {"path": bloom_file.name, **params}}
    if aws:  # an S3 PUT replaces the whole object at once, so this is the atomic switch
        s3.put_object(Bucket=args.bucket, Key="current.json", Body=json.dumps(manifest).encode())
    else:
        atomic_write_json(data / "current.json", manifest)
    print(f"[{version}] published: current.json now points at version {version}")


if __name__ == "__main__":
    main()

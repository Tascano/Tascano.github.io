"""A small load generator: concurrent clients, skewed popularity, 5 candidate creatives per request.

    python loadtest.py --url http://localhost:8000 --seconds 20 --processes 2 --concurrency 32

Like a real ad server, about half of each request's candidates come from the product's own category;
the rest are long shots. It reports throughput and latency as the CLIENT sees them, then asks the
service what each layer did (/metrics). One process tops out at a few thousand requests a second,
so --processes runs a small fleet of generators; to push a real fleet, run it from several machines.
"""
import argparse
import asyncio
import datetime as dt
import multiprocessing as mp
import random
import time

import httpx

from data import make_world


def skewed(items, s=1.0, seed=1):
    """Zipf popularity: rank r gets weight 1/r^s, ranks shuffled so IDs don't give it away."""
    order = random.Random(seed).sample(items, len(items))
    return order, [1 / (r ** s) for r in range(1, len(order) + 1)]


def build_traffic(day, targeted):
    asins, _, creatives, _, _, category = make_world(day=dt.date.fromisoformat(day).toordinal())
    by_category = {}
    for cr in creatives:
        by_category.setdefault(category[cr], []).append(cr)
    return skewed(asins), skewed(creatives, seed=2), by_category, category, targeted


async def run(url, seconds, concurrency, per_request, traffic, seed):
    (a_items, a_w), (c_items, c_w), by_category, category, targeted = traffic
    latencies, errors = [], 0
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)

    async def worker(rng):
        nonlocal errors
        while time.perf_counter() < deadline:
            asin = rng.choices(a_items, a_w)[0]
            pool = by_category.get(category[asin], c_items)
            crs = [rng.choice(pool) if rng.random() < targeted else rng.choices(c_items, c_w)[0]
                   for _ in range(per_request)]
            t = time.perf_counter()
            try:
                r = await client.post(f"{url}/relevance", json={"asin": asin, "creatives": crs})
                r.raise_for_status()
                latencies.append((time.perf_counter() - t) * 1000)
            except httpx.HTTPError:
                errors += 1

    async with httpx.AsyncClient(limits=limits, timeout=10) as client:
        deadline = time.perf_counter() + seconds
        await asyncio.gather(*(worker(random.Random(seed * 1000 + i)) for i in range(concurrency)))
    return latencies, errors


def generator(args_tuple):
    return asyncio.run(run(*args_tuple))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--processes", type=int, default=2, help="generator processes (a tiny load-test fleet)")
    ap.add_argument("--concurrency", type=int, default=32, help="concurrent requests per process")
    ap.add_argument("--creatives", type=int, default=5, help="candidate creatives per request")
    ap.add_argument("--targeted", type=float, default=0.5, help="share of candidates from the product's category")
    ap.add_argument("--reset", action="store_true", help="reset the service's counters first")
    args = ap.parse_args()

    server = httpx.get(f"{args.url}/metrics").json()
    traffic = build_traffic(server["version"], args.targeted)
    if args.reset:
        httpx.post(f"{args.url}/admin/reset-metrics")
    start = time.perf_counter()
    jobs = [(args.url, args.seconds, args.concurrency, args.creatives, traffic, p) for p in range(args.processes)]
    with mp.Pool(args.processes) as pool:
        results = pool.map(generator, jobs)
    elapsed = time.perf_counter() - start
    latencies = sorted(ms for lat, _ in results for ms in lat)
    errors = sum(e for _, e in results)
    c = httpx.get(f"{args.url}/metrics").json()

    pct = lambda q: latencies[int(q * (len(latencies) - 1))] if latencies else float("nan")
    rps, mean_s = len(latencies) / elapsed, sum(latencies) / max(len(latencies), 1) / 1000
    print(f"requests: {len(latencies):,} ok, {errors:,} errors in {elapsed:.1f}s -> {rps:,.0f} req/s")
    print(f"client latency ms: p50 {pct(0.5):.1f}  p99 {pct(0.99):.1f}  max {pct(1.0):.1f}")
    print(f"Little's law: {rps:,.0f} req/s x {mean_s:.4f} s = {rps * mean_s:.0f} in flight "
          f"(you ran {args.processes * args.concurrency})")
    if c["lookups"]:
        print(f"server [{c['version']}] {c['lookups']:,} lookups: Bloom said no {c['bloom_no'] / c['lookups']:.0%}, "
              f"cache hits {c['cache_hits'] / c['lookups']:.0%}, read from db {c['db_keys'] / c['lookups']:.0%} "
              f"in {c['db_reads']:,} batched reads")
    print(f"server latency ms: p50 {c['latency_ms']['p50']}  p99 {c['latency_ms']['p99']}  max {c['latency_ms']['max']}")


if __name__ == "__main__":
    main()

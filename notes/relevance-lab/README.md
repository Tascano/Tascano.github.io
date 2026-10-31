# Relevance API lab

A small, runnable version of the system in
[A Million Questions a Second](https://tascano.github.io/notes/scaling-ad-relevance-apis.html):
precomputed (ASIN, creative) relevance, a Bloom filter, a hot-key cache, versioned publishing,
a load test, a garbage-collector experiment, and the same service on AWS.

**Step-by-step guide:** https://tascano.github.io/notes/relevance-lab.html

| File | What it is |
|---|---|
| `data.py` | A synthetic world of ASINs (in categories) and creatives that advertise them |
| `precompute.py` | The daily batch: similarities → (ASIN, creative) scores → validate → publish a version |
| `bloom.py` | The Bloom filter from the post, plus save and load |
| `store.py` | Where scores live: SQLite on a laptop, DynamoDB on AWS (versions side by side) |
| `service.py` | The API (FastAPI): Bloom filter → cache → one batched read, swapping versions live |
| `loadtest.py` | A load generator with skewed traffic; reports client and server views |
| `GcLab.java` | A JVM garbage-collector experiment (Java 21) |
| `aws/stack.yaml` | CloudFormation: DynamoDB, S3, load balancer, Auto Scaling group, load generator |
| `test_lab.py` | Checks for the laptop path and, with moto, the AWS path |

Quick start (macOS/Linux):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python precompute.py --day 2026-10-30
uvicorn service:app --port 8000          # then, in another terminal:
python loadtest.py --seconds 12 --reset
```

The AWS stack creates billable resources. Delete it when you are done (see the guide).

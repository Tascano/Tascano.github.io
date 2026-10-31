"""A synthetic world: products (ASINs) in categories, and creatives that advertise them.

Same seed = same world, so everyone running the lab gets the same numbers. `day` changes
the creatives a little, the way a new day's DSP feeds would.
"""
import numpy as np


def make_world(day=0, n_asins=10_000, n_creatives=1_000, n_categories=50, dim=32, seed=7):
    rng = np.random.default_rng(seed)
    centroids = rng.standard_normal((n_categories, dim))
    asin_category = rng.integers(0, n_categories, n_asins)
    asin_vec = centroids[asin_category] + 0.35 * rng.standard_normal((n_asins, dim))
    asins = [f"B0{i:08d}" for i in range(n_asins)]

    day_rng = np.random.default_rng(seed * 1_000 + day)
    creatives = [f"cr-{i}" for i in range(n_creatives)]
    creative_asins, creative_vec = {}, np.zeros((n_creatives, dim))
    category = {a: int(c) for a, c in zip(asins, asin_category)}
    for i, cr in enumerate(creatives):
        if day_rng.random() < 0.1:  # a brand-new creative: no product mapped yet
            creative_asins[cr] = []
            category[cr] = int(day_rng.integers(0, n_categories))
            creative_vec[i] = centroids[category[cr]] + 0.35 * day_rng.standard_normal(dim)
        else:
            picks = day_rng.choice(n_asins, size=day_rng.integers(1, 3), replace=False)
            creative_asins[cr] = [asins[j] for j in picks]
            category[cr] = category[asins[picks[0]]]
            creative_vec[i] = asin_vec[picks].mean(axis=0)
    return asins, asin_vec, creatives, creative_vec, creative_asins, category

import hashlib
import math

class BloomFilter:
    """A set that can say 'definitely not here' with certainty."""

    def __init__(self, expected_items, false_positive_rate):
        n, p = expected_items, false_positive_rate
        self.m = math.ceil(-n * math.log(p) / math.log(2) ** 2)  # bits
        self.k = max(1, round(self.m / n * math.log(2)))  # hash count
        self.bits = bytearray((self.m + 7) // 8)

    def _positions(self, key):
        d = hashlib.blake2b(key.encode(), digest_size=16).digest()
        h1 = int.from_bytes(d[:8], "little")
        h2 = int.from_bytes(d[8:], "little") | 1
        # k positions from two hashes (Kirsch-Mitzenmacher)
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, key):
        for p in self._positions(key):
            self.bits[p >> 3] |= 1 << (p & 7)

    def might_contain(self, key):
        return all(self.bits[p >> 3] >> (p & 7) & 1
                   for p in self._positions(key))

    # Saving and loading, so the batch can publish a filter and every host can load it.
    def save(self, path):
        with open(path, "wb") as f:
            f.write(self.bits)
        return {"m": self.m, "k": self.k}

    @classmethod
    def load(cls, path, m, k):
        bf = cls.__new__(cls)
        bf.m, bf.k = m, k
        with open(path, "rb") as f:
            bf.bits = bytearray(f.read())
        return bf

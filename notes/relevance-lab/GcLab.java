// A garbage-collector experiment: a pretend relevance service handles requests on a fixed schedule,
// makes garbage on every request, and keeps a big read-only table in memory. Latency is measured from
// when each request was SUPPOSED to start, so a GC pause shows up in every request it delays.
//
// It also keeps a hot-key cache that churns (new entries in, old ones evicted), which is what slowly
// fills the old generation in a real service.
//
//   java -Xms2g -Xmx2g -XX:+AlwaysPreTouch -XX:+UseParallelGC GcLab.java objects   # millions of small objects
//   java -Xms2g -Xmx2g -XX:+AlwaysPreTouch -XX:+UseG1GC       GcLab.java objects
//   java -Xms2g -Xmx2g -XX:+AlwaysPreTouch -XX:+UseZGC -XX:+ZGenerational GcLab.java objects   (JDK 21+)
//   java -Xms2g -Xmx2g -XX:+AlwaysPreTouch -XX:+UseParallelGC GcLab.java array     # the table as one flat array
//
//   java -Xms2g -Xmx2g -XX:+AlwaysPreTouch -XX:+UseParallelGC GcLab.java array 100000  # ...and a capped cache
//
// Arguments: layout (objects|array), cache entries (default 1,000,000), requests per second (default 20,000).
// Add -Xlog:gc to see every collection.

import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

public class GcLab {
    static final int KEYS = 3_000_000;            // the precomputed table
    static final int SECONDS = 30, WARMUP_SECONDS = 5;
    static int cacheEntries = 1_000_000;          // the hot-key cache, which churns

    // An LRU cache: every insert past capacity evicts the oldest entry, which becomes old-generation garbage.
    static final Map<String, Double> cache = new LinkedHashMap<>(1 << 16, 0.75f, true) {
        protected boolean removeEldestEntry(Map.Entry<String, Double> eldest) { return size() > cacheEntries; }
    };

    public static void main(String[] args) throws Exception {
        String layout = args.length > 0 ? args[0] : "objects";
        cacheEntries = args.length > 1 ? Integer.parseInt(args[1]) : 1_000_000;
        int rate = args.length > 2 ? Integer.parseInt(args[2]) : 20_000;  // requests per second

        // The read-only table, held two ways.
        Map<Long, Double> asObjects = null;   // ~3M boxed keys and values: many small objects for the GC to walk
        double[] asArray = null;              // one object, whatever its size
        if (layout.equals("objects")) {
            asObjects = new HashMap<>(KEYS * 2);
            for (long k = 0; k < KEYS; k++) asObjects.put(k, k * 0.5);
        } else {
            asArray = new double[KEYS];
            for (int k = 0; k < KEYS; k++) asArray[k] = k * 0.5;
        }
        System.gc();

        double sink = 0;
        long interval = 1_000_000_000L / rate;
        long warmStart = System.nanoTime();                              // warm-up: let the JIT compile, not measured
        for (int i = 0; i < rate * WARMUP_SECONDS; i++) {
            long scheduled = warmStart + i * interval;
            while (System.nanoTime() < scheduled) Thread.onSpinWait();
            sink += handleRequest(asObjects, asArray);
        }

        long[] latencyNanos = new long[rate * SECONDS];
        long gcCountBefore = gcCount(), gcTimeBefore = gcTimeMs();
        long start = System.nanoTime();
        for (int i = 0; i < latencyNanos.length; i++) {
            long scheduled = start + i * interval;
            while (System.nanoTime() < scheduled) Thread.onSpinWait();   // wait for this request's turn
            sink += handleRequest(asObjects, asArray);
            latencyNanos[i] = System.nanoTime() - scheduled;             // includes any pause it waited through
        }
        Arrays.sort(latencyNanos);
        System.out.printf("%s layout, cache %,d entries, %,d req/s for %ds%n", layout, cacheEntries, rate, SECONDS);
        System.out.printf("latency ms: p50 %.3f  p99 %.3f  p99.9 %.3f  max %.1f%n",
                pct(latencyNanos, 0.50), pct(latencyNanos, 0.99), pct(latencyNanos, 0.999),
                latencyNanos[latencyNanos.length - 1] / 1e6);
        System.out.printf("collections: %d, stop-the-world pause time %d ms  (checksum %.0f)%n",
                gcCount() - gcCountBefore, gcTimeMs() - gcTimeBefore, sink % 1000);
    }

    // Each request makes garbage the way real request handling does: boxed numbers, strings, lists.
    static double handleRequest(Map<Long, Double> asObjects, double[] asArray) {
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        List<String> scratch = new ArrayList<>();
        double total = 0;
        for (int c = 0; c < 5; c++) {                      // five candidate creatives
            long key = rnd.nextLong(KEYS);
            String cacheKey = "B0" + key + "|cr-" + c;      // a key string
            scratch.add(cacheKey);
            double score = asObjects != null ? asObjects.get(key) : asArray[(int) key];
            cache.put(cacheKey, score);                     // the hot-key cache churns
            total += score;
        }
        byte[] response = new byte[2_048];                 // a response buffer, also thrown away
        response[0] = (byte) scratch.size();
        return total + response[0];
    }

    static double pct(long[] sorted, double q) {
        return sorted[(int) (q * (sorted.length - 1))] / 1e6;
    }

    // ZGC reports its concurrent cycles and its pauses separately; count only what stops the application.
    static List<GarbageCollectorMXBean> pausingCollectors() {
        List<GarbageCollectorMXBean> all = ManagementFactory.getGarbageCollectorMXBeans();
        List<GarbageCollectorMXBean> pauses = all.stream().filter(b -> b.getName().contains("Pauses")).toList();
        return pauses.isEmpty() ? all : pauses;
    }

    static long gcCount() {
        return pausingCollectors().stream().mapToLong(GarbageCollectorMXBean::getCollectionCount).sum();
    }

    static long gcTimeMs() {
        return pausingCollectors().stream().mapToLong(GarbageCollectorMXBean::getCollectionTime).sum();
    }
}

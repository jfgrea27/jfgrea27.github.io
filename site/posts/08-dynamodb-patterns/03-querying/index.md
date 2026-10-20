---
title: "03 - Querying"
author: "James"
date: "2026-10-20"
summary: "Reading data efficiently once the keys are designed: Scan vs Query, filters, pagination, GSI projections and batch retries."
tags: ["dynamodb", "aws", "databases", "querying"]
draft: false
hideHeader: true
---

Once the keys are designed, the next question is how to read the data efficiently. The one fact to hold on to is that DynamoDB charges for what it **reads**, not what it **returns**. Most of this page is about making those two numbers the same. The rest is about handling the API's paging and batching behaviour correctly.

In short: **query, don't scan**. `Query` reads one partition, while `Scan` reads the whole table, so parallel Scan is for batch jobs only. **Filters don't save money**, because a `FilterExpression` runs after the read, so selectivity belongs in the key. **Everything is paged**: responses stop at 1 MB or at `Limit`, so we follow `LastEvaluatedKey` and expose it to API clients as an opaque cursor. **Index projections are a choice**: `KEYS_ONLY`, `INCLUDE` or `ALL` trades index storage and write cost against follow-up reads. And **batch calls can partially fail**: `BatchWriteItem` and `BatchGetItem` return unprocessed items, which we must retry with backoff.

| # | Pattern | What we'll learn |
|---|---|---|
| 12 | [Avoid Scan (parallel Scan for batch jobs)](#12--avoid-scan-use-parallel-scan-for-batch-jobs) | The cost difference between Scan and Query; segmented parallel scans |
| 13 | [Filter expressions don't reduce cost](#13--filter-expressions-dont-reduce-cost) | Measuring read units for filters vs key conditions; the `Limit` + filter trap |
| 14 | [Pagination with cursors](#14--pagination-with-cursors) | `LastEvaluatedKey`, opaque API cursors, boto3 paginators |
| 15 | [GSI projections](#15--gsi-projections) | What each projection type returns and costs |
| 16 | [Batch operations with retries](#16--batch-operations-with-retries) | Chunking to 25/100, retrying unprocessed items, `batch_writer()` |

## 12 · Avoid Scan (use parallel Scan for batch jobs)

**Code:** [12-avoid-scan-parallel-scan.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/03-querying/12-avoid-scan-parallel-scan/12-avoid-scan-parallel-scan.py) · run with `just run 12`

### Problem

`Scan` reads **every item in the table**, and only then applies any filter. Its cost and latency grow with the size of the table, not with the size of the result. In the script below, finding one user's 5 orders with a Scan reads 1,000 items. A Query reads 5.

### Pattern

**In request paths, we use `Query` or `GetItem` only.** If an access pattern seems to need a Scan, that's a sign we're missing a key or a GSI that serves it (see [access-pattern-first design](../02-modelling/#02--access-pattern-first-design) and [GSI overloading](../02-modelling/#09--gsi-overloading)).

**For batch jobs** (migrations, backfills, re-indexing, one-off exports), we use a **parallel scan**:

```python
table.scan(Segment=i, TotalSegments=N)  # one worker per segment
```

Each worker scans a disjoint slice of the table and pages through it with `LastEvaluatedKey`.

### In practice

The script writes 200 users with 5 orders each (1,000 items), then looks for `USER#42`'s orders two ways, and finally runs a 4-segment parallel scan over the whole table:

```python
# Bad: find one user's orders by scanning the whole table.
resp = table.scan(FilterExpression=Attr("PK").eq("USER#42"), ReturnConsumedCapacity="TOTAL")

# Good: Query reads only that partition.
resp = table.query(KeyConditionExpression=Key("PK").eq("USER#42"), ReturnConsumedCapacity="TOTAL")

# Batch job (export, migration, backfill): parallel scan split into segments.
TOTAL_SEGMENTS = 4

def scan_segment(segment):
    count, kwargs = 0, {"Segment": segment, "TotalSegments": TOTAL_SEGMENTS}
    while True:
        page = table.scan(**kwargs)
        count += page["Count"]
        if "LastEvaluatedKey" not in page:
            return count
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]

with ThreadPoolExecutor(max_workers=TOTAL_SEGMENTS) as pool:
    per_segment = list(pool.map(scan_segment, range(TOTAL_SEGMENTS)))
```

```text
>>> Scan p12-avoid-scan
    filter:     PK = 'USER#42'

=== Scan + filter for USER#42 ===
{
  "returned": 5,
  "examined": 1000,
  "consumed": {
    "TableName": "p12-avoid-scan",
    "CapacityUnits": 3.5
  }
}

>>> Query p12-avoid-scan
    key:        PK = 'USER#42'

=== Query for USER#42 ===
{
  "returned": 5,
  "examined": 5,
  "consumed": {
    "TableName": "p12-avoid-scan",
    "CapacityUnits": 0.5
  }
}

>>> Scan p12-avoid-scan
    Segment:    0
    TotalSegments: 4

>>> Scan p12-avoid-scan
    Segment:    1
    TotalSegments: 4

>>> Scan p12-avoid-scan
    Segment:    2
    TotalSegments: 4
    ... (+1 more Scan calls not shown)

=== Parallel scan: items per segment ===
{
  "segments": [
    210,
    245,
    275,
    270
  ],
  "total": 1000
}
```

Both requests return the same 5 items, but the Scan examined 1,000 of them and consumed 7x the capacity. That gap only widens as the table grows. The parallel scan splits the table into 4 roughly equal, non-overlapping segments that together cover all 1,000 items exactly once.

### Why

- A Query costs about the same on a 1 GB table as on a 10 TB one. A Scan does not.
- A big Scan can use up all of the table's capacity and throttle production traffic.
- A parallel scan finishes a full-table job N times faster.

### Trade-offs

- A parallel scan also uses capacity N times faster. We should rate-limit it, run it off-peak, or use on-demand mode.
- For analytics or full exports, **Export to S3** costs no table capacity at all (see [analytics outside DynamoDB](../08-operations/#41--analytics-outside-dynamodb)).

### Gotchas

- Each Scan page returns at most 1 MB, so we always loop on `LastEvaluatedKey` (see [pagination](#14--pagination-with-cursors)).
- A `FilterExpression` doesn't reduce what we pay for (see [the next pattern](#13--filter-expressions-dont-reduce-cost)).
- A Scan is not a point-in-time snapshot. Items written while it runs may or may not appear.
- Small, bounded tables (say, a config table with 50 rows) are fine to scan.

## 13 · Filter expressions don't reduce cost

**Code:** [13-filter-expressions-cost.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/03-querying/13-filter-expressions-cost/13-filter-expressions-cost.py) · run with `just run 13`

### Problem

`FilterExpression` looks like a SQL `WHERE`, but it runs **after** the read. We pay for every item the key condition matched, even the ones the filter then throws away. In the script, fetching "open orders" with a filter reads 1,000 items (~127 RCUs) to return 10.

### Pattern

Put the selectivity in the **key**, so the key condition only touches the items we actually want. Here each order is also written under a status-prefixed sort key:

| PK            | SK                              |
|---------------|---------------------------------|
| `CUSTOMER#c1` | `ORDER#0000`                    |
| `CUSTOMER#c1` | `STATUS#OPEN#ORDER#0000`        |
| `CUSTOMER#c1` | `STATUS#SHIPPED#ORDER#0001`     |

`Query(PK=CUSTOMER#c1, SK begins_with STATUS#OPEN#)` then reads only the 10 open orders (~1.5 RCUs).

There are other ways to achieve the same thing:

- [Composite sort keys](../02-modelling/#05--composite-hierarchical-sort-keys).
- A GSI keyed on the attribute (see [GSI overloading](../02-modelling/#09--gsi-overloading)).
- A [sparse index](../02-modelling/#10--sparse-index) that only holds the matching items.

### In practice

The script writes 1,000 orders of ~1 KB each for one customer, only 10 of them `OPEN`, and a second copy of each keyed by status. A small `query_all` helper pages through results and sums up `Count`, `ScannedCount` and consumed capacity:

```python
show(
    "FilterExpression status=OPEN (reads everything, then discards)",
    query_all(
        KeyConditionExpression=Key("PK").eq("CUSTOMER#c1") & Key("SK").begins_with("ORDER#"),
        FilterExpression=Attr("status").eq("OPEN"),
    ),
)
show(
    "KeyCondition SK begins_with STATUS#OPEN# (reads only matches)",
    query_all(KeyConditionExpression=Key("PK").eq("CUSTOMER#c1") & Key("SK").begins_with("STATUS#OPEN#")),
)

# Limit applies BEFORE the filter: you can get 0 results and still have more pages.
page = table.query(
    KeyConditionExpression=Key("PK").eq("CUSTOMER#c1") & Key("SK").begins_with("ORDER#"),
    FilterExpression=Attr("status").eq("OPEN"),
    Limit=50,
    ExclusiveStartKey={"PK": "CUSTOMER#c1", "SK": "ORDER#0001"},
)
```

```text
>>> Query p13-filter-cost
    key:        (PK = 'CUSTOMER#c1' AND begins_with(SK, 'ORDER#'))
    filter:     status = 'OPEN'

=== FilterExpression status=OPEN (reads everything, then discards) ===
{
  "returned": 10,
  "read": 1000,
  "RCUs": 127.5
}

>>> Query p13-filter-cost
    key:        (PK = 'CUSTOMER#c1' AND begins_with(SK, 'STATUS#OPEN#'))

=== KeyCondition SK begins_with STATUS#OPEN# (reads only matches) ===
{
  "returned": 10,
  "read": 10,
  "RCUs": 1.5
}

>>> Query p13-filter-cost
    key:        (PK = 'CUSTOMER#c1' AND begins_with(SK, 'ORDER#'))
    filter:     status = 'OPEN'
    Limit:      50
    startKey:   {PK: 'CUSTOMER#c1', SK: 'ORDER#0001'}

=== Limit=50 + filter ===
{
  "returned": 0,
  "read": 50,
  "more": true
}
```

The same 10 orders cost 127.5 RCUs with a filter and 1.5 RCUs with the selectivity in the key, an 85x difference. The last request shows the `Limit` trap: DynamoDB read 50 items, the filter dropped all of them, and we got back an empty page that still says there's more to read.

### Why

Cost and latency follow the items **read**, not the items returned.

### Trade-offs

- Extra keys or GSIs cost writes and storage, and must be kept in sync when the status changes.
- Filters are **fine** when they drop only a small share of what we read, e.g. hiding [TTL-expired](../06-lifecycle-and-events/#30--ttl-for-expiry) or [soft-deleted](../06-lifecycle-and-events/#33--soft-delete--archival) items.

### Gotchas

- **`Limit` applies before the filter.** A page can come back with 0 items and still have a `LastEvaluatedKey`, so we keep paging until it's gone (see [pagination](#14--pagination-with-cursors)).
- The 1 MB page size is also measured before the filter.
- Comparing `ScannedCount` with `Count` in the response tells us how much a filter wasted. It's worth logging.

## 14 · Pagination with cursors

**Code:** [14-pagination-cursors.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/03-querying/14-pagination-cursors/14-pagination-cursors.py) · run with `just run 14`

### Problem

A Query or Scan returns at most 1 MB (or `Limit` items) per call. DynamoDB has no `OFFSET`, so "page 7" can't be computed. We can only continue from where the last page stopped.

### Pattern

- Each response includes `LastEvaluatedKey` when there's more data. We pass it back as `ExclusiveStartKey` on the next call.
- For APIs, we **encode it as an opaque cursor** (base64 JSON, ideally signed or encrypted) and return it as `nextCursor`.
- No `LastEvaluatedKey` means we've reached the last page.

```python
resp = table.query(KeyConditionExpression=..., Limit=10, ExclusiveStartKey=start)
next_cursor = encode(resp.get("LastEvaluatedKey"))
```

In batch code, boto3 paginators (`client.get_paginator("query")`) run this loop for us.

### In practice

The script writes 23 posts to one feed and pages through them 10 at a time, the way an API handler would: cursor in, items and next cursor out. It then does the same with a boto3 paginator:

```python
def encode_cursor(last_key):
    return base64.urlsafe_b64encode(json.dumps(last_key).encode()).decode() if last_key else None


def list_posts(cursor=None, page_size=10):
    """What an API handler looks like: cursor in, items + next cursor out."""
    kwargs = {"KeyConditionExpression": Key("PK").eq("FEED#news"), "Limit": page_size}
    start = decode_cursor(cursor)
    if start:
        # In real code: check the decoded key belongs to this PK (don't trust clients).
        if start.get("PK") != "FEED#news":
            raise ValueError("invalid cursor")
        kwargs["ExclusiveStartKey"] = start
    resp = table.query(**kwargs)
    return {
        "items": [i["title"] for i in resp["Items"]],
        "nextCursor": encode_cursor(resp.get("LastEvaluatedKey")),
    }

# boto3 paginators do the LastEvaluatedKey loop for you.
paginator = table.meta.client.get_paginator("query")
pages = paginator.paginate(
    TableName=table.name,
    KeyConditionExpression="PK = :pk",
    ExpressionAttributeValues={":pk": "FEED#news"},
    PaginationConfig={"PageSize": 10},
)
```

```text
>>> Query p14-pagination
    key:        PK = 'FEED#news'
    Limit:      10

=== Page 1 ===
{
  "items": [
    "Post 0",
    "Post 1",
    ...
    "Post 9"
  ],
  "nextCursor": "eyJTSyI6ICJQT1NUIzAwOSIsICJQSyI6ICJGRUVEI25ld3MifQ=="
}

>>> Query p14-pagination
    key:        PK = 'FEED#news'
    Limit:      10
    startKey:   {SK: 'POST#009', PK: 'FEED#news'}

=== Page 2 ===
{
  "items": [
    "Post 10",
    "Post 11",
    ...
    "Post 19"
  ],
  "nextCursor": "eyJTSyI6ICJQT1NUIzAxOSIsICJQSyI6ICJGRUVEI25ld3MifQ=="
}

>>> Query p14-pagination
    key:        PK = 'FEED#news'
    Limit:      10
    startKey:   {SK: 'POST#019', PK: 'FEED#news'}

=== Page 3 ===
{
  "items": [
    "Post 20",
    "Post 21",
    "Post 22"
  ],
  "nextCursor": null
}

=== Paginator page sizes ===
[
  10,
  10,
  3
]
```

Each `nextCursor` is just the base64 of the last key on the page (`{"SK": "POST#009", "PK": "FEED#news"}`), and we can see it come back as `startKey` on the next request. The third page has no `LastEvaluatedKey`, so `nextCursor` is `null`. The paginator makes the same three requests (not repeated above) and gives the same 10/10/3 split.

### Why

- **Constant cost per page.** Page 1,000 costs the same as page 1. Offset pagination gets slower the deeper we go.
- **Stable under inserts.** New items don't shift or duplicate the next page.

### Trade-offs

- We can only go forward, and we can't jump to page N. (We can go backward by reversing `ScanIndexForward` from a cursor.) "Load more" or infinite-scroll UIs fit this well.
- There's **no total count** without reading everything. If we need one, we keep a separate [atomic counter](../05-consistency/#24--atomic-counters).

### Gotchas

- The cursor contains key values, which may include IDs or emails. **We shouldn't trust it from clients.** Check it belongs to the partition being queried (as `list_posts` does), and consider encrypting it.
- On a GSI, `LastEvaluatedKey` includes both the index keys and the table keys. Pass it back unchanged.
- With a `FilterExpression`, pages can be short or empty while more data remains (see [the previous pattern](#13--filter-expressions-dont-reduce-cost)).
- For newest-first feeds, combine [sortable keys](../02-modelling/#06--sortable-ids-latest-first) with `ScanIndexForward=False`.

## 15 · GSI projections

**Code:** [15-gsi-projections.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/03-querying/15-gsi-projections/15-gsi-projections.py) · run with `just run 15`

### Problem

A GSI is a separate copy of our data, and the projection decides which attributes get copied into it. Copying too much costs storage, plus write capacity on every update. Copying too little forces an extra read for each result.

### Pattern

We choose the projection per index, based on what that access pattern needs to return:

| Projection  | Copies                      | Use when                                                   |
|-------------|-----------------------------|------------------------------------------------------------|
| `KEYS_ONLY` | table + index keys          | We only need IDs, or we'll `BatchGetItem` a few results.   |
| `INCLUDE`   | keys + named attributes     | List views needing a few fields (customer, total).         |
| `ALL`       | everything                  | The index serves full-item reads, or items are small.      |

### In practice

The script builds all three projections over the same orders, each of which carries a large `lineItems` blob that a list view never needs:

```python
table = recreate_table(
    "p15-gsi-projections",
    gsis=[
        gsi("ByStatusKeys", pk="status", sk="createdAt", projection="KEYS_ONLY"),
        gsi("ByStatusInclude", pk="status", sk="createdAt", projection="INCLUDE", include=["customer", "total"]),
        gsi("ByStatusAll", pk="status", sk="createdAt", projection="ALL"),
    ],
)

for index in ["ByStatusKeys", "ByStatusInclude", "ByStatusAll"]:
    item = table.query(IndexName=index, KeyConditionExpression=Key("status").eq("OPEN"), Limit=1)["Items"][0]
    show(f"{index}: attributes returned", sorted(item))

# KEYS_ONLY needs a second round trip to get the rest of the item.
keys = table.query(IndexName="ByStatusKeys", KeyConditionExpression=Key("status").eq("OPEN"))["Items"]
full = client.batch_get_item(RequestItems={table.name: {"Keys": [{"PK": k["PK"], "SK": k["SK"]} for k in keys], ...}})
```

```text
>>> Query p15-gsi-projections
    key:        status = 'OPEN'
    IndexName:  ByStatusKeys
    Limit:      1

=== ByStatusKeys: attributes returned ===
[
  "PK",
  "SK",
  "createdAt",
  "status"
]

>>> Query p15-gsi-projections
    key:        status = 'OPEN'
    IndexName:  ByStatusInclude
    Limit:      1

=== ByStatusInclude: attributes returned ===
[
  "PK",
  "SK",
  "createdAt",
  "customer",
  "status",
  "total"
]

>>> Query p15-gsi-projections
    key:        status = 'OPEN'
    IndexName:  ByStatusAll
    Limit:      1

=== ByStatusAll: attributes returned ===
[
  "PK",
  "SK",
  "createdAt",
  "customer",
  "lineItems",
  "status",
  "total"
]

>>> Query p15-gsi-projections
    key:        status = 'OPEN'
    IndexName:  ByStatusKeys

>>> BatchGetItem
    p15-gsi-projections: 5 keys, e.g. {PK: 'ORDER#0', SK: 'ORDER'}

=== KEYS_ONLY + BatchGetItem (2nd request) ===
5

=== Index sizes (Local reports the same number for each; on AWS ALL > INCLUDE > KEYS_ONLY) ===
{
  "ByStatusInclude": 6124,
  "ByStatusAll": 6124,
  "ByStatusKeys": 6124
}
```

`KEYS_ONLY` returns just the table and index keys. `INCLUDE` adds exactly the `customer` and `total` we asked for. `ALL` drags `lineItems` along too. To show the full order from the `KEYS_ONLY` index we need the second `BatchGetItem` round trip. The index sizes at the end are identical only because DynamoDB Local doesn't track them per index.

### Why

- **Write cost.** A table write also writes to each GSI whose projected attributes changed. With `ALL`, updating a large blob that no index queries on is still copied into the index.
- **Storage.** Large, rarely needed attributes (`lineItems`, descriptions) shouldn't be copied into every index.

### Trade-offs

- **We can't change a GSI's projection.** We have to create a new index and drop the old one. If unsure, `ALL` is the safe default for small items.
- `KEYS_ONLY` plus a fetch costs an extra round trip and extra RCUs per result.

### Gotchas

- Querying a GSI for an attribute that isn't projected returns the item **without** that attribute. There's no error, so it's easy to miss.
- [Sparse indexes](../02-modelling/#10--sparse-index) and [overloaded GSIs](../02-modelling/#09--gsi-overloading) multiply these savings.
- DynamoDB Local reports the same `IndexSizeBytes` for every index, as we saw above. On AWS, look at `IndexSizeBytes` in `DescribeTable` (updated about every 6 hours).

## 16 · Batch operations with retries

**Code:** [16-batch-retries.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/03-querying/16-batch-retries/16-batch-retries.py) · run with `just run 16`

### Problem

`BatchWriteItem` and `BatchGetItem` save round trips, but they can **partly succeed**. If some items are throttled or the response is too big, the call still returns HTTP 200 and lists the leftovers in `UnprocessedItems` / `UnprocessedKeys`. Code that ignores them silently loses writes or misses reads.

### Pattern

1. **Chunk** to the API limits: 25 puts/deletes per `BatchWriteItem` (16 MB max), and 100 keys per `BatchGetItem` (16 MB max).
2. After every call, **resend only the unprocessed part**.
3. Wait between retries with **exponential backoff and jitter**, and give up after N attempts.

```python
for attempt in range(max_attempts):
    resp = client.batch_write_item(RequestItems=request)
    request = resp["UnprocessedItems"]
    if not request:
        break
    time.sleep(min(cap, base * 2**attempt) * random.uniform(0.5, 1))
```

For writes, boto3's `Table.batch_writer()` already chunks to 25 and resends unprocessed items for us. Its `overwrite_by_pkeys` option drops duplicate keys within a batch, which would otherwise fail validation. There's no equivalent helper for `BatchGetItem`, so there we write the loop ourselves.

### In practice

DynamoDB Local never throttles, so the script wraps `batch_write_item` in a `flaky_batch_write` that pretends the first call left a third of the items unprocessed. A generic `with_backoff` helper retries whatever comes back unprocessed:

```python
def with_backoff(call, request, unprocessed_key, max_attempts=8):
    """Call a batch API, retrying only what came back unprocessed, with jittered exponential backoff."""
    responses = []
    for attempt in range(max_attempts):
        resp = call(RequestItems=request)
        responses.append(resp)
        request = {t: r for t, r in (resp.get(unprocessed_key) or {}).items() if r}
        if not request:
            return responses
        delay = min(2.0, 0.05 * 2 ** (attempt + 1)) * random.uniform(0.5, 1.0)  # capped, jittered
        print(f"  retry #{attempt + 1} in {delay:.2f}s")
        time.sleep(delay)
    raise RuntimeError(f"still unprocessed after {max_attempts} attempts: {request}")


# BatchWriteItem: 60 items -> batches of 25/25/10
for batch in chunks(items, MAX_BATCH_WRITE):
    request = {TABLE: [{"PutRequest": {"Item": it}} for it in batch]}
    with_backoff(flaky_batch_write, request, "UnprocessedItems")

# The easy way for writes: batch_writer() chunks to 25 and resends unprocessed items for you
with dynamodb.Table(TABLE).batch_writer(overwrite_by_pkeys=["PK", "SK"]) as w:
    for i in range(60, 130):
        w.put_item(Item={"PK": f"ITEM#{i:03}", "SK": "META", "n": i})
```

```text
=== Writing 60 items in batches of 25 ===

>>> BatchWriteItem
    p16-batch-retries: 25 puts, 0 deletes
  (simulated) 8 items came back unprocessed
  retry #1 in 0.06s

>>> BatchWriteItem
    p16-batch-retries: 8 puts, 0 deletes
  wrote batch of 25

>>> BatchWriteItem
    p16-batch-retries: 25 puts, 0 deletes
  wrote batch of 25
  wrote batch of 10
    ... (+1 more BatchWriteItem calls not shown)

>>> BatchGetItem
    p16-batch-retries: 60 keys, e.g. {PK: 'ITEM#000', SK: 'META'}

=== Fetched back ===
{
  "count": 60,
  "note": "BatchGetItem returns items in no particular order"
}

>>> BatchWriteItem
    p16-batch-retries: 25 puts, 0 deletes

>>> BatchWriteItem
    p16-batch-retries: 25 puts, 0 deletes

>>> BatchWriteItem
    p16-batch-retries: 20 puts, 0 deletes

>>> Scan p16-batch-retries
    Select:     COUNT

=== Items in table after batch_writer() added 70 more ===
130
```

The first batch of 25 comes back with 8 unprocessed items, and the retry sends exactly those 8, not all 25. All 60 keys then come back in a single `BatchGetItem` (under the 100-key limit). Finally `batch_writer()` splits 70 puts into 25/25/20 on its own, leaving 130 items in the table.

### Why

- **Fewer round trips.** One request instead of 25 or 100.
- **Correctness.** The retry loop is what makes batches safe to use.
- Jittered backoff stops many clients from retrying in lockstep and making the throttling worse.

### Trade-offs

- **Not atomic.** Some items can succeed while others fail. When it must be all-or-nothing, use `TransactWriteItems` (see [transactions](../05-consistency/#25--transactions)).
- **Costs the same capacity** as single calls. Batching saves latency, not money.
- `BatchWriteItem` has no conditions or updates: only `PutRequest` (a full overwrite) and `DeleteRequest`.

### Gotchas

- The same key twice in one batch raises a `ValidationException`.
- `BatchGetItem` returns items **in any order**, so we match them up by key.
- Unprocessed items usually point to a hot partition or under-provisioned capacity (see [write sharding](../07-performance-and-scale/#35--write-sharding) and [capacity modes](../08-operations/#38--capacity-modes-on-demand-vs-provisioned)). Retrying hides the symptom, so we should alarm on throttling metrics too.
- The AWS SDKs also retry *throttling errors* themselves (`retries={"mode": "adaptive"}` in botocore's `Config`). That is separate from `Unprocessed*`, which we must always handle ourselves.

---
title: "09 - What not to do"
author: "James"
date: "2026-10-20"
summary: "The common ways DynamoDB designs go wrong, each measured, with the pattern that fixes it."
tags: ["dynamodb", "aws", "databases", "anti-patterns"]
draft: false
hideHeader: true
---

We finish the series by turning everything around. Most DynamoDB pain comes from a short list of mistakes, and each one has a symptom we can spot and a pattern from earlier in the series that fixes it. This page measures what each mistake actually costs, using `ReturnConsumedCapacity` and request counts, so it doubles as a review checklist for an existing table.

| Anti-pattern | Symptom | Fix |
|---|---|---|
| [One table per entity, joined in the app](#1-relational-modelling-one-table-per-entity-joins-in-code) | Several round trips per page | [04 · Single-table design](../02-modelling/#04--single-table-design) |
| [Unbounded list inside an item](#2-unbounded-lists-or-maps-inside-one-item) | Write cost grows on every append, then the write fails at 400 KB | [17 · Keep items small](../04-item-size/#17--keep-items-small-use-item-collections) |
| [Low-cardinality partition key](#3-low-cardinality-partition-key) | Throttling on one hot key while the rest of the table is idle | [34 · High-cardinality keys](../07-performance-and-scale/#34--high-cardinality-partition-keys), [35 · Write sharding](../07-performance-and-scale/#35--write-sharding) |
| [Scan + filter in a request path](#4-scan--filterexpression-instead-of-a-key-query) | Read cost proportional to table size | [12 · Avoid Scan](../03-querying/#12--avoid-scan-use-parallel-scan-for-batch-jobs), [10 · Sparse index](../02-modelling/#10--sparse-index) |
| [Too many GSIs](#5-too-many-gsis) | Every write costs one extra write per index | [09 · GSI overloading](../02-modelling/#09--gsi-overloading) |
| [Ad-hoc analytics on the live table](#6-ad-hoc-analytics-on-the-live-table) | Reporting jobs eat capacity and throttle the app | [41 · Analytics outside DynamoDB](../08-operations/#41--analytics-outside-dynamodb) |

## 42 · Anti-patterns

**Code:** [42-anti-patterns.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/09-anti-patterns/42-anti-patterns/42-anti-patterns.py) · run with `just run 42`

The script builds a small table for each mistake and measures it. All the numbers below come from a run against DynamoDB Local. For each anti-pattern we look at the smell (how to recognise it), the cost (what the script measured) and the fix.

### 1. Relational modelling (one table per entity, joins in code)

**Smell:** `users`, `orders` and `addresses` tables, with the app fetching a user and then looping over order IDs.

**Cost:** N+1 requests. The script stores a user with three order IDs in a `users` table, and the orders in an `orders` table. It then loads the same data from a single table where the user and their orders share a partition key:

```python
user = users.get_item(Key={"userId": "u1"})["Item"]
for oid in user["orderIds"]:
    orders.get_item(Key={"orderId": oid})
    requests += 1

single.query(KeyConditionExpression=Key("PK").eq("USER#u1"))
```

```text
>>> GetItem p42-users
    key:        {userId: 'u1'}

>>> GetItem p42-orders
    key:        {orderId: 'o1'}

>>> GetItem p42-orders
    key:        {orderId: 'o2'}
    ... (+1 more GetItem calls not shown)

>>> Query p42-single
    key:        PK = 'USER#u1'

=== 1. Relational modeling: requests to load a user + orders ===
{
  "table-per-entity": 4,
  "single-table": 1
}
```

Loading a user with 3 orders took **4 requests vs 1**, and latency grows with N.

**Fix:** put items that are read together in one item collection ([04](../02-modelling/#04--single-table-design), [11](../02-modelling/#11--denormalization-and-duplication)), and design from the access patterns ([02](../02-modelling/#02--access-pattern-first-design)).

### 2. Unbounded lists or maps inside one item

**Smell:** `comments: [...]`, `events: [...]` or `followers: {...}` that grow forever.

**Cost:** every update rewrites the **whole** item. The script appends 10 KB messages to a `messages` list on a single chat item until something breaks:

```python
resp = t.update_item(
    Key={"PK": "CHAT#c1", "SK": "META"},
    UpdateExpression="SET messages = list_append(messages, :m)",
    ExpressionAttributeValues={":m": [f"message {i} " + "x" * 10_000]},
    ReturnConsumedCapacity="TOTAL",
)
```

```text
>>> UpdateItem p42-unbounded
    key:        {PK: 'CHAT#c1', SK: 'META'}
    update:     SET messages = list_append(messages, ['message 0 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'])
    ... (+38 more UpdateItem calls not shown)

=== 2. Unbounded list ===
{
  "appends before failure": 40,
  "WCU of 1st / last append": [
    10.0,
    392.0
  ],
  "error": "Item size to update has exceeded the maximum allowed size",
  "fix": "one item per message: PK=CHAT#c1, SK=MSG#<ulid> (patterns 17, 06)"
}
```

The first append cost 10 WCU, which is just the new 10 KB. By the 40th append, the same-sized message cost **392 WCU**, because we were paying to rewrite every message before it. The next append failed outright, because the item had reached the 400 KB limit.

**Fix:** one item per child (`PK=CHAT#c1, SK=MSG#<ulid>`), and query the collection ([17](../04-item-size/#17--keep-items-small-use-item-collections), [06](../02-modelling/#06--sortable-ids-latest-first)). For big blobs, see [20](../04-item-size/#20--offload-large-items-to-s3) and [21](../04-item-size/#21--chunking).

### 3. Low-cardinality partition key

**Smell:** `PK = status`, `PK = date`, `PK = tenant` when one tenant is huge, or `PK = "ALL"`.

**Cost:** traffic piles onto a few keys. The script writes 1,000 orders keyed by status, with 90% of them `PENDING`:

```text
=== 3. Low-cardinality PK (PK=status): items per partition key ===
{
  "PENDING": 900,
  "SHIPPED": 90,
  "CANCELLED": 10,
  "note": "90% of reads/writes hit one key -> ~1,000 WCU/s cap. Use PK=ORDER#id + sparse GSI (10) or sharding (35)"
}
```

DynamoDB Local doesn't throttle, so the script can only show the distribution. In AWS, 90% of the load would hit one partition key, which is capped at about 1,000 WCU / 3,000 RCU per second. Throttling follows, however much capacity the table has.

**Fix:** a high-cardinality PK such as `ORDER#id` ([34](../07-performance-and-scale/#34--high-cardinality-partition-keys)). Serve "orders by status" from a sparse GSI ([10](../02-modelling/#10--sparse-index)), and shard keys that are hot by nature ([35](../07-performance-and-scale/#35--write-sharding)).

### 4. Scan + FilterExpression instead of a key query

**Smell:** `table.scan(FilterExpression=Attr("customer").eq(x))` on a request path.

**Cost:** we pay for every item **read**, not every item returned. The script stores 1,000 orders across 100 customers, then finds customer `C7`'s orders twice: once with a filtered Scan, and once with a Query on a GSI keyed by customer:

```python
kwargs = dict(FilterExpression=Attr("customer").eq("C7"), ReturnConsumedCapacity="TOTAL")
resp = t.scan(**kwargs)  # looped over every page

q = t.query(IndexName="GSI1", KeyConditionExpression=Key("GSI1PK").eq("C7"), ReturnConsumedCapacity="TOTAL")
```

```text
>>> Scan p42-scan-filter
    filter:     customer = 'C7'

>>> Query p42-scan-filter
    key:        GSI1PK = 'C7'
    IndexName:  GSI1

=== 4. Scan+filter vs Query on a GSI (find one customer's orders) ===
{
  "scan": {
    "scanned": 1000,
    "returned": 10,
    "RCU": 68.0
  },
  "query": {
    "scanned": 10,
    "returned": 10,
    "RCU": 1.0
  }
}
```

Both return the same 10 orders. The Scan read all 1,000 items to find them and cost **68 RCU**. The GSI Query read only the 10 it needed and cost **1 RCU**. The scan also gets worse as the table grows, while the query doesn't.

**Fix:** add a key or GSI for the access pattern ([09](../02-modelling/#09--gsi-overloading), [07](../02-modelling/#07--inverted-index)). See also [12](../03-querying/#12--avoid-scan-use-parallel-scan-for-batch-jobs) and [13](../03-querying/#13--filter-expressions-dont-reduce-cost).

### 5. Too many GSIs

**Smell:** one GSI per attribute "just in case", up to the limit of 20.

**Cost:** every write is repeated into each index that projects the item. The script puts the same ~1 KB item into tables with 0, 2 and 5 GSIs, and reads the write cost back with `ReturnConsumedCapacity="INDEXES"`:

```text
>>> PutItem p42-gsis-0
    item:       {PK: 'X', SK: 'Y', pad: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'}

>>> PutItem p42-gsis-2
    item:       {PK: 'X', SK: 'Y', pad: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...', GSI0PK: 'a', GSI0SK: 'b', GSI1PK: 'a', GSI1SK: 'b'}

>>> PutItem p42-gsis-5
    item:       {PK: 'X', SK: 'Y', pad: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...', GSI0PK: 'a', GSI0SK: 'b', GSI1PK: 'a', GSI1SK: 'b', GSI2PK: 'a', GSI2SK: 'b', GSI3PK: 'a', GSI3SK: 'b', GSI4PK: 'a', GSI4SK: 'b'}

=== 5. WCU for one ~1 KB put ===
{
  "0 GSIs": 1.0,
  "2 GSIs": 3.0,
  "5 GSIs": 6.0
}
```

One put cost **1 WCU with 0 GSIs, 3 with 2, and 6 with 5**: one write for the table, plus one per index. In provisioned mode, an under-provisioned GSI also throttles writes to the base table.

**Fix:** overload a few generic GSIs (`GSI1PK`/`GSI1SK`) to serve many patterns ([09](../02-modelling/#09--gsi-overloading)), keep them sparse ([10](../02-modelling/#10--sparse-index)), and project only what we need ([15](../03-querying/#15--gsi-projections)).

### 6. Ad-hoc analytics on the live table

**Smell:** reporting queries, dashboards or "export everything" jobs scanning production tables.

**Cost:** a full scan every time (see #4), competing with user traffic for capacity. And even then, there's no GROUP BY, JOIN or ORDER BY on non-key attributes. The script doesn't measure this one; it's #4 at a larger scale:

```text
=== 6. Ad-hoc analytics on DynamoDB ===
"GROUP BY / joins / 'top N by X' need a full scan every time (see #4) and steal capacity from live traffic. Export to S3 + Athena, or zero-ETL to Redshift instead (pattern 41)."
```

**Fix:** export to S3 + Athena, zero-ETL to Redshift or OpenSearch, or stream changes to a data lake ([41](../08-operations/#41--analytics-outside-dynamodb), [31](../06-lifecycle-and-events/#31--dynamodb-streams--cdc)).

### Also watch for

A few smaller mistakes don't get their own measurement, but come up just as often:

- **Not handling `UnprocessedItems`** in batch calls, which silently loses writes ([16](../03-querying/#16--batch-operations-with-retries)).
- **Reading a GSI right after writing** and expecting to see the write ([28](../05-consistency/#28--gsis-are-eventually-consistent)).
- **Offset pagination** ("page 7"). DynamoDB only has cursors ([14](../03-querying/#14--pagination-with-cursors)).
- **Read-modify-write without conditions**, which causes lost updates ([23](../05-consistency/#23--optimistic-locking), [22](../05-consistency/#22--conditional-writes)).
- **Random UUIDs as sort keys** when we need time order ([06](../02-modelling/#06--sortable-ids-latest-first)).

That's the end of the series. If you've read this far, the best next step is to clone the [repo](https://github.com/jfgrea27/dynamodb-patterns), run `just up`, and break things for yourself. Or go back to the [start](../01-intro-and-setup/) and pick the patterns that match the problem in front of you.

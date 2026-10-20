---
title: "01 - Intro & setup"
author: "James"
date: "2026-10-20"
summary: "What DynamoDB is, the everyday API, and how to develop against DynamoDB Local."
tags: ["dynamodb", "aws", "databases", "docker"]
draft: false
hideHeader: true
---

Before any of the patterns make sense, we need a shared vocabulary: what a table, an item and a key are, how DynamoDB stores data on partitions, what each read and write operation costs, and what the request language looks like. This page covers all of that, then walks through the everyday API (lesson 00) and how to develop against DynamoDB without an AWS account (lesson 01).

Every later page assumes the material here, so it's worth reading even if you've used DynamoDB before.

| # | Section | You'll learn |
|---|---|---|
| | [What DynamoDB is](#what-dynamodb-is) | The one-paragraph pitch, and the price of it |
| | [The data model](#the-data-model) | Tables, items, attributes, keys, item collections, types |
| | [How data is stored: partitions](#how-data-is-stored-partitions) | Hashing, per-partition limits, why key design matters |
| | [Reading data](#reading-data) / [Writing data](#writing-data) | The operations and what they cost |
| | [Expressions](#expressions) | The small string language every request uses |
| | [Secondary indexes](#secondary-indexes) | GSIs vs LSIs |
| | [Capacity and cost](#capacity-and-cost) | Read and write units, on-demand vs provisioned |
| | [Built-in features](#built-in-features) / [Limits](#limits-worth-memorising) | What comes for free, and the numbers to remember |
| 00 | [Basics](#00--basics) | Put, get, update, query, conditional put, delete, scan |
| 01 | [Local development](#01--local-development) | Docker setup, endpoint config, per-test tables, Local vs LocalStack vs moto |

## What DynamoDB is

Amazon DynamoDB is a fully managed, serverless **key-value and document database**. We create a table and read and write items over an HTTPS API. AWS handles the servers, storage, replication, patching and scaling for us.

Its promise is **consistent single-digit-millisecond latency at any scale**, from ten requests a day to millions a second. The price of that promise is that we **design the table around the queries we will run**. DynamoDB is very fast at fetching data by key, and it deliberately offers nothing slower.

It grew out of Amazon's internal *Dynamo* system (described in the [2007 paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)) and launched as an AWS service in 2012.

## The data model

A handful of terms come up on every page of this series:

| Term | Meaning |
|---|---|
| **Table** | A collection of items. The only thing we declare up front is the primary key (and any indexes). |
| **Item** | One record, up to **400 KB**. Think of it as a JSON document. |
| **Attribute** | A named value on an item. Items in the same table can have completely different attributes. |
| **Primary key** | Uniquely identifies an item. Either a *partition key* alone, or *partition key + sort key*. |
| **Partition key (PK, "hash key")** | Hashed to decide which physical partition stores the item. |
| **Sort key (SK, "range key")** | Orders items that share a partition key. Enables range queries. |
| **Item collection** | All items that share a partition key value. One `Query` can read all or part of it. |

The item collection is the idea to hold on to. Most of the modelling patterns are about deciding which items should live together in one.

### Data types

| Type | Code | Example |
|---|---|---|
| String | `S` | `"USER#alice"` |
| Number | `N` | `42`, `3.14`. Sent as a string on the wire, up to 38 digits of precision. |
| Binary | `B` | gzip bytes, images |
| Boolean | `BOOL` | `true` |
| Null | `NULL` | `null` |
| Map | `M` | nested object `{"city": "London"}` |
| List | `L` | `["a", 1, true]` |
| String / Number / Binary set | `SS` / `NS` / `BS` | `{"red", "blue"}`, unique and unordered |

Key attributes must be `S`, `N` or `B`. In Python, boto3's resource API (`boto3.resource("dynamodb")`) converts our values to and from these types for us. The one surprise is that numbers come back as `Decimal`.

## How data is stored: partitions

```text
             hash(PK)
 item ──────────────────▶  partition 1  [ PK=A: SK1, SK2, SK3 ]  [ PK=D: ... ]
                           partition 2  [ PK=B: ... ]
                           partition 3  [ PK=C: ... ]
```

When we write an item, DynamoDB hashes its partition key to pick a **partition**. Inside a partition, items with the same PK are stored **sorted by SK**, which is what makes range queries on the sort key cheap.

A partition holds about **10 GB** and serves up to **3,000 read units/s and 1,000 write units/s**. DynamoDB splits partitions automatically as data or traffic grows, and every write is replicated to **three Availability Zones** before it is acknowledged.

This is why key design matters so much. Traffic spread across many PK values scales without limit. Traffic concentrated on one PK value (a *hot partition*) hits the per-partition ceiling, however much capacity the table has. We come back to this in [performance & scale](../07-performance-and-scale/).

## Reading data

There are four ways to read:

| Operation | What it does | Cost profile |
|---|---|---|
| `GetItem` | Fetch one item by its full primary key | Cheapest, constant time |
| `BatchGetItem` | Up to 100 `GetItem`s in one call (any tables) | Same as the individual gets |
| `Query` | Items from **one** partition key, optionally narrowed by a sort-key condition (`=`, `<`, `>`, `between`, `begins_with`), in SK order, forwards or backwards | Pay only for items read |
| `Scan` | Read every item in the table or index | Pays for the whole table. Batch jobs only. |

A few rules apply to all of them:

- Results come back in **pages of up to 1 MB**. We follow `LastEvaluatedKey` to get the next page.
- **Consistency:** reads are *eventually consistent* by default. They cost half as much and may be a moment stale. Passing `ConsistentRead=True` gives a *strongly consistent* read on the table (this isn't available on GSIs).
- **Filter expressions** drop items *after* they've been read. They save bandwidth, not cost.

## Writing data

| Operation | What it does |
|---|---|
| `PutItem` | Create or **fully replace** an item |
| `UpdateItem` | Change specific attributes (`SET`, `REMOVE`, `ADD`, `DELETE`). Creates the item if it's missing. |
| `DeleteItem` | Remove an item |
| `BatchWriteItem` | Up to 25 puts or deletes in one call. **Not atomic**: some may come back as `UnprocessedItems`. |
| `TransactWriteItems` | Up to 100 actions across tables, **all or nothing** (costs 2× units) |

Any single-item write can carry a **condition expression**, such as "only if it doesn't exist" or "only if `version = 3`". If the condition fails, the write is rejected and nothing changes. Conditions are the foundation of most of the concurrency patterns in [consistency & concurrency](../05-consistency/).

## Expressions

The request language is a set of small string expressions with placeholders. Here's an update that renames a user and bumps a counter, but only if the user exists:

```python
table.update_item(
    Key={"PK": "USER#alice", "SK": "PROFILE"},
    UpdateExpression="SET #n = :name ADD loginCount :one",
    ConditionExpression="attribute_exists(PK)",
    ExpressionAttributeNames={"#n": "name"},          # "name" is a reserved word
    ExpressionAttributeValues={":name": "Alice", ":one": 1},
)
```

There are five kinds of expression:

| Expression | Used for |
|---|---|
| `KeyConditionExpression` | Which partition (and SK range) a `Query` reads |
| `FilterExpression` | Drop items after reading (Query/Scan) |
| `ConditionExpression` | Guard a write |
| `UpdateExpression` | What an `UpdateItem` changes |
| `ProjectionExpression` | Which attributes to return |

boto3's `Key("PK").eq(...)` and `Attr("status").eq(...)` helpers build these for us. The demos in the repo print the final expression for every request, with the names and values filled in, so we can always see exactly what was sent.

## Secondary indexes

An index is a second copy of (some of) our data, keyed differently so we can query it another way. DynamoDB keeps it in sync automatically. There are two kinds:

| | Global secondary index (GSI) | Local secondary index (LSI) |
|---|---|---|
| Keys | Any partition key + optional sort key | Same partition key, different sort key |
| When created | Any time | Only at table creation |
| Consistency | Eventually consistent only | Strong or eventual |
| Capacity | Its own | Shares the table's |
| Limits | 20 per table (default) | 5 per table. Caps each item collection at 10 GB. |

In practice, prefer GSIs. One property turns out to be very useful: items that don't have the index key attributes are left out of the index entirely. That's a *sparse index*, and it's a powerful tool. Indexes come up throughout [modelling](../02-modelling/) and [querying](../03-querying/).

## Capacity and cost

We pay for **reads**, **writes** and **storage**:

- **1 read unit** = one strongly consistent read of up to **4 KB** (or two eventually consistent reads). Transactional reads cost 2×.
- **1 write unit** = one write of up to **1 KB**. Transactional writes cost 2×. Every GSI the item lands in costs another write.
- **On-demand mode:** pay per request and scale instantly. **Provisioned mode:** reserve units per second (with auto scaling). Provisioned is cheaper for steady traffic.
- Item size drives cost. A 5 KB item costs 2 read units and 5 write units every time we touch it. This is why there's a whole page on [item size](../04-item-size/).

## Built-in features

DynamoDB comes with a set of features that several patterns build on:

| Feature | What it gives us | Pattern |
|---|---|---|
| **TTL** | Automatic, free deletion of items after a timestamp | [30](../06-lifecycle-and-events/#30--ttl-for-expiry) |
| **Streams** | An ordered, 24-hour log of every item change, for triggers and replication | [31](../06-lifecycle-and-events/#31--dynamodb-streams--cdc) |
| **Transactions** | ACID across up to 100 items | [25](../05-consistency/#25--transactions) |
| **PITR & backups** | Restore to any second in the last 35 days | [39](../08-operations/#39--point-in-time-recovery--backups) |
| **Global tables** | Multi-region, active-active replication | [40](../08-operations/#40--global-tables-multi-region) |
| **Export to S3** | Full-table export for analytics, without using table capacity | [41](../08-operations/#41--analytics-outside-dynamodb) |
| **DAX** | In-memory, microsecond read cache with the same API | [36](../07-performance-and-scale/#36--caching-dax--elasticache) |
| **PartiQL** | SQL-like syntax (`SELECT * FROM t WHERE PK = ?`). It still only runs efficient key lookups if we write it that way. | n/a |

## Limits worth memorising

| Limit | Value |
|---|---|
| Item size | 400 KB (names + values) |
| Query / Scan page | 1 MB before filtering |
| Per partition | 3,000 RCU/s, 1,000 WCU/s, ~10 GB |
| `BatchWriteItem` / `BatchGetItem` | 25 / 100 items |
| Transaction | 100 items, 4 MB |
| GSIs / LSIs per table | 20 (soft) / 5 |
| LSI item collection | 10 GB |
| Stream retention | 24 hours |
| Nested attribute depth | 32 levels |

## The mental model to carry forward

If we remember five things from this page, they should be these:

1. **Start from the access patterns.** Write down every question the app asks, then design keys so each one is a `GetItem` or a `Query`.
2. **Store data the way it is read.** Items fetched together share a partition key. Data needed on another item gets copied there.
3. **Spread the load.** Use high-cardinality partition keys so traffic and storage spread across partitions.
4. **Keep items small**, and avoid `Scan` in request paths.
5. **Use conditions for correctness.** Atomic updates and conditional writes replace locks.

The rest of the series takes each of these and turns it into concrete patterns:

| Page | What it covers |
|---|---|
| [02 - Modelling](../02-modelling/) | Designing keys, single-table design, indexes, relationships |
| [03 - Querying](../03-querying/) | Reading efficiently: Scan vs Query, filters, pagination, projections, batches |
| [04 - Item size](../04-item-size/) | Living with the 400 KB limit and per-KB pricing |
| [05 - Consistency](../05-consistency/) | Correct concurrent writes: conditions, locking, transactions, idempotency |
| [06 - Lifecycle & events](../06-lifecycle-and-events/) | Expiry, change streams, archival |
| [07 - Performance & scale](../07-performance-and-scale/) | Hot partitions, sharding, caching, time-series |
| [08 - Operations](../08-operations/) | Capacity, backups, multi-region, analytics |
| [09 - What not to do](../09-anti-patterns/) | What goes wrong and how to spot it |

First, though, let's see the API in action.

## 00 · Basics

**Code:** [00-basics.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/00-intro/00-basics/00-basics.py) · run with `just run 00`

### Problem

Before the patterns make sense, we need to be comfortable with the everyday API: how to write an item, read it back, change it, query a partition and delete it.

### Pattern

We use one table with a composite key (`PK` partition key, `SK` sort key) holding animals:

| PK           | SK      | attributes                        |
|--------------|---------|-----------------------------------|
| `ANIMAL#dog` | `Bella` | age                               |
| `ANIMAL#dog` | `Rex`   | age, breed, tags (string set)     |
| `ANIMAL#cat` | `Tom`   | age, owner (map)                  |

The script walks through each core operation in turn:

| Operation | Call | Notes |
|---|---|---|
| Create / replace | `put_item(Item=...)` | Replaces the whole item if the key exists |
| Read one | `get_item(Key=...)` | Needs the full key. Missing items return no `Item`, not an error. |
| Change some attributes | `update_item(UpdateExpression="SET ... REMOVE ...")` | `ReturnValues="ALL_NEW"` returns the result |
| Read a partition | `query(KeyConditionExpression=Key("PK").eq(...))` | Sorted by SK. `ScanIndexForward=False` reverses. |
| Narrow by sort key | `& Key("SK").begins_with("R")` | Also `between`, `<`, `>`, `=` |
| Guarded write | `ConditionExpression="attribute_not_exists(PK)"` | Raises `ConditionalCheckFailedException` |
| Delete | `delete_item(Key=..., ReturnValues="ALL_OLD")` | Returns the deleted item |
| Read everything | `scan()` | Reads the whole table. Avoid outside batch jobs. |

### In practice

Here's the heart of the script, from the update onwards:

```python
# UpdateItem: change some attributes, leave the rest. ReturnValues shows the result.
resp = table.update_item(
    Key={"PK": "ANIMAL#dog", "SK": "Rex"},
    UpdateExpression="SET age = age + :one, last_vet = :d REMOVE breed",
    ExpressionAttributeValues={":one": 1, ":d": "2026-10-20"},
    ReturnValues="ALL_NEW",
)

# Query with a sort key condition, descending SK.
resp = table.query(
    KeyConditionExpression=Key("PK").eq("ANIMAL#dog") & Key("SK").begins_with("R"),
    ScanIndexForward=False,
)

# Conditional write: only create if it doesn't already exist.
try:
    table.put_item(Item={"PK": "ANIMAL#dog", "SK": "Rex", "age": 0}, ConditionExpression="attribute_not_exists(PK)")
except table.meta.client.exceptions.ConditionalCheckFailedException:
    show("Conditional put rejected", "Rex already exists, nothing was overwritten")
```

And here's what it sends and gets back:

```text
>>> PutItem p00-basics
    item:       {PK: 'ANIMAL#dog', SK: 'Rex', age: 4, breed: 'labrador', tags: {'good', 'loud'}}

>>> GetItem p00-basics
    key:        {PK: 'ANIMAL#dog', SK: 'Nope'}

=== GetItem missing key ===
false

>>> UpdateItem p00-basics
    key:        {PK: 'ANIMAL#dog', SK: 'Rex'}
    update:     SET age = age + 1, last_vet = '2026-10-20' REMOVE breed
    ReturnValues: ALL_NEW

=== UpdateItem Rex (age+1, set last_vet, remove breed) ===
{
  "SK": "Rex",
  "PK": "ANIMAL#dog",
  "last_vet": "2026-10-20",
  "age": 5,
  "tags": [
    "good",
    "loud"
  ]
}

>>> Query p00-basics
    key:        PK = 'ANIMAL#dog'

=== Query all dogs ===
[
  {
    "SK": "Bella",
    "age": 2,
    "PK": "ANIMAL#dog"
  },
  {
    "SK": "Rex",
    ...
  }
]

>>> Query p00-basics
    key:        (PK = 'ANIMAL#dog' AND begins_with(SK, 'R'))
    ScanIndexForward: False

>>> PutItem p00-basics
    item:       {PK: 'ANIMAL#dog', SK: 'Rex', age: 0}
    condition:  attribute_not_exists(PK)

=== Conditional put rejected ===
"Rex already exists, nothing was overwritten"

>>> DeleteItem p00-basics
    key:        {PK: 'ANIMAL#cat', SK: 'Tom'}
    ReturnValues: ALL_OLD

=== DeleteItem Tom (old value) ===
{
  "SK": "Tom",
  "owner": {
    "name": "Sam",
    "city": "Leeds"
  },
  "PK": "ANIMAL#cat",
  "age": 7
}

>>> Scan p00-basics
```

A few things stand out. The `GetItem` on a missing key quietly returns no item rather than raising. The update expression is shown with the real values substituted in, and `REMOVE breed` really does drop the attribute from the returned item. The query for all dogs comes back sorted by sort key (`Bella` before `Rex`). And the conditional put is rejected without touching the existing `Rex`.

### Why

Every pattern in this series is a combination of these calls with carefully chosen keys. It's worth watching the printed `>>>` requests to see the expressions boto3 actually sends, because that's what DynamoDB evaluates and bills us for.

### Gotchas

- `put_item` **replaces** the whole item. Use `update_item` to change some attributes.
- Numbers come back as `Decimal`, and sets come back as a Python `set`.
- Words like `name`, `status` and `date` are reserved in expressions. Use `ExpressionAttributeNames` (`#n`) to refer to them.

## 01 · Local development

**Code:** [01-local-development.py](https://github.com/jfgrea27/dynamodb-patterns/blob/main/patterns/01-setup/01-local-development/01-local-development.py) · run with `just run 01` (needs `just up`)

### Problem

Developing straight against AWS is slow, costs money, needs credentials, and lets tests collide in shared tables. Mocking boto3 by hand isn't much better: it misses real behaviour like condition failures, key validation and GSI queries.

### Pattern

We run **DynamoDB Local**, AWS's own emulator, in Docker. It speaks the same API, so the same boto3 code works locally and in AWS. The only switch is the endpoint:

```yaml
# docker-compose.yml (this repo)
services:
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    command: "-jar DynamoDBLocal.jar -sharedDb -dbPath ./data"
    ports: ["8000:8000"]
    volumes: ["./docker/dynamodb:/home/dynamodblocal/data"]
```

```python
endpoint = os.environ.get("DYNAMODB_ENDPOINT")  # unset in prod
boto3.resource("dynamodb", endpoint_url=endpoint, ...)
```

Everything in the repo reads `DYNAMODB_ENDPOINT`. In production we leave it unset, and the normal AWS credential chain takes over.

For tests, we give **each test its own uniquely named table** and always delete it afterwards. The script does this with a `temp_table()` context manager; a pytest fixture works just as well. Each lesson in the repo follows the same idea by dropping and recreating its own `pNN-*` table, so runs never interfere. The tables should be built from the same definition as production, ideally exported from our IaC (CDK, Terraform, CloudFormation).

DynamoDB Local isn't the only option:

| Tool                 | Good for                                     | Notes                                   |
|----------------------|----------------------------------------------|-----------------------------------------|
| **DynamoDB Local**   | realistic API behaviour, streams, PartiQL, transactions | official; Java/Docker              |
| **LocalStack**       | DynamoDB *plus* S3, Lambda, SQS, etc.        | wraps DynamoDB Local for DynamoDB       |
| **moto**             | fast in-process unit tests, no Docker        | `@mock_aws`; less faithful               |

### In practice

The script fails fast if the container isn't running, then runs two tests, each against a throwaway table:

```python
@contextmanager
def temp_table(prefix="p01-test"):
    name = f"{prefix}-{uuid.uuid4().hex[:8]}"
    table = ddb.create_table(TableName=name, ...)  # same definition as prod
    table.wait_until_exists()
    try:
        yield table
    finally:
        table.delete()


for test in (test_create_user, test_duplicate_user_rejected):
    with temp_table() as t:
        test(t)
        print(f"  PASS {test.__name__}  (table {t.name})")
```

```text
=== Connected to http://localhost:8000 ===
{
  "existing tables": 50
}

=== Running tests, each against its own throwaway table ===

>>> PutItem p01-test-c067a46e
    item:       {PK: 'USER#1', SK: 'PROFILE', name: 'Ada'}

>>> GetItem p01-test-c067a46e
    key:        {PK: 'USER#1', SK: 'PROFILE'}
  PASS test_create_user  (table p01-test-c067a46e)

>>> PutItem p01-test-4e1a63bc
    item:       {PK: 'USER#1', SK: 'PROFILE'}

>>> PutItem p01-test-4e1a63bc
    item:       {PK: 'USER#1', SK: 'PROFILE'}
    condition:  attribute_not_exists(PK)
  PASS test_duplicate_user_rejected  (table p01-test-4e1a63bc)

=== Test tables left behind ===
[]
```

Each test gets its own randomly named table, and the duplicate-user test passes because DynamoDB Local really does reject the conditional put. That's exactly the kind of behaviour a hand-written mock would miss. At the end, no test tables are left behind.

### Why

- **Fast and free.** No network round trip to AWS, and no bill.
- **Realistic.** It catches condition, key and index mistakes that hand-written mocks don't.
- **Isolated.** Unique tables per test mean parallel test runs don't interfere.

### Trade-offs

DynamoDB Local covers tables, indexes, streams, transactions and PartiQL. What it **doesn't** do matters just as much, and the patterns that need these features simulate them instead:

- There's no throttling or capacity limit, so performance looks better than reality ([38](../08-operations/#38--capacity-modes-on-demand-vs-provisioned), [16](../03-querying/#16--batch-operations-with-retries)).
- TTL never actually deletes items ([30](../06-lifecycle-and-events/#30--ttl-for-expiry)).
- There's no PITR or backups ([39](../08-operations/#39--point-in-time-recovery--backups)), no global tables ([40](../08-operations/#40--global-tables-multi-region)), no exports ([41](../08-operations/#41--analytics-outside-dynamodb)) and no DAX ([36](../07-performance-and-scale/#36--caching-dax--elasticache)).
- GSIs update immediately, so eventual-consistency bugs don't show up ([28](../05-consistency/#28--gsis-are-eventually-consistent)).

Because of this, keep a small integration suite that runs against a real AWS account in CI.

### Gotchas

- **`-sharedDb`:** without it, each access key + region combination gets a *separate* database. That leads to "my table disappeared" confusion when two tools use different dummy keys.
- `-inMemory` is faster for tests, but loses data on restart. `-dbPath` persists. This repo stores its data in `docker/dynamodb/`, which should be kept out of git.
- Region and credentials must still be set, even though their values are ignored.

With the vocabulary, the API and a local database in place, we're ready for the heart of DynamoDB: [modelling](../02-modelling/).

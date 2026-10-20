---
title: "DynamoDB patterns"
author: "James"
date: "2026-10-20"
summary: "43 DynamoDB design patterns, from key design to global tables, each with a runnable demo against DynamoDB Local."
hideBackToTop: true
tags: ["dynamodb", "aws", "databases", "data-modelling"]
draft: false
hideHeader: true
math: false
---

[Amazon DynamoDB](https://aws.amazon.com/dynamodb/) promises **single-digit-millisecond latency at any scale**. The catch is that it gets there by refusing to do anything slow: no joins, no ad-hoc queries, no query planner to save you. If you model a DynamoDB table like a relational one, it will work for a while, then get expensive, then get slow.

The way out is a small set of design patterns that come up again and again: prefixed keys, single-table design, overloaded indexes, conditional writes, write sharding and so on. This series goes through 43 of them, grouped into 9 topics. Each one is explained, run, and shown with the exact requests it sends to DynamoDB.

All the code can be found in my [dynamodb-patterns](https://github.com/jfgrea27/dynamodb-patterns) repository. Every pattern there is a short write-up (`.md`) plus a runnable Python demo (`.py`) that runs against **DynamoDB Local**, so you don't need an AWS account to follow along.

---

## How the repository works

The repo uses `docker compose` for DynamoDB Local, `uv` for Python dependencies and `just` as a task runner (a nix flake provides all three if you use `direnv`):

```sh
git clone https://github.com/jfgrea27/dynamodb-patterns && cd dynamodb-patterns
just setup          # uv sync + pull the DynamoDB Local image
just up             # start DynamoDB Local on localhost:8000
just run 4          # run pattern 04 (single-table design)
just read 4         # print its write-up
just run-all        # run every pattern and report failures
just down           # stop DynamoDB Local
```

Patterns are numbered in reading order, so each one only builds on those before it. They live in category folders: `patterns/<category>/NN-name/NN-name.{md,py}`.

A few things make the demos useful as a learning tool:

- **Every request is printed.** Each DynamoDB call is shown with its key condition, filter, condition and update expressions, with the real names and values substituted in. You see exactly what was sent, not just what came back.
- **Safe to re-run.** Each script drops and recreates its own `pNN-*` table.
- **Simulated where needed.** DynamoDB Local doesn't support S3, DAX, point-in-time recovery, global tables, table export or TTL deletion. Those lessons simulate the behaviour and show the real AWS call alongside.

For example, here is part of the output of `just run 4`. One `Query` fetches a user and all of their orders, newest first:

```text
>>> Query p04-single-table
    key:        (PK = 'USER#alice' AND begins_with(SK, 'ORDER#'))
    ScanIndexForward: False

=== Alice's orders, newest first ===
[
  {
    "SK": "ORDER#2026-10-15#o2",
    "total": 17,
    "PK": "USER#alice",
    "type": "Order"
  },
  {
    "SK": "ORDER#2026-10-01#o1",
    "total": 42,
    "PK": "USER#alice",
    "type": "Order"
  }
]
```

Every pattern in the series includes output like this, captured from a real run.

---

## The topics

| # | Topic | What it covers |
|---|---|---|
| 01 | [Intro & setup](01-intro-and-setup/) | What DynamoDB is, the basic API, and developing against DynamoDB Local |
| 02 | [Modelling](02-modelling/) | Designing partition keys, sort keys and indexes so every access pattern is a `GetItem` or `Query` |
| 03 | [Querying](03-querying/) | Reading efficiently: Scan vs Query, filters, pagination, projections, batches |
| 04 | [Item size & large data](04-item-size/) | Living with the 400 KB item limit and per-KB pricing |
| 05 | [Consistency & concurrency](05-consistency/) | Correct concurrent writes with conditions, transactions, idempotency and locks |
| 06 | [Lifecycle & events](06-lifecycle-and-events/) | TTL expiry, DynamoDB Streams and archival |
| 07 | [Performance & scale](07-performance-and-scale/) | Hot partitions, write sharding, caching and time-series data |
| 08 | [Operations](08-operations/) | Capacity modes, backups, multi-region and analytics |
| 09 | [What not to do](09-anti-patterns/) | The common mistakes, measured, and the pattern that fixes each one |

If you're new to DynamoDB, start with [01 - Intro & setup](01-intro-and-setup/). [Modelling](02-modelling/) is the heart of the series, and most later topics build on it.

## The mental model to carry forward

If you take only five things away from this series:

1. **Start from the access patterns.** Write down every question the app asks, then design keys so each one is a `GetItem` or a `Query`.
2. **Store data the way it is read.** Items fetched together share a partition key. Data needed on another item gets copied there.
3. **Spread the load.** Use high-cardinality partition keys so traffic and storage spread across partitions.
4. **Keep items small** and avoid `Scan` in request paths.
5. **Use conditions for correctness.** Atomic updates and conditional writes replace locks.

## Further reading

- Alex DeBrie, [*The DynamoDB Book*](https://www.dynamodbbook.com/)
- Rick Houlihan, AWS re:Invent, "Advanced design patterns for DynamoDB"
- The [DynamoDB developer guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- The original [Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) (2007)

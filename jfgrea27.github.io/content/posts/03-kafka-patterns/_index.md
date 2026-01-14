---
title: "Kafka: a practical exploration"
author: "James"
date: "2025-11-29"
summary: "Exploration of Kafka configurations."
hideBackToTop: true
tags: ["algorithms", "data-structures"]
draft: false
hideHeader: true
math: false
---

[Apache Kafka](https://kafka.apache.org/) has become the _de facto_ event streaming and processing platform in the industry.

This set of articles explores Kafka through practical experiments, both as a learning tool as well as a resource for anyone who land on this side. All the code can be found in my [kafka-patterns](https://github.com/jfgrea27/kafka-patterns) repository. This article will only show the screen recordings of the experiments, but you can ofcourse look at the code directly for each example by looking at the repository. The code is written in Java, the prefered language for Kafka applicatoins.

# Kafka in one paragraph

Kafka is an event streaming platform and stream processing platform.

In short, messages are send by producers to a topic in the Kafka cluster. The leader broker in the topic's replica set will save the message and replicate the data across the replicas. Ordering of messages in topics is not guaranteed, however, topics have partitions, where the ordering of message consumption in given partition in topic is guaranteed. Consumers are organised in consumer groups per topic. Each consumer in consumer group can be assigned one or more partitions to process. Consumers commit offsets to store their current progress in processing the messages.

Please refer to [Terminology](#terminology) for a quick summary of the nomeclature, or the Kafka documentation for more details.

# Kafka patterns

We will explore 5 patterns for now:

- [01 simple producer & consumer](#01-simple-producer--consumer);
- [02 topic partition in producer & consumer](#02-partition-producer--consumer);
- [03 ordering of messages in topics/partitions](#03-ordering-of-messages-in-partition)
- [04 partition vs throughput](#04---partition-vs-throughputparallelismscaling)
- [05 producer delivery semantics](#05---producer-delivery-semantics)
- [06 consumer delivery semantics](#06---consumer-delivery-semantics)

#### 01 - Simple producer & consumer

In this demo, we explore a very basic producer/consumer.

The producer will continuously send messages every 5 seconds (configurable with `SEND_INTERVAL_SECONDS`). The consumer will consume from broker. Press Ctrl+C to stop either application gracefully.
Here we see that the producer publishes messages to the `demo.topic` and these are picked up by the consumer.

<video src="01-simple-producer-consumer/demo.mov" controls title="Simple producer and consumer demo" style="max-width: 600px; display: block; margin: 0 auto;"></video>

You can see that messages are published to all partitions (0 and 1).
You can see that messages are consumed from all partitions (0 and 1).

#### 02 - Partition producer & consumer

In this demo, we explore the concept of [partitions](#partition) in Kafka. A given topic can be split into partitions. Messages are written to one partition, determined by their partition key.

We can define a `Partitioner` class that will generate a partition key for a given message. `ConstantPartitioner` will always send to `partition=0`.

<video src="02-partition-producer-consumer/demo.mov" controls title="Example of partitioned topics" style="max-width: 600px; display: block; margin: 0 auto;"></video>

As you can see, consumer consuming from partition 0 (top left) will receive all the message, whilst consumer consuming from partition 1 (bottom left) will receive none of the messages. This shows that consumers that subscribed to a specific partition will only read messages on that partition.

#### 03 - Ordering of messages in partition

As explained in [background](#background) section, messages are not guaranteed to be consumed in the right order in a given topic, but ordering is guaranteed in a partition in a topic is guaranteed.

We will use the same `Partitioner` class in [02 topic partition in producer & consumer](#02-partition-producer--consumer), but this time have the producer publish to both partitions. You should see that the ordering of the messages is preserved in each partition, namely, the monotonically incresing, although, a give partition may consume newer messages that were sent after messages in other partitions.

#### 04 - Partition vs {throughput,parallelism,scaling}

Tweaking the partition count per topic impacts throughput and parallelism

- Throughput: the smaller the partition, the more messages per partition, meaning broker has less resources to handle writes -> lower throughput.
- Parallelism: Each partition offers another degree of parallelism. More partitions -> more consumers can run in the consumer group, increasing parallelism.

Too many partitions can cause severe issues, including:

- Resource intensive on brokers: each partition requires resources (CPU, memory, IO, etc.).
- Failover slows: rebalancing load (e.g. consumer failure) take more time since Kafka coordinator needs to reallocate all partitions across replicas.

From the consumer's perspective, if a topic has several partitions spread across several brokers, the throughput is larger since the read load on the brokers wil be spread across the brokers.
From the producer's perspective, if a topic has several partitions spread across several brokers, the throughput is larger since the write load on the brokers will be spread across the brokers.

Overall the right level of partitioning is required to maximise scalability and speed of the Kafka application.

Below, we will run experiments with 1, 10 and 1000 partition(s) size topics, where a producer will publish as many messages as possible to the topic and then measure _consumer lag_. Consumer lag, the number of messages behind those published to partition, indicates whether consumers are keeping up producers. The consumers in this experiment will only run for 10 seconds from when their consume their first message.

We would expect that larger partition will reduce consumer lags.

Here are the [results](04-partitions-vs-throughput/results.csv) for each partition count:

<div style="display: flex; justify-content: center;">

| Topic      | Partitions | Total Lag | Average Lag |
| :--------- | :--------- | :-------- | :---------- |
| topic-1    | 1          | 4121      | 4121.00     |
| topic-10   | 10         | 3515      | 351.50      |
| topic-1000 | 1000       | 1478      | 1.48        |

</div>

As you can see, the average lag reduces with larger topics, which supports the theory on throughput and parallelism.

Creating 10000 topics crashes the container, which also supports the resource burden partitions cause.

#### 05 - Producer delivery semantics

As described in [delivery semantics](#delivery-semantics), there are 3 kinds of delivery semantics for the producer:

- At-least-once;
- At-most-once;
- Exactly-once.

In this section, we will look at delivery semantics from the perspective of the producer.

_At-leace-once_

The setup up for at-least-once semantic is as follows:

```
# producer setup
acks=all # waits all in-sync replicas (ISR) acknowledgement
retries>0 # retries if record is not sent
enable.idempotence=false # will not deduplicate messages if received twice
```

To simulate multiple same message sent, we will use [toxiproxy](https://github.com/Shopify/toxiproxy) to block acknowledgements:

<video src="05-producer-delivery-semantics/at-least-once-demo.mov" controls title="At-least-once delivery demo" style="max-width: 600px; display: block; margin: 0 auto;"></video>

Here is a demo where we set up simple producer/consumer, then add latency via the `toxiproxy`, then remove the latency and see that a consumer will consume the same message twice.

_At-most-once_

The setup for at-most-once semantic is as follows:

```
# producer setup
acks=0 # don't acknowledge, just send next message
retries=0 # don't retry if failed
```

We will apply the same simulation as for _at-least-once_ delivery semantic above but will see that no message is sent twice:
<video src="05-producer-delivery-semantics/at-most-once-demo.mov" controls title="At-most-once delivery demo" style="max-width: 600px; display: block; margin: 0 auto;"></video>

Here is a demo where we set up simple producer/consumer, then add droppage via the `toxiproxy`, then remove the latency and see that a consumer will have a gap between the messages in the topic, meaning some messages were not sent.

_Exactly-once_

The setup for exactly-once semantic is as follows:

```
# producer setup
acks=0 # don't acknowledge, just send next message
retries=0 # don't retry if failed
enable.idempotence=true # deduplicate messages if they arrive twice
transactional.id=demo-tx-1
```

Here we see that Kafka requires a transaction to apply exactly-once delivery semantics. This transaction allows producers to send messages atomically to one/more topics (a.k.a. all or nothing).

<video src="05-producer-delivery-semantics/exactly-once-demo.mov" controls title="Exactly-once delivery demo" style="max-width: 600px; display: block; margin: 0 auto;"></video>

As you can see, no message is dropped/delivered twice, regardless of the send/ack dropage simulated via toxiproxy.

Overall, this shows that different settings will impact delivery semantics. It is worth noting that depending on the application, a certain delivery semantic might be more suited. For example, low latency events like view clicks on a video most will probably not require accurate aggregate value, and so at-most-once delivery semantic is useful. Conversely, data analytics pipelines where crucial duplicate results can be cleaned up async will require at-least-once delivery semantics and finally exactly-once delivery semantics might be required in crucial cases such as financial transactions, where dropped or duplicate messages can be very costly. You must decide which delivery semantic makes most sense given the context.

At-most-once has the lowest overheads since no ack is required.
At least-once will require some acknowledgments, which increases overheads.
Exactly-once will require the most overhead since a transaction, idempotency, retries and acks are all required. This will have performance impacts, but are worth the trade off in crucial contexts.

#### 06 - Consumer delivery semantics

Consumers commit their progress as [offset](#offset). This offset dictates whether a given user has consumed the message. Crucially, how the application commits this offset will impact the delivery semantic from the consumer's perspective. There are 3 cases:

- At-most-once: Consumer will read the message, commit message consumed and then process it. If the consumer fails during processing, the consumer won't consume the message again when back up.
- At-least-once: Consumer will read the message, process it and then commit message consumed. If the consumer fails just after processing, the consumer will consume the message again since the offset was not committed.
- Exactly-once: Consumer will messages that have been committed in the transaction `read_committed`.

We will explore 3 demos for each case:

_At-most-once_

Here is the setup for at-most-once:

```
# consumer config
enable.auto.commit=true
auto.commit.interval.ms=5
```

We will set up a consumer that will read, commit and fail processing in a loop.

<video src="06-consumer-delivery-semantics/at-most-once-demo.mov" controls title="Consumer at-most-once delivery demo" style="max-width: 600px; display: block; margin: 0 auto;"></video>

As you can see, the consumer fails on every odd message, and it doesn't retry since it has already committed its consumption of these messages prior to processing them.

_At-least-once_

Here is the setup for at-most-once:

```
# consumer config
enable.auto.commit=false
```

We will set up a consumer that will read, commit and fail processing in a loop.

<video src="06-consumer-delivery-semantics/at-least-once-demo.mov" controls title="Consumer at-least-once delivery demo" style="max-width: 600px; display: block; margin: 0 auto;"></video>

As you can see, the consumer fails on every odd message, and it seeks to known offset and then rereads messages that have already been sent.

# Terminology

## _Topic_:

A category/feed where messages are published to. Order of messages in topics are **not guaranteed**, only within partition.

# _Broker_

A Kafka server that stores messages and serves them to clients. When a partition is replicated, one of the partition's replica broker is the leader broker. All messages are published to this broker and then replicated to the other brokers in the replication set. If the leader broker fails, new leader broker election is triggered.

## _Producer_

A client that sends messages to broker on a topic.

## _Consumer_

A client that reads messages from broker's topic.

## _Partition_

A subdivision of a topic. Order of messages in partition in a topic are guaranteed.

## _Consumer group_

A consumer group is made up of consumers that will subscribe to messages on a topic. Consumers are assigned one or more partitions in the topic and process events here. No two consumers will be assigned the same partitions to preserve ordering.

## _Offset_

Consumers consume messages and commit an offset. Replaying history is possible.

## _Replication_

A replication of a Kafka Broker.

## _Delivery Semantics_

Delivery semantics describes what guarantees a sender/receiver has when sending/receiver a record in Kafka.

Delivery semantics can be analysed from both the producer and consumer's perspective.

There are 3 kinds of delivery semantics:

- At-least-once semantic: messages are produced/consumed at least once, meaning duplicates sends/reads are possible.
  - Producer: Retries>0, Acknowledgement of message delivery to all brokers is expected from producer. Loss of ack might lead to duplicate message sent.
  - Consumer: If producer sends duplicates, consumer will consume more than once.
- At-most-once semantic: messages are produced/consumed at most once, meaning message might be read/send.
  - Producer: Retries=0, Acknowledgement of message delivery to all brokers is not expected from producer. If producer fails before leader ack, then no retry -> loss message.
- Exactly-once semantic: messages are produced/consumed exactly once.
  - Producer: Idempotent producer - same messages to partition on topic will be deduplicated.
  - Consumer: Complex set up, requires Kafka transactions (`isolation.level=read_committed`).

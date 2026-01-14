---
title: "Data Structures and Algorithms Patterns"
author: "James"
date: "2025-11-29"
summary: "Some general notes on DSA."
hideBackToTop: true
tags: ["algorithms", "data-structures"]
draft: false
hideHeader: true
math: true
---


With [Advent of Code 2025](https://adventofcode.com/) round the corner, I thought I'd refresh myself/go in more depth into some DSA patterns. What a better way that writting a blog post and publishing into the internet void!

This blog is a knowledge dump of certain patterns, tricks and in-depth data structures in Python.


# A quick recap on algorithmic complexity

Algorithmic performance broadly looks at two measurements:
- Time complexity: how much time an algorithm takes as its inputs scale.
- Space complexity: how much space an algorithm takes as its inputs scale.

We use the notion of $\Omicron(n)$ to define the complexity function given a set of inputs. 

The *Worst case $\Omicron(n)$* describes the maximum time/space an algorithm takes for *any* input. It is the **guaranteed upper bound**. 

The *Average case $\Omicron(n)$* describes the expected time across all posbbile inputs. It tells you what you **expect typically**.

For example, a hashmap that uses linked lists for handling key collisions will have an average case $\Omicron(1)$ lookup but a worst case $\Omicron(n)$ in case all entries hash to the same bucket.

For reference, the complexity function size order is
$$
\Omicron(1) \ll \Omicron(log N) \ll \Omicron(N) \ll \Omicron(N^k) \ll \Omicron(!N)
$$

Further, the largest component of the complexity function will override any smaller componets: e.g. $\Omicron(log N + N) \to \Omicron(N)$.


# Data Structures

Read or write operations on data may be significantly improved if the right data structure is chosen. 

In this section, we will explore fundamental data structures. I have implemented some of these in my [c-ds](https://github.com/jfgrea27/c-ds) repository, which includes implementation in C, with memory leaks checks etc. 

## Dynamic arrays
Arrays hold data in a contiguous block of memory. 

This makes scanning the array efficient since data is located next to one another. 

Data is indexed, meaning updates are fast.

When a dynamic array is full, a process of allocating more memory for the array is required. This often relies on requesting double the amount of memory and copying all existing elements into the new allocated memory. 
You can see this process in [my cvector implementation](https://github.com/jfgrea27/c-ds/blob/main/src/cvector/cvector.c#L25-L42).
As discussed in the [recap on complexity](#a-quick-recap-on-algorithmic-complexity) above, appending at end will have an average-case of $\Omicron(1)$ and a worst-case $\Omicron(n)$. We call this *ammortized* $\Omicron(1)$ (= when certain infrequent operations make other operations fast). 

Any insertions at a given index in the dynamic array will require shifting all elements after the inserted value


## Linked lists
Linked lists hold data in non-contiguous chains of points and values. To access the next element, one must look up its memory address, which won't necessarily be close to the current element in the list. 

Since elements are linked, inserting an element mid linked list is significantly cheaper than for [dynamic arrays](#dynamic-arrays).

## Hashmaps
Hashmaps store hashable data in a look-up table that has $\Omicron(1)$ time complexity. 

Whenever an element is added to the hashmap, we take its hash via hash function and then insert it into the underlying look-up table of the hashmap's entry, also called **bucket**. 

It is possible that a hash function outputs the same hash for two distinct values. We call this a **hash collision**. Here are two ways for dealing with hash collisions:

- **Linked list**: each bucket contains the start node of a linked list. If two elements hash to the same bucket, we append the element in the link list. Whenever we want to look up one of these element in the dict, we hash the element, find the relevant bucket and then walk down the linked list until we find the element who's key matches the one we are looking for. 
- **Probing**: if a hash for an element outputs a bucket that is already full, find the next available bucket and insert the element there. When we read the element, we cycle through over buckets that are part of the probe chain until we find the bucket with the entry that matches the key we are looking for.

Generally, a hashmap is an array (either fix size if using linked-list for collisions or [dynamic array](#dynamic-arrays) if using probing as the array might get full. 

There are advantages to using both linked lists and dynamic arrays for collisions. 
Dynamic arrays have contiguous memory locations, making them fast to look up in case of collisions. 
Linked lists will allow for much larger collisions, with no need to resizing the dynamic array in the probing case.

## Trees 
TODO 

## Python

### `list`
Python `list` data structure is a [dynamic array](#dynamic-array) under the hood. The following are some relevant operations:

<div style="display: flex; justify-content: center;">

| Operation      | Time Complexity    |
| -------------- | ------------------ |
| `append(x)`    | **O(1) amortized** |
| `insert(i, x)` | **O(n)**           |
| `lst[i]`       | **O(1)**           |

</div>

This is consistent with what we discussed in the dynamic array section. 

### `dict`/`set`
Python `dict` or `set` are [hashmaps](#hashmaps) under the hood that use **probing** for hash collisions.

<div style="display: flex; justify-content: center;">

| Operation                        | Time Complexity |
|----------------------------------|-----------------|
| `d[key] = value` (insert/update) | **O(1) amortized**  |
| `d[key]` (read)                  | **O(1) amortized**  |
| `del d[key]`                     | **O(1) amortized**  |
| `key in d`                       | **O(1) amortized**  |
| `d.get(key)`                     | **O(1) amortized**  |

</div>

As discussed, probing will handle collisions by adding the element to the next bucket. Since the dynamic array under the hood can become full, rehashing and copying over all the elements of the hashmap may occur. This is why we see ammortized operations

This is consistent with what we discussed in the dynamic array section. 

### Strings
It is worth noting that in Python, `str` is **immutable**, meaning we copy the entire string everytime we add/remove a character. Hence, it is best not to do operations directly on strings but rather convert them to arrays first, which are of course **mutable**. 

# Algorithm tricks

This section describes algorithm tricks and patterns that may be relevant

## Arrays

Here is a brain-dump of tricks with arrays which might be useful. You can also see the kinds of problems the tricks are good for. 

### Two-pointers

Idea: TODO

**Opposite end pointers**
```py
def fn(arr):
    left = ans = 0
    right = len(arr) - 1

    while left < right:
        # do some logic here with left and right
        if CONDITION:
            left += 1
        else:
            right -= 1
    
    return ans
```

Time complexity: $\Omicron(N)$

When to use?
TODO

**Same end pointers**

Idea: TODO 
```py
def fn(arr1, arr2):
    i = j = ans = 0

    while i < len(arr1) and j < len(arr2):
        # do some logic here
        if CONDITION:
            i += 1
        else:
            j += 1
    
    while i < len(arr1):
        # do logic
        i += 1
    
    while j < len(arr2):
        # do logic
        j += 1
    
    return ans

```

Time complexity: $\Omicron(N)$

When to use?
TODO

### Sliding window

Idea: TODO 

```py
def fn(arr):
    left = ans = curr = 0

    for right in range(len(arr)):
        # do logic here to add arr[right] to curr

        while WINDOW_CONDITION_BROKEN:
            # remove arr[left] from curr
            left += 1

        # update ans
    
    return ans
```

Time complexity: $\Omicron(N)$

When to use?
TODO


### Prefix sum

Idea: Calculate some up to index i ahead of other parts of the solution to save calculating every time. 

```py
def fn(arr):
    prefix = [arr[0]]
    for i in range(1, len(arr)):
        prefix.append(prefix[-1] + arr[i])
    
    return prefix
```

Time complexity: $\Omicron(N)$

When to use?
TODO



## Linked lists

### Fast and slow pointers

```py
def fn(head):
    slow = head
    fast = head
    ans = 0

    while fast and fast.next:
        # do logic
        slow = slow.next
        fast = fast.next.next
    
    return ans
```

### Reverse linked list

```py
def fn(head):
    curr = head
    prev = None
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node 
        
    return prev
```


## Stacks and queues
TODO
## Heaps
TODO
## Greedy
TODO


## BFS/DFS

```py
def dfs(root):
    if not root:
        return
    
    ans = 0

    # do logic
    dfs(root.left)
    dfs(root.right)
    return ans
```

```py
def dfs(root):
    stack = [root]
    ans = 0

    while stack:
        node = stack.pop()
        # do logic
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)

    return ans
```
## Backtracking
TODO

## Famous algorithms
TODO






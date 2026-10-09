---
title: "Linux I/O models"
author: "James"
date: "2026-10-09"
summary: "The five ways a Linux process can wait for data, explored through small C programs and strace."
hideBackToTop: true
tags: ["linux", "c", "io", "io_uring"]
draft: false
hideHeader: true
math: false
---

Every time you `await` something in Python, spawn a goroutine in Go, or write a Tokio handler in Rust, something underneath has to answer a simple question: **what does my process do while the data isn't there yet?**

Linux gives you 5 answers to that question, the 5 I/O models:

1. **Blocking I/O**: the process sleeps until the data is ready.
2. **Non-blocking I/O**: the call returns immediately and the caller busy loops/polls for results.
3. **I/O multiplexing**: one thread waits on many **File Descriptors (FD)**.
4. **Signal-driven I/O**: the kernel raises a signal when an FD is ready.
5. **Asynchronous I/O**: the kernel notifies on completion.

This article goes through each of them with small C programs, and uses `strace` to see what is really happening between the process and the kernel. All the code can be found in my [lowlevel](https://github.com/jfgrea27/lowlevel/tree/main/learnings/linux-io-models) repository. The examples were run on Linux (an `aarch64` VM), so if you're on macOS you'll need a VM or container to follow along.

---

## File descriptors

I/O is the process of reading & writing data, to a file, a stream or a socket. Each Linux process keeps track of which of these are open in its **File Descriptor Table**.

Initially, a process has 3 FDs: `stdin`, `stdout` and `stderr`. You can inspect a process' FDs through `/proc/<PID>/fd/*` (or `/proc/self/fd/*` from within the process).

Let's take a very simple [fd-demo](https://github.com/jfgrea27/lowlevel/blob/main/learnings/linux-io-models/00-fd-demo/main.c):

```c
// 00-fd-demo/main.c
#include <stdio.h>

int main(void)
{
    char line[256];

    // stdin/stdout/stderr
    fgets(line, sizeof line, stdin);
    printf("out: %s", line);
    fprintf(stderr, "err: %s", line);

    // adding an fd:
    FILE *log = fopen("log.txt", "w");
    fprintf(log, "log: %s", line);
    fclose(log);

    return 0;
}
```

Let's compile it and step through it with `gdb`:

```sh
cd 00-fd-demo
gcc -g main.c -o main # note the -g is for debugging.

gdb ./main
```

```txt
(gdb) info proc
(gdb) run
(gdb) n
...
# before fopen
(gdb) shell ls -l /proc/PID/fd
lrwx------ 1 user group 64 Oct  6 09:41 0 -> /dev/pts/0
lrwx------ 1 user group 64 Oct  6 09:41 1 -> /dev/pts/0
lrwx------ 1 user group 64 Oct  6 09:41 2 -> /dev/pts/0
(gdb) n
# after fopen
(gdb) shell ls -l /proc/PID/fd
lrwx------ 1 user group 64 Oct  6 09:25 0 -> /dev/pts/0
lrwx------ 1 user group 64 Oct  6 09:25 1 -> /dev/pts/0
lrwx------ 1 user group 64 Oct  6 09:25 2 -> /dev/pts/0
l-wx------ 1 user group 64 Oct  6 09:41 3 -> /path/to/linux-io-models/00-fd-demo/log.txt
(gdb) n
...
# after fclose
(gdb) shell ls -l /proc/PID/fd
lrwx------ 1 user group 64 Oct  6 09:41 0 -> /dev/pts/0
lrwx------ 1 user group 64 Oct  6 09:41 1 -> /dev/pts/0
lrwx------ 1 user group 64 Oct  6 09:41 2 -> /dev/pts/0
```

As you can see, a new FD (`3`) is recorded in the process when we open the file, and removed once we close it. FDs `0`, `1` and `2` are `stdin`, `stdout` and `stderr`, all pointing at the terminal (`/dev/pts/0`).

Everything that follows is about how a process waits on one (or many) of these FDs.

---

## 1. Blocking I/O

**TLDR;** the process is blocked during I/O.

System calls: `read()` and `write()`. This is the default.

Under the hood, the thread sleeps until the data has been copied from kernel space into the user space buffer.

Let's look at an [example](https://github.com/jfgrea27/lowlevel/blob/main/learnings/linux-io-models/01-blocking-io/main.c). Here, the important line is:

```c
// ...
    ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
// ...
```

This reads from the `stdin` FD into the empty buffer `buf`.

To make the wait visible, we pipe in `(sleep 3; echo hi)`, which:

1. sleeps for 3s, then
2. echoes "hi", then
3. pipes the "hi" into our `./main`.

Our program starts straight away, but can only read the data once it is in the pipe:

```sh
# compile
gcc -O0 main.c -g -o main
# inspect
(sleep 3; echo hi) | strace -T -e trace=read,fcntl ./main
# output:
# read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0\267\0\1\0\0\0\360\206\2\0\0\0\0\0"..., 832) = 832 <0.000122>
## sleeps for 3 seconds
# read(0, "hi\n", 4096)                   = 3 <2.996911>
# read 3 bytes
# +++ exited with 0 +++
```

(The first `read(3, "\177ELF...")` is just the dynamic loader reading `libc`, you'll see it in every example.)

The `-T` flag shows the time spent in each syscall: `<2.996911>`. The main thread was stuck inside `read()` for the full 3 seconds, unable to do anything else.

---

## 2. Non-blocking I/O

**TLDR;** the process is not blocked during I/O, but has to keep asking.

System calls: `read()` and `write()`, with the additional `O_NONBLOCK` flag set on the FD.

Under the hood, if the data isn't ready, `read()` returns straight away with an error. The thread can then do some work and poll the kernel again later.

Let's look at an [example](https://github.com/jfgrea27/lowlevel/blob/main/learnings/linux-io-models/02-non-blocking-io/main.c). Here, the important lines are:

```c
    // adding the flags including `O_NONBLOCK`.
    int fl = fcntl(0, F_GETFL);
    fcntl(0, F_SETFL, fl | O_NONBLOCK);

// ...
    for (int tries = 0;; tries++) {
        ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
        // ...
        if (errno != EAGAIN)
        {
            perror("read");
            break;
        }
        usleep(1000); // busy doing work.
        // ...
    }
// ...
```

This time, with the same `(sleep 3; echo hi)`, the main thread is not blocked (it can do work):

```sh
# compile
gcc -O0 main.c -g -o main
# inspect
(sleep 3; echo hi) | strace -T -e trace=read,fcntl ./main
# output:
# read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0\267\0\1\0\0\0\360\206\2\0\0\0\0\0"..., 832) = 832 <0.000073>
# fcntl(0, F_GETFL)                       = 0 (flags O_RDONLY) <0.000077>
# fcntl(0, F_SETFL, O_RDONLY|O_NONBLOCK)  = 0 <0.000076>
# read(0, 0xffffc4190c88, 4096)           = -1 EAGAIN (Resource temporarily unavailable) <0.000047>
# read(0, 0xffffc4190c88, 4096)           = -1 EAGAIN (Resource temporarily unavailable) <0.000063>
# ... 3 seconds worth of these.
# read(0, 0xffffc4190c88, 4096)           = -1 EAGAIN (Resource temporarily unavailable) <0.000046>
# read(0, 0xffffc4190c88, 4096)           = -1 EAGAIN (Resource temporarily unavailable) <0.000065>
# read(0, "hi\n", 4096)                   = 3 <0.000182>
# got 3 bytes after 29 tries
# +++ exited with 0 +++
```

We now get an `EAGAIN` error code, which means "nothing here yet, try again". Each `read()` takes microseconds instead of seconds, so the thread is free between calls.

The flow for the program is:

1. Is there some data to consume? No, go to step 2; Yes, go to step 4.
2. Do something else for X amount of time.
3. Go to step 1.
4. Consume the data available.

Here the main thread acts as its own event loop. The catch: every one of those `EAGAIN`s is a syscall, and syscalls are expensive. Poll too often and you burn CPU; poll too rarely and you add latency.

---

## 3. I/O multiplexing

**TLDR;** block, but on many FDs at once.

System calls: `select()`, `poll()`, `epoll_wait()`.

Multiplexing takes [1. Blocking I/O](#1-blocking-io) and applies it to many FDs. Rather than blocking inside `read()`, we block inside `poll()`, which tells us which FD is ready. Then, the `read()` on that FD is guaranteed not to block.

`poll` takes a list of `pollfd`:

```c
struct pollfd {
    int   fd;         /* file descriptor */
    short events;     /* requested events */
    short revents;    /* returned events */
};
```

`events` goes from user to kernel space ("tell me when this happens"), and `revents` (r = returned) goes from kernel to user space ("this is what happened"). Have a look at `man 2 poll` for all the event types.

Let's look at an [example](https://github.com/jfgrea27/lowlevel/blob/main/learnings/linux-io-models/03-multiplexing-io/main.c). Here, the important lines are:

```c
    // define a list of pollfds
    struct pollfd fds[MAX_FDS];
    // open the file descriptors
    for (int i = 0; i < nfds; i++)
    {
        fds[i].fd = open(argv[i + 1], O_RDONLY);
        // ...
        fds[i].events = POLLIN; // tell me when it's readable
    }

    while (remaining > 0)
    {
        // Sleep until at least one fd is ready (-1 = no timeout)
        int ready = poll(fds, nfds, -1);
        // ...
        for (int i = 0; i < nfds; i++)
        {
            if (!(fds[i].revents & (POLLIN | POLLHUP | POLLERR)))
                continue; // this one isn't ready

            char buf[4096];
            ssize_t n = read(fds[i].fd, buf, sizeof buf); // won't block: poll said ready
            if (n > 0)
            {
                printf("source %d: %.*s", i, (int)n, buf);
            }
            else
            { // 0 = EOF (or error): stop watching it
                close(fds[i].fd);
                fds[i].fd = -1; // poll ignores negative fds
                remaining--;
            }
        }
    }
```

The flow is:

1. Register the file descriptors.
2. `poll` the kernel. This blocks until at least one FD is ready.
3. Read from the ready FDs. This won't block since the data has arrived (as signalled by step 2).

With [1. Blocking I/O](#1-blocking-io), running 2 I/O operations in a single thread runs them sequentially. With multiplexing, they run concurrently. Let's feed in a slow source (3s) and a fast one (1s):

```sh
# compile
gcc -O0 main.c -g -o main
# inspect
time strace -T -e trace=read,ppoll ./main <(sleep 3; echo slow) <(sleep 1; echo fast)

# read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0\267\0\1\0\0\0\360\206\2\0\0\0\0\0"..., 832) = 832 <0.000116>
# ppoll([{fd=3, events=POLLIN}, {fd=4, events=POLLIN}], 2, NULL, NULL, 0) = 1 ([{fd=4, revents=POLLIN}]) <0.995887>
# read(4, "fast\n", 4096)                 = 5 <0.000010>
# source 1: fast
# ppoll([{fd=3, events=POLLIN}, {fd=4, events=POLLIN}], 2, NULL, NULL, 0) = 1 ([{fd=4, revents=POLLHUP}]) <0.000052>
# read(4, "", 4096)                       = 0 <0.000087>
# ppoll([{fd=3, events=POLLIN}, {fd=-1}], 2, NULL, NULL, 0) = 1 ([{fd=3, revents=POLLIN}]) <1.998587>
# read(3, "slow\n", 4096)                 = 5 <0.000037>
# source 0: slow
# ppoll([{fd=3, events=POLLIN}, {fd=-1}], 2, NULL, NULL, 0) = 1 ([{fd=3, revents=POLLHUP}]) <0.000047>
# read(3, "", 4096)                       = 0 <0.000046>
# +++ exited with 0 +++

# real    0m3.009s
# user    0m0.001s
# sys     0m0.014s
```

The whole thing takes **3 seconds, not 3 + 1 seconds**: the two waits overlap.

Reading the trace: the first `ppoll` wakes up after ~1s with FD 4 (`fast`) ready. The next `ppoll` returns `POLLHUP` (hang up, no more data) for FD 4, so we close it. The last `ppoll`s wait the remaining ~2s for FD 3 (`slow`).

One drawback of `select`/`poll` is that every call hands the kernel the full list of FDs, and the kernel (and then your program) scans all of it to find the ready ones: `O(N)` per call. This is fine for a handful of FDs, but not for a server with 10k connections. That's what `epoll` fixes: you register FDs once, and `epoll_wait` only returns the ones that are ready. It's the same model, just scalable, and it's what most runtimes use under the hood (more on that [below](#so-what-does-my-higher-level-language-use)).

---

## 4. Signal-driven I/O

**TLDR;** the kernel interrupts the process when an FD is ready.

System calls: `sigaction()` and `fcntl()` with `F_SETOWN` and `O_ASYNC`.

In both [2. Non-blocking I/O](#2-non-blocking-io) and [3. I/O multiplexing](#3-io-multiplexing), the caller (user space) asks the kernel whether data is ready. What if we flip it, and let the kernel signal the user space program instead?

This is what signal-driven I/O looks like.

Let's look at an [example](https://github.com/jfgrea27/lowlevel/blob/main/learnings/linux-io-models/04-signal-driven-io/main.c). Here, the important lines are:

```c
    // 1. Install a handler for SIGIO
    struct sigaction sa = {0}; // set the sigaction struct to default 0s.
    sa.sa_handler = on_sigio;  // call on_sigio when the signal arrives (callback)
    sigemptyset(&sa.sa_mask);  // don't block any other signals while in the handler.
    sigaction(SIGIO, &sa, NULL); // wire up SIGIO to the handler.

    // 2. Tell the kernel which process gets the signal
    fcntl(STDIN_FILENO, F_SETOWN, getpid());

    // 3. Turn on signal-driven mode (plus non-blocking, so draining can't hang)
    int flags = fcntl(STDIN_FILENO, F_GETFL);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_ASYNC | O_NONBLOCK);
```

The remaining code does some "work" in a loop and, once the handler has flagged that data is ready, reads it into a buffer.

```sh
# compile
gcc -O0 main.c -g -o main
# inspect
(sleep 3; echo hi) | strace -T -e trace=read,fcntl ./main

# read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0\267\0\1\0\0\0\360\206\2\0\0\0\0\0"..., 832) = 832 <0.000050>
# fcntl(0, F_SETOWN, 25191)               = 0 <0.000099>
# fcntl(0, F_GETFL)                       = 0 (flags O_RDONLY) <0.000150>
# fcntl(0, F_SETFL, O_RDONLY|O_NONBLOCK|FASYNC) = 0 <0.000076>
## 3 seconds of work, no syscalls
# --- SIGIO {si_signo=SIGIO, si_code=SI_KERNEL} ---
# --- SIGIO {si_signo=SIGIO, si_code=SI_KERNEL} ---
# read(0, "hi\n", 4096)                   = 3 <0.000345>
# got 3 bytes after 29 units of work: hi
# read(0, "", 4096)                       = 0 <0.000152>
```

Compare this with [2. Non-blocking I/O](#2-non-blocking-io): the same 29 units of work, but no wall of `EAGAIN`s. The process makes no syscalls while it waits, and the kernel delivers a `SIGIO` when the pipe has data (and again when the writer closes it, hence the two signals).

Sounds great, so why is it so rarely used? Signals are awkward to program with: the handler can interrupt your code at any point, you can only safely do a handful of things inside it, and a `SIGIO` doesn't tell you *which* FD is ready. With many FDs, you're back to checking each one.

---

## 5. Asynchronous I/O

**TLDR;** hand the whole I/O operation to the kernel, and collect the result once it's done.

System calls: `io_uring_setup()`, `io_uring_enter()` (usually via `liburing`).

Since version 5.1 of the kernel, a newer asynchronous model for I/O is available: `io_uring`.

The core idea relies on two ring buffers shared between user space and the kernel:

```txt
 user space                         kernel
 ┌──────────────────────┐
 │ Submission Queue (SQ)│ ──────▶  picks up SQEs, does the I/O
 │  [sqe][sqe][sqe]...  │
 └──────────────────────┘
 ┌──────────────────────┐
 │ Completion Queue (CQ)│ ◀──────  writes a CQE when each op finishes
 │  [cqe][cqe]...       │
 └──────────────────────┘
```

User space adds a **Submission Queue Entry (SQE)** to the SQ, and is notified of its result through a **Completion Queue Entry (CQE)** in the CQ.

An SQE reads like "read FD X into buffer Y, length N, offset Z". Adding one is not a syscall: the request is just written into the shared buffer. A CQE holds what the equivalent syscall would have returned (e.g. the number of bytes read).

Let's look at an [example](https://github.com/jfgrea27/lowlevel/blob/main/learnings/linux-io-models/05-asynchronous-io/main.c). Here, the important lines are:

```c
#include <liburing.h> // the library used for io_uring.

int ret = io_uring_queue_init(8, &ring, 0); // set up the ring with 8 entries in the submission queue.

// get a free entry in the submission queue so that we can fill in the request
struct io_uring_sqe *sqe;
sqe = io_uring_get_sqe(&ring);
// prepare the request - which fd, where to save it, what offset.
io_uring_prep_read(sqe, file_fd, file_req.buf, sizeof file_req.buf, 0); // offset 0
// attach our own pointer, which comes back in the CQE
io_uring_sqe_set_data(sqe, &file_req);

// we can queue multiple requests at once (up to the 8 entries from initialisation).
// In the example, we queue one for stdin and one for a file.

// submit everything in one go
io_uring_submit(&ring);

// do work, collect results as they arrive
int done = 0;
long work = 0;
while (done < 2) {
    struct io_uring_cqe *cqe;
    while (io_uring_peek_cqe(&ring, &cqe) == 0) {
        // ...

        printf("%s done after %ld units of work: %d bytes: %.*s\n",
               r->name, work, cqe->res, cqe->res, r->buf);

        // ...
        io_uring_cqe_seen(&ring, cqe); // mark the completion as consumed
        done++;
    }
    usleep(100000); // stand-in for real work
}
// tear down the ring.
io_uring_queue_exit(&ring);
close(file_fd);
```

Here we:

1. Prepare and submit multiple I/O requests to the SQ.
2. Do busy work whilst the kernel does the I/O.
3. Consume the results from the CQ.

By default, the CQ has twice as many entries as the SQ (you'll see `cq_entries=16` below).

```sh
# add the liburing library if not there
sudo apt install liburing-dev -y
# compile
gcc -O0 main.c -g -o main -luring
# inspect
(sleep 3; echo hi) | strace -T -e trace=io_uring_setup,io_uring_enter,mmap,read ./main

# ...
## setting up io_uring
# io_uring_setup(8, {flags=0, sq_thread_cpu=0, sq_thread_idle=0, sq_entries=8, cq_entries=16, features=IORING_FEAT_SINGLE_MMAP|IORING_FEAT_NODROP|...}) = 3 <0.000110>

## mapping the rings into shared memory
# mmap(NULL, 352, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_POPULATE, 3, 0) = 0xfdfbb2347000 <0.000046>
# mmap(NULL, 512, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_POPULATE, 3, 0x10000000) = 0xfdfbb2346000 <0.000044>
## submit both requests in a single syscall
# io_uring_enter(3, 2, 0, 0, NULL, 8)     = 2 <0.000150>
# file done after 1 units of work: 6 bytes: foobar
## 3 seconds of work, no syscalls
# pipe done after 29 units of work: 3 bytes: hi
```

Notice what's missing: there is no `read()` on the pipe at all. A single `io_uring_enter` submits both requests, and then the results just... appear.

How does this work without a syscall to fetch the data?

`io_uring` uses `mmap`, which creates a new mapping in the virtual address space of the process. Here, the two `mmap` calls on FD 3 (the ring) map the SQ and CQ into memory that **both** the process and the kernel can see. Once mapped, the process reads CQEs straight from memory, no syscall required.

(A note on `mmap`: the first touch of a page causes a page fault in the kernel, but once the page is in memory, there are no more syscalls. `MAP_POPULATE` above pre-faults the pages so even that is avoided.)

So why would you not use `io_uring`?

- **Portability**: it's Linux only. On macOS the closest equivalent is `kqueue`, so you'd need per-platform code.
- **Security**: `io_uring` is a big new kernel surface, and privilege-escalation bugs in it are still found regularly. Google, for instance, has disabled it on Android and ChromeOS.

So when should you use `io_uring`? When I/O volume is very high, and syscall/thread overheads are a real bottleneck.

---

## So what does my higher level language use?

You'll rarely write any of the above by hand. Here's what the common languages/frameworks do for you:

| Language / framework | 1. Blocking | 2. Non-blocking | 3. Multiplexing | 4. Signal-driven | 5. Asynchronous (`io_uring`) |
|---|---|---|---|---|---|
| **Python** (plain `socket`, `open`) | default for sockets & files | opt-in: `sock.setblocking(False)` | opt-in: `selectors` / `select` module | ✗ | ✗ |
| **Python** (`asyncio`) | files, via `asyncio.to_thread` (thread pool) | sockets set non-blocking internally | sockets: `selectors` → `epoll` | ✗ | ✗ (third-party only) |
| **Go** | files, the runtime moves the blocked thread aside | all network fds set non-blocking internally | network "netpoller" → `epoll` (goroutines *look* blocking) | ✗ | ✗ (third-party only) |
| **Rust** (`std`) | default for sockets & files | opt-in: `set_nonblocking(true)` | ✗ (needs a crate) | ✗ | ✗ |
| **Rust** (Tokio) | `tokio::fs`, via `spawn_blocking` thread pool | sockets set non-blocking internally | sockets: `mio` → `epoll` | ✗ | separate runtimes: `tokio-uring`, `glommio`, `monoio` |
| **Node.js** (libuv) | files, via libuv thread pool | sockets set non-blocking internally | sockets: `epoll` | ✗ | ✗ by default |
| **Java** | classic `java.io` | NIO channels | NIO `Selector` → `epoll` (virtual threads build on it) | ✗ | Netty io_uring transport |
| **nginx / Redis** | ✗ | sockets | `epoll` event loop | ✗ | ✗ |

Takeaways:

- On Linux, almost everything runs **non-blocking sockets + `epoll`** for the network, and a **thread pool of blocking calls** for files (`epoll` can't help with regular files: they always report "ready").
- Signal-driven I/O is essentially unused by runtimes.
- `io_uring` is completion-based (the kernel owns your buffer until the CQE arrives), which doesn't fit APIs designed around readiness (`epoll`). Hence it lives in separate, opt-in libraries.

---

## Closing remarks

All five models answer the same question: **what does my process do while the data isn't there yet?**

1. **Blocking:** sleep inside `read()`.
2. **Non-blocking:** keep asking (`EAGAIN`, `EAGAIN`, `EAGAIN`...), burning CPU.
3. **Multiplexing:** sleep in one place (`poll`/`epoll`) on behalf of *many* FDs, then `read()` the ready ones.
4. **Signal-driven:** get on with other work, let the kernel interrupt you with `SIGIO`, then `read()`.
5. **Asynchronous:** hand the whole `read()` to the kernel, and pick up the result from shared memory.

Each step moves a bit more of the work from the process to the kernel. Models 1-4 tell you when you **can** read (readiness). Only `io_uring` tells you the read **has happened** (completion).

`strace` made the difference visible every time: the 3-second wait moved from a blocking `read(0, ...) <2.99>`, to a stream of `EAGAIN` retries, to a single `ppoll`, to a `SIGIO`, and finally to no `read()` at all.

Python's `asyncio`, Go's goroutines, Tokio and Node all wrap model 3 (`epoll`) plus a thread pool for files, and `io_uring` stays an opt-in for disk-heavy software like databases. Knowing what sits underneath still pays off: when something hangs, spins at 100% CPU, or just seems slow, `strace -T` will usually show you which of these five models you're really running.

---
title: "01 - Types of TEEs"
author: "James"
date: "2025-08-26"
summary: "A whistle stop tour of the types of TEEs."
tags: ["tee", "privacy"]
draft: false
hideHeader: true
---

Trusted Execution Environments are special pieces of hardware that encrypt data in-use so to prevent attackers from compromising running applications.

Hardware providers including ARM, Intel and AMD have built various TEE solutions that depend on the scope of the [**Trusted Computing Base**](#trusted-computing-base).

- Intel's Secure Guard Extension (SGX)
- AMD Secure Encrypted Virtulization with Secure Nested Paging (SEV-SNP)
- ARM TrustZone
- Confidential Computing (CoCo)

For the sake of scope reduction, I will only explore Intel's SGX, AMD's SEV-SNP and CoCos, going from smallest TCB to largest TCB.

## The TEE Zoo

For each TEE solution, we will discuss

- its Architecture;
- its Remote Attestation framework;
- an example of a working TEE;
- its use-cases.

### Intel SGX

**Architecture**

The SGX architecture relies on creating a reserved region of memory, the **Enclave Page Cache** that holds encrypted data that is protected by a hardware-derived key (the **Root Sealing Key (RSK)**) that only resides in a secure CPU register.
SGX also adds a set of instructions (including `ECREATE`, `EENTER`, `EEXIT`) to manage the enclave.
The **Memory Encryption Engine (MEE)** built into the memory controller is responsible for the encryption/decryption of the data.

No one, not even the root has access to the EPC in DRAM. Further, data is only decrypted inside the CPU, so L1/L2/L3 caches still hold encrypted data. The MEE encrypts/decrypts data on-the-fly, which has some performance overhead.

The control flow works as follows:

1. Enclave is created using `ECREATE`;
2. Data is loaded using `EADD`;
3. Enclave is initialized using `EINIT`;
4. Enter the enclave using `EENTER`;
5. Run _trusted function_;
6. Exit the enclave using `EEXIT`.

[Remote Attestation](#remove-attestation) in SGX is done as follows:

**Example - a minimal SGX enclave**

This example is a basic application running an enclave using the [sgx-linux](https://github.com/intel/linux-sgx) repository.

We will assume you have installed `Intel SGX SDK` and `Intel SGX PSW`.

> **_NOTE:_** I had some difficulties installing SGX Linux on my Ubuntu 24.04 box. [This article](https://codentium.com/setting-up-intel-sgx/) was very useful

I have created a [minimal-sgx-enclave](https://github.com/jfgrea27/minimal-sgx-enclave) for exploring SGX internals.

```sh
git clone git@github.com:jfgrea27/minimal-sgx-enclave.git
# build
make
# run
./app
```

You have ran your first enclave!

The repository explores SGX more in depth including:

- [SGX Ergonomics](https://github.com/jfgrea27/minimal-sgx-enclave/blob/main/README.md#sgx-ergonomics)
- [Assembly calls](https://github.com/jfgrea27/minimal-sgx-enclave/blob/main/README.md#assembly-calls)
- [Remote Attestation](https://github.com/jfgrea27/minimal-sgx-enclave/blob/main/README.md#sgx-ergonomics)

**Discussion**

As we have detailed in SGX's architecture above, the system relies on a very small TCB that includes the CPU and its microcode. Data is always stored in EPC (encrypted), which limits SGX use-cases to small applications, although Azure do provide some of their DCdsv3 series with up to 256GiB of EPC, as noted [here](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dcdsv3-series?tabs=sizebasic#sizes-in-series).

It is worth noting that SGX are not fully immune.
TODO TALK ABOUT THE TYPES OF ATTACKS vulenrable to side-channel attacks - cache timing, page fault patterns.

A typical use case for using SGX Intel as TEE would be smallish applications that require small trust - for instance a cryptographic key/password store.

### AMD SEV-SNP

**Architecture**

<!--
- Guest VM full memory is encrypted

- Limitations

  - Attacks inside Guest OS still possible

- when to use

  - cloud deployments where customers don't trust the cloud provider

- Atestation -> what it measures -->

**Example - Deploying a TEE on a Cloud provider**

- build a simple postgres DB running in VM.

**Discussion**

### Confidential Containers

**Architecture**

**Example - K8S meets TEEs**

**Discussion**

## Lexicon

### Guest vs Host OS

In the context of Virtual Machines (VMs), we distinguish Guest OS running the application inside the virtualized hardware from Host OS running the hypervisor.

In Type-1 hypervisors (or _bare-metal hypervisor_), there is no such Host OS.

In Type-2 hypervisor, there is a Host OS that runs the hypervisor amongst other applications.

Most cloud providers predominantly deploy applications in VMs running [Type-1 hypervisor](https://en.wikipedia.org/wiki/Hypervisor), as illustrated below

![alt text](/posts/01-genai-and-tee/01-types-of-tees/hypervisor-types.svg "Types of hypervisor - (Wikipedia)")

As a contrast, if you were to run a VM on your laptop, this would be a Type-2 hypervisor as your laptop OS is running the hypervisor (and guest OS) as well as other applications (like browser, etc.).

### Trusted Computing Base

The **Trusted Computing Base (TCB)** is the set of hardware, firmware and software components that must be trusted to enforce the security properties of a system. If any part of the TCB is _compromised_, the security guarantees of the system (e.g. TEE) can be broken.

The smaller the TCB, the less must be trusted to be secure, hence better security.

In the context of TEEs, the TCB varies depending on the type of TEE. For instance, in Intel's SGX, the TCB is very small including CPU, enclave runtime and enclave code, whilst for AMD SEV-SNP, the TCB is larger since the entire guest OS must be trusted.

Smaller TCB might not always make sense, especially if your application has a significant memory footprint. Please read [The TEE Zoo](#the-tee-zoo) for details on this.

### Remove Attestation

TODO

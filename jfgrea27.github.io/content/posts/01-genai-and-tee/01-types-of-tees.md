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

For the sake of scope reduction, I will only explore Intel's SGX and AMD's SEV, going from smaller to large TCB.

## The TEE Zoo

For each TEE solution, we will discuss

- its architecture;
- an example of a working TEE;
- remote attestation for this type of TEE;
- use cases

### Intel SGX

**Architecture**

The SGX architecture relies on creating a reserved region of memory, the **Enclave Page Cache** that holds encrypted data. This part of the memory is encrypted by special hardware that lives inside the CPU.
During boot, the CPU will generate a hardware-derived key, the **Root Sealing Key (RSK)**, which is used by **Memory Encryption Engine (MEE)** (also living inside the CPU) to encrypt/decrypt any data leaving/entering the CPU.

Intel's SGX also includes special instruction sets including `ECREATE`, `EENTER`, etc., which help separate the User Runtime System (urts) from the Trusted Runtime System (trst).

No one, not even `root` user has access to the EPC in DRAM. Further, data is only decrypted inside the CPU, so L1/L2/L3 caches still hold encrypted data. The encryption process does have some performance overheads.

The control flow works as follows:

1. Enclave is created using `ECREATE`;
2. Data is loaded using `EADD`;
3. Enclave is initialized using `EINIT`;
4. Enter the enclave using `EENTER`;
5. Run _trusted function_;
6. Exit the enclave using `EEXIT`.

The `ECALL`/`OCALL` instructions allow calling urts/trst code from trst/urts respectively.

**Example - a minimal SGX enclave**

This [minimal-sgx-enclave](https://github.com/jfgrea27/minimal-sgx-enclave) uses the [sgx-linux](https://github.com/intel/linux-sgx) project. 

We will assume you have installed `Intel SGX SDK` and `Intel SGX PSW`.

> **_NOTE:_** I had some difficulties installing SGX Linux on my Ubuntu 24.04 box. [This article](https://codentium.com/setting-up-intel-sgx/) was very useful

```sh
git clone git@github.com:jfgrea27/minimal-sgx-enclave.git
# build
make
# run
./app
```

You have ran your first enclave!

**Remote Attestation in SGX enclave**

At a high level, RA for SGX works as follows:

1. Enclave creates a report with `MRENCLAVE`, a cryptographic measurement of the enclave code and data at initialisation of the SGX enclave. This enables the identification of the enclave.
2. Host generatesa quote that includes the measurements from the enclave. 
3. Host sends the quotes to a *Quoting Enclave (QE)*, a pre-installed enclave, which signs the quote, producing a final *SGX quote*.
4. The Host sends the signed SGX quote to a remote verified (e.g. Intel Attestation Service), which verifies the signature and genuiness of the enclave.
5. The enclave is now proven to be trusted. 

Notes:
- The key signed by QE is hardwarebacked and tamper-proof, meaning that the authenticity of the quote is ensured. 
- QE is shipped as part of the SGX software platform.

**Use cases**

As we have detailed in SGX's architecture above, the system relies on a very small TCB that includes the CPU and its microcode. Data is always stored in EPC (encrypted), which limits SGX use-cases to small applications, although Azure do provide some of their DCdsv3 series with up to 256GiB of EPC, as noted [here](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dcdsv3-series?tabs=sizebasic#sizes-in-series).

It is worth noting that SGX are not fully immune. Since data is not encrypted in L1/L2/L3 caches, it is susceptible to side-channel attacks, including speculative execution attacks (e.g. [Meltdown & Spectre](https://meltdownattack.com/)).

A typical use case for using SGX Intel as TEE would be smallish applications that require small trust - for instance a cryptographic key/password store.

There has been notable work around distributed SGX architecture (e.g [here](https://arxiv.org/pdf/2207.05079)), which look interesting. However, the limitations of running SGX only on CPU and not GPU make some workloads (e.g. AI) limited.

### AMD SEV

**Architecture**
As we have seen in [Intel SGX](#intel-sgx), the memory limitations of the EPC make deploying large scale TEE applications in the SGX architecture pretty tricky.

AMD came up with a compromise: rather than have an enclave at the process level, why not make one at the **VM** level.

This is how AMD **Secure Encrypted Virtualization** project was created. 

The advantages of forgoing this security are significant:

- Minimal changes to your applications are required to run it in an AMD SEV-SNP enclave; a lift-and-shit option if you want to deploy quickly.
- More flexible sizes/general availability than Intel SGX.

Clearly, a larger TCB will increase the attack surface. Any vulnerability in devices (e.g. compromised NICs) could be a threat due to the reduced isolation of the enclave.

AMD's SEV offering has evovled since it was fist created in 2016. It now has 3 types of SEV:

- AMD SEV: protect from hypervisor. 
- AMD SEV-ES (Encrypted State): exteds AMD SEV by protecting the CPU register state during VM exists.
- AMD SEV-SNP (Secure Nested Paging): The lasted and strongest version of SEV. It is more battle tested against malicious hypervisor attacks, supports [Remote Attestation](#remote-attestation).


**Example - Deploying a TEE on a Cloud provider**

- 

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

![alt text](hypervisor-types.png "Types of hypervisor - (Wikipedia)")

As a contrast, if you were to run a VM on your laptop, this would be a Type-2 hypervisor as your laptop OS is running the hypervisor (and guest OS) as well as other applications (like browser, etc.).

### Trusted Computing Base

The **Trusted Computing Base (TCB)** is the _minimum_ set of hardware, firmware and software components that must be trusted to enforce the security properties of a system. If any part of the TCB is _compromised_, the security guarantees of the system (e.g. TEE) can be broken.

The smaller the TCB, the less must be trusted to be secure, hence better security.

In the context of TEEs, the TCB varies depending on the type of TEE. For instance, in Intel's SGX, the TCB is very small including CPU, enclave runtime and enclave code, whilst for AMD SEV-SNP, the TCB is larger since the entire guest OS must be trusted.

Smaller TCB might not always make sense, especially if your application has a significant memory footprint. Please read [The TEE Zoo](#the-tee-zoo) for details on this.

### Remote Attestation

**Remote Attestation (RA)** is a process that allows a **remote party** to verify that a program is running *inside a genuine TEE*. The underlying attestation protocol depeneds on the type of TEE, as discussed in [The TEE Zoo](#the-tee-zoo).

RA is required since host OS or cloud provider cannot be fully trusted, and so RA provides a mechanism to trust enclave without having *physical access*.

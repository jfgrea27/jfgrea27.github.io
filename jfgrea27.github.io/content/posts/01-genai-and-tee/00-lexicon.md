---
title: "TEE: 00 - TEE Lexicon"
author: "James"
date: "2025-10-05"
summary: "Lexicon for TEE"
hideBackToTop: true
tags: ["tee"]
draft: false
hideHeader: true
weight: 10
---


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

Smaller TCB might not always make sense, especially if your application has a significant memory footprint. Please read [The TEE Zoo](/posts/01-genai-and-tee/01-types-of-tees/#the-tee-zoo) for details on this.

### Remote Attestation

**Remote Attestation (RA)** is a process that allows a **remote party** to verify that a program is running *inside a genuine TEE*. The underlying attestation protocol depeneds on the type of TEE, as discussed in [The TEE Zoo](/posts/01-genai-and-tee/01-types-of-tees/#the-tee-zoo).

RA is required since host OS or cloud provider cannot be fully trusted, and so RA provides a mechanism to trust enclave without having *physical access*.

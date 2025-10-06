---
title: "TEE: 02 - TEEs and Kubernetes"
author: "James"
date: "1970-01-01"
summary: "Deploy TEE in Kubernetes for production"
hideBackToTop: true
tags: ["kubernetes", "tee"]
draft: true
hideHeader: true
weight: 8
---

As described in [TEE: 01 - Types of TEEs](/posts/01-genai-and-tee/01-types-of-tees), deploying TEEs can be tricky. 
Containerization and Kubernetes have become *de facto* technologies for releasing modern software. This article looks at the various solutions for deploying TEEs in production. 


## Confidential Containers

As described in [Confidential Containers Architecture](https://github.com/confidential-containers/confidential-containers/blob/main/architecture.md), CoCo support both *process-level* and *virtual machine-level* isolation, leveraging SGX and AMD-SEV-SNP. 

It supports 3 types of architectures:

- Process-level using the `enclave-cc` runtime. This runtime uses a `LibOS` to virtualize the operating system of the guest enclave inside the EPC. 
- Lightweight VM using `Kata container` runtime. Each container is launched in its own micro VM (QEMU under the hood). This VM can be one of the usual hardware-backed TEEs (Intel SGX, AMD SEV SNP). This provides stronger isolation than full VM TEE.
- Full-VM isolation 


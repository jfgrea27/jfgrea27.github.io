---
title: "GenAI and Trusted Execution Environments"
author: "James"
date: "2025-08-26"
summary: "An intro to a series on deploying GenAI applications in TEEs."
hideBackToTop: true
tags: ["ai", "tee"]
draft: false
hideHeader: true
---

Generative AI applications often deal with **sensitive data** (e.g. medical records, legal documents, etc.).

Trusted Execution Environments (TEE) are secure hardware that:

- Run code isolation from the rest of the system;
- Protect memory and computation from the OS, hypervisor;
- Guarantee the code running inside hasn't been tampered through an **attestation** framework that takes measurements of the hardware and software running in the TEE and validates these to ensure the TEE has not yet been tampered.

As GenAI is becoming more widely used, I am interested in seeing where we could leverage TEEs to deploy GenAI applications in domains and environments that would on the one hand greatly benefit from such technology (e.g. medical/financial sectors), but are currently too confidential to use chatbot providers such as ChatGPT.

## A quick security reminder

Running applications in TEEs will not guarantee the security of the system. A secure system will have sensitive data encrypted

1. At **rest** on disk - e.g. using AES/RSA or equivalent standard encryption algorithms;
2. In **transit** across network - e.g. using TLS;
3. In **use** on machine - e.g. using TEEs.

It is advised that the security engineer should carry out the necessary [Thread Modeling](https://owasp.org/www-community/Threat_Modeling) in order to ensure the safety of their deployed application.

This series on TEEs is only part of what is required to built such secure systems.

More specifically, this series will explore the following:

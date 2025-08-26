---
title: "GenAI and Trusted Execution Environments"
author: "James"
date: "2025-08-26"
summary: "An intro to a series on deploying GenAI applications in TEEs."
hideBackToTop: true
tags: ["ai", "tee"]
draft: false
---

Generative AI applications often deal with **sensitive data** (e.g. medical records, legal documents, etc.).

Trusted Execution Environments (TEE) are secure hardware that:

- Run code isolation from the rest of the system;
- Protect memory and computation from the OS, hypervisor;
- Guarantee the code running inside hasn't been tampered through an **attestation** framework.

As GenAI is becoming more widely used, I am interested in seeing where we could leverage TEEs to deploy GenAI applications in domains and environments that would on the one hand greatly benefit from such technology (e.g. medical/financial sectors), but are currently too confidential to use chatbot providers such as ChatGPT.

This series explores the above, with the following posts:

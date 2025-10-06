---
title: "TEE: 01 - Types of TEEs"
author: "James"
date: "2025-10-06"
summary: "A whistle stop tour of the types of TEEs."
tags: ["tee", "privacy"]
draft: false
hideHeader: true
weight: 9
---

Trusted Execution Environments are special pieces of hardware that encrypt data in-use so to prevent attackers from compromising running applications.

In this article, we will go through a whistle stop tour of the Confidential Computing landscape, exploring the following for each TEE:

- its architecture;
- an example of a working TEE;
- remote attestation for this type of TEE;
- use cases.


## The TEE Zoo

Confidential Computing primarily comes in two flavors: **process-based** and **virtual machine-based** isolation.
- **Processed-based**: each process is isolated in an enclave. e.g. [Intel SGX](https://www.intel.com/content/www/us/en/products/docs/accelerator-engines/software-guard-extensions.html) 
- **Virtual machine-based**: the entire virtual machine is isolated from its host. e.g. [AMD SEV-SNP](https://www.amd.com/en/developer/sev.html) or [Intel TDX](https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html)

The key drawback of **virtual machine-based** TEEs are that their [**Trusted Computing Base**](/posts/01-genai-and-tee/00-lexicon/#trusted-computing-base)is larger as it includes several more components. 


### Process-based - Intel SGX

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

Looking at the code, we see that we must define `Enclave.edl`

```edl  
enclave {
    trusted {
        public int enclave_add(int a, int b);
    };

    untrusted {
        void host_print([in, string] const char* str);
    };
};

```
This is a specification of the `ECALL` from the host to the enclave and `OCALL` from the enclave to host. It is clear that one must design their application with these trust boundaries in mind; it's not just a lift-and-shift implementation of a TEE.

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

### Virtual machine-based - AMD SEV

**Architecture**

As we have seen in [Intel SGX](#intel-sgx), the memory limitations of the EPC make deploying large scale TEE applications in the SGX architecture pretty tricky.

AMD came up with a compromise: rather than have an enclave at the process level, why not make one at the **VM**-level.

This is how AMD **Secure Encrypted Virtualization** project was created. 

The advantages of forgoing this security are significant:

- Minimal changes to your applications are required to run it in an AMD SEV-SNP enclave; a lift-and-shit option if you want to deploy quickly.
- More flexible sizes/general availability than Intel SGX.

Clearly, a larger TCB will increase the attack surface. Any vulnerability in devices (e.g. compromised NICs) could be a threat due to the reduced isolation of the enclave.

AMD's SEV offering has evolved since it was fist created in 2016. It now has 3 types of SEV:

- **AMD SEV**: protect from hypervisor. 
- **AMD SEV-ES (Encrypted State)**: exteds AMD SEV by protecting the CPU register state during VM exists.
- **AMD SEV-SNP (Secure Nested Paging)**: The lasted and strongest version of SEV. It is more battle tested against malicious hypervisor attacks, supports [Remote Attestation](/posts/01-genai-and-tee/00-lexicon/#remote-attestation).

**Example - Deploying a TEE on a Cloud provider**

As I don't have an AMD machine with SEV, [azure-amd-sev-snp-enclave](https://github.com/jfgrea27/azure-amd-sev-snp-enclave) deploys the smallest available AMD SEV-SNP VM in Azure via terraform. 
Note: not all regions support AMD SEV-SNP, and I also required increasing my quota to the `DC2ads` family to standup the VM.


```sh
git clone git@github.com:jfgrea27/azure-amd-sev-snp-enclave.git
# login into azure
az login
# initialise terraform
terraform init
# deploy infrastructure
terraform apply -var="subscription_id=YOUR_SUBSCRIPTION"
```

The important parts of the terraform include:

```terraform
# Terraform
resource "azurerm_linux_virtual_machine" "vm" {
  name                            = "confidential-vm"
  size                            = "Standard_DC2ads_v5"
  ..
  secure_boot_enabled = true
  vtpm_enabled = true

  os_disk {
    name                   = "osdisk-confidential-vm"
    caching                = "ReadWrite"
    storage_account_type   = "Standard_LRS"
    secure_vm_disk_encryption_set_id = azurerm_disk_encryption_set.des.id
    security_encryption_type = "DiskWithVMGuestState" # Use SEV-SNP encryption
  }

  ...
}
```
Notes:
- Although Azure deploys and maintains the operation of the VM, the hypervisor (and underlying host OS) **cannot directly read of write memory pages** allocated to the VM since the memory is encrypted. 
- Persistant storage (data at rest), must also be encrypted (as discussed on the project [README.md](https://github.com/jfgrea27/azure-amd-sev-snp-enclave)).
- As we can see, the `secure_boot_enabled` and `vtmp_enabled` (Trusted Platform Module) which are both required to launch the VM securily. 
- `security_encryption_type=DiskWithVMGuestState` is required for SEV-SNP.


**Remote Attestation in AMD SEV-SNP enclave**

At a high level, RA for AMD SEV-SNP works as follows:

1. The VM guest communicates with the **AMD Secure Processor** a dedicated co-processor on the CPU, requesting attestation via the *Guest Owner Key (GOK)* interface.
2. The *PSP (Platform Security Processor)* measures the VM (firmware, memory, etc.) and generates a measurement report .
3. The PSP signs it using an AM root key. 
4. The host gets the AMD-signed certificate chain. 

Notes:
- Step 3 (signing) is similar to how QE signs the measurements in SGX.
- The quotes in the AMD case represent the entire VM's measurements and so are more coarse. This means we cannot validate the exact application code's authenticity. This is one of the prices to pay for a lift-and-shift approach to running TEEs.


**Discussion**

It is clear from the above demonstration that little effort is required to migrate an application to run on AMD SEV-SNP. 
However, as already mentioned, the TCB for AMD SEV-SNP is significantly larger than for SGX. This means that the attack surface is greater, 
including shared libraries, guest OS etc. 

A typical use case for AMD SEV-SNP is running confidential workloads in virtualized or cloud environments, where the cloud provider is not fully trusted. 
This includes applications such as secure machine learning, confidential data analytics, and privacy-preserving multi-tenant services. 
For example, cloud providers like Azure and Google Cloud now offer Confidential VMs backed by SEV-SNP, allowing customers to run standard VM workloads with hardware-enforced 
isolation and attestation capabilities, without refactoring applications.

## Conclusion

Trusted Execution Environments (TEEs) are transforming how we think about data security by extending protection beyond data at rest and in transit to include data in use. 
Through hardware-enforced isolation, TEEs allow applications to run sensitive computations even on untrusted infrastructure, 
making them foundational to the growing field of Confidential Computing.

We have seen that Intel SGX and AMD SEV-SNP represent two distinct approaches to this goal. 
SGX offers fine-grained, process-level isolation with a minimal Trusted Computing Base (TCB), making it ideal for small, 
security-critical components such as cryptographic key management or secure enclaves for specific computations. 
In contrast, AMD SEV-SNP provides virtual machine–level isolation, enabling entire workloads to run confidentially with 
minimal application changes—an appealing option for cloud and enterprise environments seeking stronger assurances against host compromise.

Each architecture has trade-offs: SGX’s small TCB provides strong guarantees but limits scalability, while SEV-SNP’s larger 
TCB broadens usability at the cost of a wider attack surface. It is the responsibility of the Security Engineer of the system to critically analyse which TEE best suits their current use case.

I hope you have find this article interesting!


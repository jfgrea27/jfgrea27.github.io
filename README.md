# Personal website

This is my personal website.


## TODOs

- [ ] Projec 1 - Local AI Training Pipeline
  - Companies need reproducible pipelines to train, version, and monitor AI models. This project shows you can design a simple end-to-end ML training workflow without cloud infra.
  


  # AI Infrastructure & Security Projects (Local, Cloud-Free)

This roadmap is designed to strengthen **AI + Infra** skills using your background in Kubernetes, Terraform, Spark, and Rust/Go.  
Each project includes problem motivation, stack, implementation, and stretch goals.

---

## 🔹 Project 1 — Local AI Training Pipeline (Batch)

**Problem / Motivation**  
Companies need reproducible pipelines to train, version, and monitor AI models.  
This project shows you can design a simple **end-to-end ML training workflow** without cloud infra.  

**Stack & Tools**  
- Docker Compose (or K8s)  
- PyTorch (training)  
- Airflow (orchestrator)  
- PostgreSQL (metadata storage)  
- MinIO (object storage for datasets & models)  
- Superset (dashboard)  

**Implementation Steps**  
1. Orchestrate with Airflow:  
   - Ingest data (CIFAR-10, IMDB).  
   - Preprocess (e.g., normalization, tokenization).  
   - Train model (PyTorch).  
   - Evaluate model + log metrics.  
   - Store artifacts in MinIO + Postgres.  
2. Build Superset dashboards for accuracy & metrics over time.  

**Stretch Goals**  
- Add MLflow/W&B experiment tracking.  
- Automate retraining on new data.  
- Version datasets & models in MinIO.  

**Skills Demonstrated**  
- Reproducible ML pipelines  
- Batch orchestration (Airflow)  
- Model artifact management  

---

## 🔹 Project 2 — Real-Time AI Inference with Streaming Data

**Problem / Motivation**  
Modern AI systems need **streaming inference** (fraud detection, recommendations, anomaly detection).  

**Stack & Tools**  
- Kafka (event streaming)  
- Spark Structured Streaming (real-time compute)  
- PyTorch (inference)  
- MinIO (sink)  
- Grafana (monitoring)  

**Implementation Steps**  
1. Deploy Kafka with Docker.  
2. Write a producer to simulate IoT/tweet/finance data.  
3. Spark Streaming job:  
   - Consume Kafka events.  
   - Run PyTorch inference.  
   - Store outputs in MinIO/Postgres.  
4. Add Grafana dashboards:  
   - Throughput (msgs/sec)  
   - Latency  
   - Accuracy drift  

**Stretch Goals**  
- Use Flink for lower latency.  
- Detect OOD (out-of-distribution) inputs.  
- Retraining trigger on drift detection.  

**Skills Demonstrated**  
- Streaming data systems  
- Real-time AI inference  
- Observability for AI workloads  

---

## 🔹 Project 3 — Kubernetes-Native AI Inference Platform

**Problem / Motivation**  
Scaling inference is a **core AI infra challenge** (e.g., serving GPT-like models).  

**Stack & Tools**  
- Kubernetes (kind/minikube)  
- Helm (deployment)  
- FastAPI (API server)  
- BentoML or Ray Serve (model serving)  
- Prometheus + Grafana (monitoring)  

**Implementation Steps**  
1. Package PyTorch model with BentoML/Ray Serve.  
2. Deploy service to K8s with Helm.  
3. Configure autoscaling (HPA/KEDA).  
4. Monitor: request latency, throughput, GPU usage.  

**Stretch Goals**  
- Multi-model serving (multi-tenant).  
- A/B testing or shadow deployments.  
- Load testing with Locust or k6.  

**Skills Demonstrated**  
- AI model serving infra  
- Kubernetes scaling  
- Metrics-driven observability  

---

## 🔹 Project 4 — Secure AI Inference (Privacy-Preserving ML)

**Problem / Motivation**  
AI needs to protect **sensitive models & user data**. Deploy inference inside **trusted enclaves**.  

**Stack & Tools**  
- Rust (Fortanix SGX SDK) or gVisor/Kata Containers  
- PyTorch → ONNX conversion  
- Vault (secrets management)  
- FastAPI (exposed API)  

**Implementation Steps**  
1. Train model → export to ONNX.  
2. Build enclave runtime (Rust or container sandbox).  
3. Run inference securely inside enclave.  
4. API: end-to-end encrypted requests.  
5. Manage secrets/keys with Vault.  

**Stretch Goals**  
- Add remote attestation for clients.  
- Secure logging without data leaks.  

**Skills Demonstrated**  
- Trusted Execution Environments (TEEs)  
- Secure ML serving  
- Rust + AI integration  

---

## 🔹 Project 5 — Capstone: Mini RAG-as-a-Platform

**Problem / Motivation**  
RAG (retrieval-augmented generation) is the backbone of production LLM apps.  

**Stack & Tools**  
- Kubernetes + Helm  
- Kafka (query event streaming)  
- Ray (orchestration)  
- FAISS / Weaviate (vector DB)  
- Hugging Face models (LLaMA/Mistral)  
- dbt (transform metadata)  
- Superset (analytics)  

**Implementation Steps**  
1. Ingest docs (Wikipedia, PDFs, GitHub repos).  
2. Generate embeddings → store in FAISS/Weaviate.  
3. FastAPI service:  
   - Query → vector search → augment → LLM response.  
   - Stream responses back to user.  
4. Kafka captures queries/responses for retraining.  
5. Superset dashboard: query volume, latency, top search terms.  

**Stretch Goals**  
- Multi-tenant namespaces in K8s.  
- Guardrails for PII filtering.  
- Scale inference with Ray Serve.  

**Skills Demonstrated**  
- LLM infra (RAG pipelines)  
- Vector DBs + orchestration  
- Full-stack AI platform design  

---

# ✅ Summary

- **Project 1–2** → Build foundation in ML pipelines + streaming AI.  
- **Project 3** → Show Kubernetes-native AI serving skills.  
- **Project 4** → Differentiate with secure/confidential AI serving.  
- **Project 5 (Capstone)** → Demonstrate platform-level thinking with RAG.  

Together, these projects position you as an **AI Infrastructure / ML Systems Engineer** who can:  
- Train, deploy, and scale AI.  
- Handle real-time + batch workloads.  
- Secure models/data with modern infra.  
- Design end-to-end AI platforms.



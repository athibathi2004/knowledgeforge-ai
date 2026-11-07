# Enterprise Cloud Architecture & Multi-Region Resiliency Guide

## 1. High Availability and Disaster Recovery Framework

KnowledgeForge Enterprise systems are designed to operate with zero single points of failure across multi-region active-active and active-passive deployments.

### Service Tier Classifications
- **Tier 1 (Mission-Critical)**: Customer transaction processing, real-time inference gateway, and core authentication services.
  - **Recovery Time Objective (RTO)**: Maximum 15 minutes.
  - **Recovery Point Objective (RPO)**: Under 1 minute across asynchronous multi-region replication.
- **Tier 2 (Core Business)**: Document parsing, batch vector indexing, and asynchronous evaluation benchmarking.
  - **Recovery Time Objective (RTO)**: Maximum 2 hours.
  - **Recovery Point Objective (RPO)**: Maximum 15 minutes.
- **Tier 3 (Supporting Services)**: Reporting, historical log archiving, and developer sandbox environments.
  - **Recovery Time Objective (RTO)**: Maximum 24 hours.
  - **Recovery Point Objective (RPO)**: Maximum 24 hours.

## 2. Data Protection and Encryption Standards

All data stored or transmitted within the architecture must adhere to strict cryptographic baselines:
- **Data at Rest**: AES-256 encryption is mandatory for all persistent storage volumes, database tables, vector embeddings, and object storage buckets. Encryption keys must be rotated automatically every 90 days using a cloud Key Management Service (KMS).
- **Data in Transit**: All external and inter-service network communication must utilize TLS 1.3 with forward secrecy. Deprecated protocols including TLS 1.0, TLS 1.1, and SSLv3 are blocked at the perimeter edge ingress.

## 3. Database and Storage Architecture

- **Relational Storage**: Primary transactional state is maintained on PostgreSQL 16 with streaming physical replication across availability zones.
- **Vector Storage**: Vector embeddings are indexed using the `pgvector` extension with Hierarchical Navigable Small World (HNSW) indexing (`m=16`, `ef_construction=64`) for sub-50ms cosine similarity retrieval.
- **Blob Storage**: Raw document artifacts (PDFs, DOCXs, text files) are stored in encrypted object storage buckets configured with versioning and immutable write-once-read-many (WORM) retention for 365 days.

## 4. Multi-Region Failover Sequence

In the event of an availability zone or regional outage:
1. Automated health probes detect region degradation when error rates exceed 5% over a 60-second window.
2. Global DNS routing redirects ingress traffic away from the degraded region within 30 seconds.
3. Database standby nodes in the secondary region are promoted to primary if the primary region is unreachable for more than 180 seconds.


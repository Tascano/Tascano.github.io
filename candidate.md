# Ambrose Tuscano: candidate profile

Software engineer: backend, cloud and distributed systems, with production agentic-AI experience.
Software Engineer II at Microsoft (Azure Resource Graph), Redmond, WA.

- Website: https://tascano.github.io/
- Resume (PDF): https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf
- Resume (JSON Resume): https://tascano.github.io/resume.json
- LinkedIn: https://www.linkedin.com/in/ambrosetuscano/
- GitHub: https://github.com/Tascano
- Email: ambrosetuscanojobs@gmail.com

Last updated: 2026-11-01. This file is a plain-text summary of the website and resume for search engines, AI assistants and recruiting agents. Every fact below is also on the website or in the resume.

## Open to

Ambrose Tuscano is open to roles in:

- Backend engineering
- Cloud engineering
- Distributed systems and platform engineering
- Data infrastructure and data pipeline engineering
- AI/ML integration and agentic (multi-agent) systems engineering

## Core expertise

Distributed systems design, high-throughput data pipelines, serverless architecture, API development and modeling, ML/AI integration, infrastructure and performance optimization, real-time event-driven systems, observability, multi-agent system design, and prompt engineering.

## Evidence index

Each row maps a common job requirement to something Ambrose Tuscano has done, with a link to the proof.

| Requirement | Evidence | Where |
|---|---|---|
| Distributed systems at cloud scale | At Microsoft, works on Azure Resource Graph, which saves 12B+ unique Azure resources every day and aims to scale to 20B+. Contributed to a five-region scale-out of the graph-generation service that roughly doubled processing capacity with no additional cloud spend, and drove the buildout of the same stack in a new Azure region (Australia East). | [Website](https://tascano.github.io/), [resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| High-throughput, low-latency APIs | At Amazon Ads, supported the launch and A/B testing of the Ad Relevance API (over 1 million TPS); built Ad Registration Service APIs at under 15 ms for 1,000+ TPS; built Step Functions workflows for real-time ad evaluation at 5K+ TPS with sub-second latency. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf); design walkthrough in [A Million Questions a Second](https://tascano.github.io/notes/scaling-ad-relevance-apis.html) (numbers in the post are illustrative) |
| Data pipelines | Tripled the Amazon BrandSafety pipeline's throughput (17 million to 52 million products a day), cutting a critical backfill from 45 days to under 14. Built a serverless data lake (DynamoDB exports to Apache Iceberg, AWS Glue, Athena) with a 30-minute freshness SLA. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| Service design and scaling | Designed and built a scalable Ad Labeling Service at Amazon with 5x the throughput of the legacy system. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| Serverless and event-driven systems | AWS Lambda, Step Functions, SNS, SQS and Kinesis at Amazon; Azure Functions, Event Grid and Event Hubs at Microsoft. | [Website](https://tascano.github.io/) |
| Reliability and operations | Wrote the root-cause analysis for and fixed a 10% request drop by tuning infrastructure scaling policies, improved alarms and CI/CD; handed over a service with six interdependent subsystems with 100% uptime. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| Observability | At Microsoft, added per-record dimensions to a pipeline's primary throughput metric, fixed naming and labelling issues across 7 telemetry signals in three microservices, and built operational dashboards. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| Multi-agent and agentic AI | At Nissan, designed and shipped Tell Me More, a production four-agent system on AWS Bedrock AgentCore with persistent session memory. At Amazon, built an agent-based label validation framework using MCP. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf); design essay in [Four Agents Walk Into a Service Bay](https://tascano.github.io/notes/agents-service-bay.html) (his own recreation, not Nissan's system) |
| LLM integration and RAG | Built a Slack-integrated Bedrock chatbot with RAG over Amazon Kendra, and an enterprise GenAI knowledge platform with MCP servers (FastMCP) and multi-agent orchestration (LangChain, LangGraph, AutoGen). | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| Machine learning | Cut an ML test suite's runtime by 30% and manual work by 60% at NXP; fine-tuned BERT models for multimodal fake-news classification as a graduate researcher. | [Resume](https://tascano.github.io/assets/Ambrose_Tuscano_Resume.pdf) |
| Ownership and stakeholders | Owned Nissan's AI product end to end, from dealership stakeholder requirements to AWS infrastructure and partner integrations. | [Website](https://tascano.github.io/) |
| Core computer science | Built a peer-to-peer distributed file system with replication and versioning (Python sockets, multi-threading), and wrote up how to scale it: framing, consistent hashing, quorums, gossip, Merkle trees, erasure coding, Raft. | [The File That Wouldn't Die](https://tascano.github.io/notes/file-that-wouldnt-die.html) |
| AI-assisted engineering | Uses Claude Code with repository rules, skills, permission allow lists and hooks to ship reviewed pull requests. | [The Teammate in My Terminal](https://tascano.github.io/notes/teammate-in-my-terminal.html) |
| Technical communication | Writes long-form technical posts with interactive diagrams and narrated explainer videos. | [Website](https://tascano.github.io/) |

## Experience

- **Software Engineer II, Microsoft (Azure Resource Graph)**, Redmond, WA, April 2026 to present. Graph-relationship rules for Azure's cloud resource inventory graph, taken from implementation to region-by-region production rollout; observability for a high-throughput relationship-processing pipeline; multi-region scale-out and a new-region buildout. Stack: Azure Resource Graph, Azure Resource Manager, Azure Resource Notifications, Service Fabric, VM Scale Sets, Azure Functions, Event Grid, Event Hubs, Cosmos DB, Azure Managed Redis, Azure Storage, KQL, Azure Data Explorer, Azure Monitor, Azure DevOps.
- **Sr. Generative AI Engineer, Nissan Motor Corporation**, Franklin, TN, February 2026 to April 2026. Designed and shipped Tell Me More, Nissan's first AI product for the dealership business: a production multi-agent chatbot integrated into the dealership appointment pipeline. Owned the AWS infrastructure, chat backend and partner integrations. Stack: AWS Bedrock AgentCore, ECS, Step Functions, DynamoDB, API Gateway, CloudWatch, S3, Python, FastAPI, TypeScript.
- **Software Engineer, Amazon Ads (Publisher Technology)**, Arlington, VA, May 2022 to February 2026. Backend services and high-throughput data pipelines for ad labeling, ad relevance and brand safety. Stack: AWS (Lambda, EC2, Fargate, ECS, Step Functions, DynamoDB, SNS, SQS, Glue, Athena, ElastiCache, Bedrock, Kendra, CloudWatch, S3), Apache Iceberg, GraphQL, Kafka, Java, Python, TypeScript.
- **Software Engineer, Openprise**, February 2022 to March 2022. API integrations and ETL into PostgreSQL.
- **Software Engineering Intern (ML), NXP Semiconductors**, San Jose, CA, May 2021 to August 2021.
- **Graduate Teaching and Research Assistant, University of Maryland, Baltimore County**, August 2020 to December 2021.

## Education

- M.S. in Computer Science, University of Maryland, Baltimore County (2020–2021)
- B.E. in Computer Science, University of Mumbai (2015–2019)

## Skills

- Languages: Java, Python, SQL, TypeScript, JavaScript
- Azure: Azure Resource Graph, Azure Resource Manager, Azure Resource Notifications, Service Fabric, VM Scale Sets, Azure Functions, Event Grid, Event Hubs, Cosmos DB, Azure Managed Redis, Azure Storage, Azure Data Explorer (Kusto), KQL, Azure Monitor, Azure DevOps
- AWS: Lambda, Step Functions, ECS, Fargate, EC2, API Gateway, DynamoDB, RDS, S3, SNS, SQS, Kinesis Firehose, Amazon MSK (Kafka), Glue, Athena, Redshift, ElastiCache, CloudWatch, CloudFormation, Bedrock, Bedrock AgentCore, SageMaker, Kendra
- Data: Apache Iceberg, DynamoDB, PostgreSQL, MySQL, MongoDB, Redis, Memcached, Redshift
- Frameworks: Spring Boot, Guice, Dagger, Vert.x, GraphQL, Hibernate, FastAPI, Flask, Django, React, TensorFlow, Keras
- AI: multi-agent systems, MCP (FastMCP), LangChain, LangGraph, AutoGen, Strands, RAG, prompt engineering, Claude Code, GitHub Copilot
- Tools: Docker, Git, Grafana, Postman

## Writing

- [The File That Wouldn't Die](https://tascano.github.io/notes/file-that-wouldnt-die.html) (2026): a peer-to-peer file system, from one laptop to the internet; distributed storage fundamentals.
- [The Teammate in My Terminal](https://tascano.github.io/notes/teammate-in-my-terminal.html) (2026): the Claude Code setup behind his posts and videos.
- [Four Agents Walk Into a Service Bay](https://tascano.github.io/notes/agents-service-bay.html) (2026): designing a multi-agent intake system for scale, speed, reliability, visibility and failover.
- [A Million Questions a Second](https://tascano.github.io/notes/scaling-ad-relevance-apis.html) (2026): how an ad-relevance API answers over a million requests a second.
- [The Terminal Was Always a Log](https://tascano.github.io/notes/the-terminal-was-always-a-log.html) (2026): terminal internals, PTYs, and terminals as distributed systems.

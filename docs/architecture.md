\# System Architecture



```mermaid

graph TD

&#x20;   User(\[User / Client]) -->|HTTP/JWT| API\[FastAPI Backend]



&#x20;   subgraph Core API

&#x20;       API -->|Auth| AuthService\[JWT Auth]

&#x20;       API -->|CRUD| JobService\[Job Tracker]

&#x20;       API -->|AI Routes| AIService\[AI Pipeline]

&#x20;   end



&#x20;   subgraph Data Layer

&#x20;       JobService -->|SQLAlchemy| Postgres\[(PostgreSQL 16)]

&#x20;       Postgres --- PGVector\[(pgvector: 384-dim)]

&#x20;       AIService -->|Semantic Search| PGVector

&#x20;   end



&#x20;   subgraph Agentic AI Engine

&#x20;       AIService -->|1. Prompt| Groq\[Groq LLM: Llama 3]

&#x20;       AIService -->|2. Embed| SentenceTransformer\[SentenceTransformers CPU]

&#x20;       AIService -->|3. Tool Call| Agent\[LangGraph Agent]

&#x20;       Agent -->|Scrape| Playwright\[Playwright + Chromium]

&#x20;   end



&#x20;   subgraph Knowledge Graph

&#x20;       AIService -->|GraphRAG Query| Neo4j\[(Neo4j Graph DB)]

&#x20;       Agent -->|Persist Entities| Neo4j

&#x20;   end



&#x20;   Groq -.->|Returns JSON Skills| Agent

&#x20;   Playwright -.->|Returns Page Text| Agent

&#x20;   SentenceTransformer -.->|Returns Vector| AIService

```


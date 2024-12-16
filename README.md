# Sasuke
A powerful, AI-driven assistant for legal and financial queries, leveraging Pathway's fast data ingestion and pipeline building. Designed to automate repetitive tasks, it includes the following specialized agents:

1. **CA Agent**: Streamlines tax filing by identifying savings opportunities, and acts as your virtual Chartered Accountant.
2. **M&A Agent**: Assists with drafting key documents like Definitive Agreements, Letters of Intent, and NDAs for mergers and acquisitions.
3. **Contract Review Agent**: Analyzes legal contracts, flagging suspicious or risky terms for your review.
4. **Market Insights Agent**: Conducts competitive market analysis, offering actionable insights for strategic decision-making.

Along with these specialized agents, it contains a tailored pipelines for legal and financial queries along with a general pipeline for all your daily needs.
Efficient, accurate, and built to save you time and effort.

## Directory Structure

```
.
├── agent.py - start of main pipeline
│ 
├── CA_agent
│   ├── CA_client.py - client to query the vector store
│   ├── CA_server.py - Pathway vector's server to store the documents for the agent
│   ├── IncomeTaxDocuments - directory containing all the relevant income tax documents
│   ├── main.py - main logic of the CA agent
│   └── multi_retrieval.py - specific implementation of multi-retrieval for the agent
├── common
│   ├── adarag.py - logic for AdaRAG agent
│   ├── corrective_rag.py - logic for corrective RAG
|   |── evaluator.py - class containing the evaluator llm
│   ├── hyde.py - logic for HyDe agent
│   ├── linked_chunks.py - create a linked list of chunks to create better context
│   ├── llm.py - fallback logic
│   ├── metrag.py
│   ├── plan_rag.py
│   ├── reranker.py
│   └── websearch.py - websearch agent for scraping along with fallback
├── docker-compose.yml - config to spin up mongo container
├── finance_agent
│   ├── agent.py
│   ├── multi_retrieval.py
│   └── single_retrieval.py 
├── flags_agent
│   ├── agent.py - main logic of the flags agent
│   ├── contracts.py - the checklist to ensure T&C aren't suspicious
├── general_agent - General pipeline
│   ├── agent.py
│   ├── multi_retrieval.py
│   ├── single_retrieval.py
│   └── zero_retrieval.py
├── guardrail - Guardrail to prevent harmful content from LLMs
│   └── guard.py
├── legal_agent - Legal pipeline
│   ├── agent.py
│   ├── multi_retrieval.py
│   └── single_retrieval.py
├── MA_agent
│   ├── agent.py - driving logic of merger and acquisition agent
│   ├── constants.py 
│   ├── definitive_agreement_outline.txt  - outline of all the merger and acquisition documents
│   .  
│   .
│   
│   ├── prompts.py - prompts used by agent
├── macro_agent
│   ├── agent.py - core logic of macro conditions analysis agent 
│   └── multi_retrieval.py - specific implementation of multi-retrieval
├── main_backend.py - main logic for the backend
├── mongo - mongodb integrations,schema
├── rag
│   ├── bm25_server.py - Pathway's BM25 server
│   ├── client.py - client for RAG
│   ├── rrf.py - logic for RRF
│   ├── splade_embed.py - splade embedder
│   ├── splade_server.py - Pathway's SPLADE server
│   └── vector_server.py - Pathway's vector server
├── README.md - project documentation
├── logger_server.py - logging server
├──query_server.py - query server that holds the main pipeline
├── requirements.txt - project dependencies
└── reranker.py - logic for reranking 
documents
├──setup.py - script to setup the framework

```

## Setup
Following setup is for Linux Machines, see the Windows Setup subheading for the relevant changes

Config (.env)
```sh
OPENAI_API_KEY="Your secret openai api key"
COHERE_API_KEY="Your secret cohere api key"
```

Environment
```sh
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

### VectorStore
Add documents to `rag/documents`
```sh
cd rag
pip install -r requirements.txt
python server.py
```

### Multi-Agent Tool

Run the tool
```sh
python -m agent
{enter_your_query}
```

### Windows Setup
For setting up the venv use 
```sh
.\venv\Scripts\activate
```

For VectorStoreServer
```sh
cd rag
docker build -t <image> .
docker run --name <container> <image>
```

## Approach

### RAG-based Pipeline
- The query is processed by AdaRAG and either sent to general, financial or legal query agent.
- The general agent has a zero retrieval, single retrieval and multi retrieval pipeline while the two domain-optimized agents lack the zero retrieval pipeline.
- The zero retrieval pipeline trivially outputs an LLM generated response
- The single retrieval pipeline makes use of HyDE, Vector Store retrieval, MetRAG, Corrective RAG and Cohere Reranker, before feeding the final context to a response-generating LLM agent.
- The multi-retrieval pipeline makes use of PlanRAG to break the query into multiple steps, each of which follows a single retrieval pipeline to obtain a set of documents and responses, which are consolidated using another round of HyDE, MetRAG, Corrective RAG and Cohere Reranker before feeding the overall context to a response-generating LLM agent
- The HyDE agent enables better document retrieval, MetRAG consolidates utility information, corrective RAG acts as a fallback mechanism and Cohere rerankers aims to limit the context length by only passing relevant documents

### Merger and Acquisition Agent
- Automates the generation of essential documents for merger and acquisition transactions, such as Term Sheets, Definitive Agreements, Letters of Intent, NDAs, and Due Diligence Request Lists.
- Takes financial and legal data from two companies as input and produces customized, structured outputs aligned with official document formats.
- Utilizes a planning agent and large language models to generate documents based on predefined outlines and templates.
- Synthesizes relevant data from extensive document repositories through contextual queries to deliver high-quality summaries and insights.

### CA Agent
- Relevant sections of the Income Tax Code of India, related to common tax deductions for individuals, viz. section 80C to 80G are included in the document store, apart from the entire Income Tax Code itself
- Apart from this, the user inputs their own information and documents to the database
- Then, PlanRAG is used on a groups of sections and subsections to streamline the RAG-based process of retrieving relevant tax code information and the user's relevant documents to consolidate them
- Followed by this, a final output determines which sections are, are not and may be relevant to the user's scenario for tax deductions.

### Macros Agent
- This agent identifies product category and then analyzes similar companies in the same domain. It outputs insights, trends, gaps and opportunities in the domain.
- This is done by passing the query to PlanRAG which generates multiple steps to handle the query.
- The response is generated by using the multi retrieval agent by combining the results of all the steps and passing the context to LLM for response generation.

### Flags Agent
This agent is designed to evaluate legal contracts and identify potential issues based on a predefined checklist collected after extensive research on problematic things that can be  or have been(in past) present in legal documents. Users upload contracts in PDF format, which are processed to extract text. The extracted content is evaluated using an AI model that checks each section against the checklist to ensure compliance, clarity, and completeness.

## Guardrail
- Guardrails are used to check the query and LLM output for safety concerns.
- It takes conversation as input, enabling nuanced context analysis for a deeper understanding of interactions.
- We use finetuned LLaMA model. The LLama Guard dynamically classifies conversations into 13 potential unsafe categories, such as hate speech, misinformation, privacy violations, and harmful advice.
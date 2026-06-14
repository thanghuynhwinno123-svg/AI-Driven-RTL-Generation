# AI-Driven RTL Generation Agent (Multi-Agent System)

An automated AI-driven framework leveraging Multi-Agent architecture and Retrieval-Augmented Generation (RAG) to seamlessly compile high-level hardware specifications into fully verified RTL code. This system was developed as an academic project in collaboration with **BOS Semiconductors Vietnam (BHRC)** and **Ho Chi Minh City University of Technology (HCMUT-DEE)**.

---

## 🚀 Overview

The traditional semiconductor design workflow is heavily bottlenecked by manual RTL coding and labor-intensive verification loops. Commercial Large Language Models (LLMs) often suffer from "hardware hallucinations"—producing syntactically valid code that fails physical synthesis or ignores complex timing constraints.

This project introduces a specialized **Multi-Agent Architecture** coupled with **Retrieval-Augmented Generation (RAG)** and the **Model Context Protocol (MCP)**. It establishes a closed-loop execution pipeline that automatically generates, validates, and self-corrects Verilog/SystemVerilog RTL directly driven by industrial simulation logs (Synopsys VCS).

As a benchmark, the system successfully generated and verified the complete microarchitecture for the **RV32EC_Zmmul** microcontroller core (a 3-stage low-power pipeline CPU).

---

## 🏗️ Multi-Agent Architecture

Instead of relying on a single passive prompt-response model, the system divides the design responsibilities across 5 specialized AI Agents running under a centralized Orchestrator (`agent_main.py`).

1. **Planner Agent:** Parses the high-level specification and evaluates dependencies to generate a conflict-free Directed Acyclic Graph (`PLAN_DAG.json`).
2. **Architect Agent:** Produces a deterministic, immutable architectural Intermediate Representation (IR) establishing the absolute port, width, and timing contracts.
3. **RTL Agent:** Translates the frozen IR contracts into syntactically strict, synthesizable SystemVerilog hardware code.
4. **Verification Agent:** Automatically designs comprehensive self-checking testbenches embedded with watchdog timeouts to monitor behavioral coverage.
5. **Critic / Debug Agent:** Diagnoses raw compile and simulation failures parsed from Synopsys VCS logs to issue targeted repair commands.

---

## 🛠️ Key Technical Features

* **Retrieval-Augmented Generation (RAG):** Integrates a local Chroma vector database containing hardware reference manuals, ISA rules, and past bug fixes to eliminate AI hallucinations.
* **Model Context Protocol (MCP):** Connects AI agents securely with local EDA tools and high-performance computing simulation hosts via a unified abstraction tier.
* **Automated Feedback-Driven Loop:** Sets up an iterative verification engine that dynamically retries code fixes (up to 10 iterations) based on industrial compiler warnings.
* **Pre-check Syntactic Gateways:** Runs static code parsers locally for fast linting before wasting simulation overhead or API budget.

---

## 📂 Project Workspace Structure

```text
├── agents/                  # Core LLM prompt definitions & individual agent scripts
├── build_state/             # Stores frozen architectural IRs and SQLite build databases
├── chroma_db_local/         # Vectorized representation of chip specifications & coding rules
├── knowledge_base/          # Source references, RV32EC microarchitecture specs, guidelines
├── memory/                  # Long-term error database logs and structured diagnostics
├── output_pass/             # Final Golden Directory: Verified RTL and self-checking testbenches
├── output_rtl/              # Temporary workspace directory used during current retry cycles
├── agent_main.py            # Central Orchestrator executing the main pipeline framework
├── environment.env          # Configurations for OpenAI/LLM endpoints and MCP parameters
└── REPORT.md                # System-generated summary document reporting execution passes
```

---

## 💻 Technical Stack & Environment

* **Host System:** Linux Environment (Industrial EDA Server)
* **AI Core Integration:** Python (Asyncio), LangChain, ChromaDB
* **Embedding Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
* **EDA Toolchains:** Synopsys VCS Simulator, Verilator, or GCC compiler

---

## 🚀 Execution & Quickstart

1. Clone this repository onto your Linux environment equipped with active Synopsys VCS toolchains.
2. Duplicate `.env.example` into `.env` and fill in your custom configurations:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   MCP_URL=http://127.0.0
   ```
3. Initialize the automated pipeline execution loop:
   ```bash
   python3 agent_main.py
   ```
4. Once execution achieves target converge rules, final production-ready designs can be accessed under `./output_pass/`.

---

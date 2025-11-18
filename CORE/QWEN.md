# RelFab - Salto 0: Grounding Epistémico - QWEN Context

## Project Overview

This is the CORE project for RelFab (Relational Factory), specifically focusing on "Salto 0: Grounding Epistémico". The project aims to validate the generation of PRU (ℰ, 𝒮, ℳ, 𝒯, 𝒟, 𝔓, 𝔗) relation graphs from real data without using LLMs or text, and then using an LLM to reason with the generated graph.

The project is written in Python and uses various libraries including graphiti-core for graph operations, FalkorDB as the graph database, and processing libraries like OpenCV, pandas, and CuPy for data analysis.

## Project Structure

```
/var/home/joss/Proyectos/CORE/
├───.env                    # Environment variables
├───README.md              # Project documentation
├───requirements.txt       # Python dependencies
├───.factory/
│   └───skills/
├───data/                  # Input data directory
│   ├───hmi_video.mp4      # Video data
│   ├───plc_log.csv        # PLC log data
│   └───schematic.pdf      # Schematic data
├───src/                   # Source code
│   ├───__init__.py
│   ├───graphiti_pru.py    # Graphiti extension for PRU ingestion
│   └───pru_extractor.py   # PRU relation extraction logic
├───tests/                 # Test files
│   └───validate_s0.py     # Validation tests for Salto 0
└───tmp/                   # Temporary files
    ├───relfab-salto-0-grounding.zip
    ├───relfab-salto-0.zip.py
    ├───__pycache__/
    └───relfab-salto-0-grounding/
```

## Key Components

### 1. PRU Extractor (`src/pru_extractor.py`)
- Contains logic to extract PRU relations from three data sources:
  - Schematic (PDF): Extracts entities (ℰ) and dependencies (𝒟)
  - Log (CSV): Extracts stochastic relations (𝒮) and mappings (ℳ)
  - Video (MP4): Extracts temporal relations (𝒯)
- Provides a command-line interface to process all three data sources
- Outputs relations in JSONL format

### 2. Graphiti PRU Extension (`src/graphiti_pru.py`)
- Extends the Graphiti framework to support direct ingestion of PRU relations without LLM processing
- Handles the creation of nodes and edges based on PRU relation types
- Uses FalkorDB as the underlying graph database

### 3. Validation Tests (`tests/validate_s0.py`)
- Automated validation of the Definition of Done for Salto 0
- Checks for data existence, relation extraction, graph ingestion, and LLM querying

## Dependencies

The project uses several key libraries:
- `graphiti-core[falkordb]` - Graph database framework with FalkorDB integration
- `cupy` - CUDA-accelerated array library (different versions for ARM64 vs other architectures)
- `opencv-python-headless` - Computer vision processing
- `pandas` - Data manipulation and analysis
- `scipy` - Scientific computing
- `llama-cpp-python` - LLM interface

## Building and Running

### Install Dependencies
```bash
pip install -e ".[dev]"
```

### Run Validation Tests
```bash
python -m tests.validate_s0
```

### Process Data and Generate Relations
```bash
python -m src.pru_extractor --schematic data/schematic.pdf --log data/plc_log.csv --video data/hmi_video.mp4 --output data/episodes.jsonl
```

### Environment Configuration
The `.env` file contains:
- OPENAI_API_KEY: API key for OpenAI (currently empty)
- OPENAI_BASE_URL: Endpoint for OpenAI API
- OPENAI_MODEL: Model name for the OpenAI API

## PRU Relation Types

The project handles different types of PRU relations:
- ℰ (Entities): Entity relations
- 𝒮 (Stochastic): Stochastic relations with time delta information
- ℳ (Mapping): Mapping relations with gain information
- 𝒯 (Temporal): Temporal relations with Intersection over Union (IoU) values
- 𝒟 (Dependency): Dependency relations with exclusivity information
- 𝔓, 𝔗: Planned for future implementation

## DoD (Definition of Done) for Salto 0

1. Real data processed: schematic, log, video
2. PRU extraction without LLM: ≥50 entities, ≥30 relations
3. Graph in FalkorDB (ARM64)
4. LLM queries graph via tool-calling

## Development Notes

- The project simulates PRU relation extraction from different data sources
- Actual implementation in Phase 1 will use LayoutParser + DINOv2 for schematics, TSFresh + CuPy for logs, and OpenCV + optical flow for videos
- The project currently uses simulated data generation but is designed for real data processing
- FalkorDB is used as the graph database backend
- The implementation is designed to work on ARM64 architecture (AGX Orin) with specific CuPy CUDA versions

## Qwen Added Memories
- Key learnings from aprender_ai project analysis: 1) Good ideas: PRU (Primitive Universal Relations) framework with 7 relation types (ℰ, 𝒮, ℳ, 𝒯, 𝒟, 𝔓, 𝔗), no-LLM/no-text processing philosophy, visual-only PDF processing, performance optimizations using KD-Trees, real industrial data integration, well-defined token systems, validity domains concept, GPU optimization for visual processing. 2) Things to avoid: complex dependency stack, incomplete implementations with many TODOs, potential memory issues, hardcoded thresholds, limited error handling, insufficient testing coverage, platform-specific optimizations that reduce portability.

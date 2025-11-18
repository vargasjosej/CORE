# CORE - RelFab: Salto 0 - Grounding Epistémico

## PRU Extraction Engine

This project implements a system for extracting Primitive Universal Relations (PRU) from industrial documents and data sources without using LLMs or text processing. The system focuses on structural and temporal relationships based on observable properties.

### The 7 PRU Types

The system extracts the following relation types:

- **ℰ (Entity)**: Structural co-occurrence
- **𝒮 (Sequentiality)**: Temporal ordering with delay
- **ℳ (Modulation)**: Functional dependency
- **𝒯 (Topology)**: Containment/embedding
- **𝒟 (Disjunction)**: Mutual exclusivity
- **𝔓 (Perspective)**: Observer transformation
- **𝔗 (Temporal Validity)**: Context-dependent validity

### Architecture

The system follows SOLID principles with a domain-driven design:

```
├── cmd/
│   └── pru-engine/           # Application entry point
├── internal/
│   ├── domain/
│   │   └── pru/             # Domain models and interfaces
│   ├── application/
│   │   └── services/        # Application services
│   └── infrastructure/
│       ├── persistence/     # Graph database integration
│       ├── gpu/             # GPU processing
│       └── io/              # File and data processing
└── pkg/
    ├── algorithms/          # Shared algorithms
    └── utils/               # Utility functions
```

### Getting Started

1. Build the project:
   ```bash
   go build ./cmd/pru-engine
   ```

2. Run the engine:
   ```bash
   ./pru-engine
   ```

### Installation Requirements

- Go 1.21+
- Docker (for FalkorDB)
- NVIDIA GPU with CUDA support (optional, for acceleration)

### Development

The project is structured to support iterative development of the PRU extraction capabilities, starting with basic functionality and expanding to full GPU-accelerated processing of industrial documents and signals.
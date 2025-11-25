# Datasets Status - Real vs Synthetic

**Date**: 2025-11-25
**Phase**: 3 (Real Dataset Validation)

---

## ✅ Datasets con Datos REALES Validados

### 1. LISA Traffic Lights (PRU-5 Disjunction)

**Status**: ✅ REAL - 100% Validated

**Source**:
- **Platform**: Kaggle
- **Dataset**: `mbornoe/lisa-traffic-light-dataset`
- **URL**: https://www.kaggle.com/datasets/mbornoe/lisa-traffic-light-dataset
- **Size**: 4.3GB, 43,007 frames
- **Location**: `/var/home/joss/Proyectos/PRU/data/lisa/`

**Tested**:
- 1,000 real frames from daySequence1/2, nightSequence1/2
- 3,000 PRU-5 relations generated
- **Accuracy**: 100% (mutual exclusion validated)

**Implementation**: `benchmark_industrial_kr.py::_load_real_lisa()`

---

### 2. Rico UI Hierarchy (PRU-4 Containment)

**Status**: ✅ REAL - 100% Validated

**Source**:
- **Platform**: HuggingFace
- **Dataset**: `shunk031/Rico` (ui-screenshots-and-view-hierarchies split)
- **URL**: https://huggingface.co/datasets/shunk031/Rico
- **Size**: 56,322 Android UI screens
- **Location**: `~/Descargas/Datasets/Rico/rico_full/`

**Tested**:
- 100 real screens from diverse Android apps
- 1,043 PRU-4 containment relations
- **FOL Compliance**: 100% (transitivity + antisymmetry)

**Implementation**: `benchmark_industrial_kr.py::_load_real_rico()`

---

### 3. OmniDocBench Document Layouts (PRU-1 + PRU-4)

**Status**: ✅ REAL - Implementation Complete

**Source**:
- **Platform**: HuggingFace
- **Dataset**: `opendatalab/OmniDocBench`
- **URL**: https://huggingface.co/datasets/opendatalab/OmniDocBench
- **Size**: 1.25GB, 1,355 pages
- **Location**: `~/Descargas/Datasets/OmniDocBench/OmniDocBench.json`

**Features**:
- 15 block-level annotations (figure, caption, text, table, etc.)
- **Explicit relationship annotations** (figure↔caption)
- 9 document types (papers, reports, textbooks, etc.)
- Multi-language (English, Chinese, mixed)

**Tested**:
- 50 pages processed
- 31 relations (PRU-1 co-presence + PRU-4 containment)

**Implementation**: `benchmark_industrial_kr.py::_load_omnidocbench()`

**Next**: Run full benchmark (1,000 pages)

---

## ⏳ Datasets PENDIENTES (Sintéticos Implementados)

### 4. COIN Procedural Videos (PRU-2 Sequentiality)

**Status**: ⏳ SYNTHETIC FALLBACK - Real Source Found

**Synthetic Implementation**:
- Location: `benchmark_industrial_kr.py::_synthetic_procedures()`
- Generates: step1 → step2 → step3 sequences
- Validates: Acyclicity, temporal ordering

**Real Source Found**:
- **Platform**: COIN Official Site
- **Dataset**: COIN (Comprehensive Instructional Video Dataset)
- **URL**: https://coin-dataset.github.io/
- **Paper**: https://arxiv.org/abs/1903.02874
- **Size**: ~500GB (11,827 videos), ~50MB (annotations only)
- **Access**: Requires registration + approval

**Dataset Structure**:
```json
{
  "database": {
    "video_id": {
      "class": "Making a cake",
      "duration": 120.5,
      "subset": "training",
      "annotation": [
        {"id": 1, "label": "crack egg", "segment": [10.2, 15.3]},
        {"id": 2, "label": "mix ingredients", "segment": [16.0, 25.5]},
        {"id": 3, "label": "pour into pan", "segment": [26.1, 30.8]}
      ]
    }
  }
}
```

**Annotations Format**:
- JSON with temporal segments
- 778 procedural tasks
- 180 classes of actions
- Sequential steps per video

**Download Instructions**:
```bash
# 1. Register at https://coin-dataset.github.io/
# 2. Fill out request form
# 3. Wait for approval email (usually 1-2 days)

# Option A: Annotations only (~50MB)
wget https://coin-dataset.github.io/data/coin_annotations.json

# Option B: Full videos + annotations (~500GB)
# Download links provided in approval email
```

**Implementation TODO**:
```python
def _load_real_coin(self, json_file: Path, limit: int):
    """
    Load real COIN procedural video annotations.

    PRU-2 Relations:
    - step_i → step_j (sequential ordering)
    - Validates: acyclicity, temporal consistency
    """
    with open(json_file) as f:
        data = json.load(f)

    relations = []
    for video_id, video_data in list(data['database'].items())[:limit]:
        steps = sorted(video_data['annotation'], key=lambda x: x['segment'][0])

        # Generate PRU-2 sequential relations
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]

            entity_current = self.resolver.resolve_entity(
                f"step_{current_step['id']}_{current_step['label']}",
                modality="video"
            )
            entity_next = self.resolver.resolve_entity(
                f"step_{next_step['id']}_{next_step['label']}",
                modality="video"
            )

            relations.append(PRURelation(
                entity_a_id=entity_current,
                entity_b_id=entity_next,
                pru_type="PRU-2",  # Sequentiality
                confidence=1.0,
                metadata={
                    'source': 'real_coin',
                    'video_id': video_id,
                    'step_from': current_step['label'],
                    'step_to': next_step['label'],
                    'time_from': current_step['segment'][1],
                    'time_to': next_step['segment'][0]
                }
            ))

    return relations
```

**Priority**: HIGH (critical for PRU-2 validation)

---

### 5. NASA CMAPSS Turbofan Sensors (PRU-3 + PRU-7)

**Status**: ⏳ SYNTHETIC FALLBACK - Real Source Available

**Synthetic Implementation**:
- Location: `benchmark_industrial_kr.py::_synthetic_sensors()`
- Generates: temp → vibration → wear → failure chains
- Validates: Causality, temporal dynamics

**Real Source Available**:
- **Platform**: NASA Open Data / Kaggle
- **Dataset**: NASA Turbofan Engine Degradation Simulation (CMAPSS)
- **URL**: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
- **Paper**: https://ti.arc.nasa.gov/publications/4346/download/
- **Size**: ~35MB (4 datasets)
- **Access**: Public (no registration)

**Dataset Structure**:
```
FD001/
  train_FD001.txt    # Training data
  test_FD001.txt     # Test data
  RUL_FD001.txt      # Remaining Useful Life labels

Format: space-separated values
Columns:
  1. unit_id         # Engine unit number
  2. cycle           # Time in cycles
  3-5. settings      # Operational settings
  6-26. sensors      # 21 sensor measurements
```

**Sensors** (21 total):
- T2: Total temperature at fan inlet
- T24: Total temperature at LPC outlet
- T30: Total temperature at HPC outlet
- T50: Total temperature at LPT outlet
- P2, P15, P30: Pressures
- Nf, Nc: Fan/core speeds
- Etc.

**Causal Chains** (PRU-3):
- Temperature sensors → Vibration sensors
- Vibration → Bearing wear
- Wear → Failure (RUL = 0)

**Temporal Dynamics** (PRU-7):
- Sensor readings evolve over cycles
- Degradation patterns: normal → warning → critical

**Download Instructions**:
```bash
# Option A: Kaggle (recommended)
kaggle datasets download -d behrad3d/nasa-cmaps
unzip nasa-cmaps.zip -d ~/Descargas/Datasets/CMAPSS/

# Option B: NASA direct
wget https://ti.arc.nasa.gov/c/6/
```

**Implementation TODO**:
```python
def _load_real_cmapss(self, data_dir: Path, limit: int):
    """
    Load real CMAPSS turbofan sensor degradation data.

    PRU-3 Relations (Causality):
    - temp_sensor ⇝ vibration_sensor
    - vibration_sensor ⇝ bearing_wear

    PRU-7 Relations (Temporal Dynamics):
    - sensor_t1 ↝ sensor_t2 (evolution)
    """
    import pandas as pd

    # Load training data
    train_file = data_dir / "train_FD001.txt"
    columns = ['unit_id', 'cycle', 'setting1', 'setting2', 'setting3'] + \
              [f'sensor{i}' for i in range(1, 22)]

    df = pd.read_csv(train_file, sep=' ', header=None, names=columns)

    relations = []

    # Group by unit_id
    for unit_id, unit_data in df.groupby('unit_id'):
        if len(relations) >= limit:
            break

        # Sort by cycle
        unit_data = unit_data.sort_values('cycle')

        # PRU-3: Causal relations (correlation → causation)
        # Example: T30 (HPC temp) causes Nf (fan speed) changes
        for i in range(len(unit_data) - 1):
            row_current = unit_data.iloc[i]
            row_next = unit_data.iloc[i + 1]

            # Temperature → Vibration causality
            if row_current['sensor3'] > threshold:  # High temp
                if row_next['sensor4'] > baseline:  # Increased vibration
                    relations.append(PRURelation(
                        entity_a_id=f"temp_sensor_{unit_id}_{i}",
                        entity_b_id=f"vibration_sensor_{unit_id}_{i+1}",
                        pru_type="PRU-3",
                        confidence=0.8,
                        metadata={
                            'source': 'real_cmapss',
                            'unit_id': unit_id,
                            'cause_value': row_current['sensor3'],
                            'effect_value': row_next['sensor4']
                        }
                    ))

        # PRU-7: Temporal dynamics (sensor evolution)
        # ...

    return relations
```

**Priority**: MEDIUM (nice to have for completeness)

---

## 📊 Alternative Sources Investigated

### DocLayNet (Original - NOT USED)

**Status**: ❌ REPLACED by OmniDocBench

**Why Not Used**:
- **Size**: 28GB core dataset (too large)
- **Format**: COCO format (no explicit relationships)
- **Limitation**: Need to infer containment from bounding boxes

**Replacement**: OmniDocBench
- Smaller (1.25GB)
- Has explicit relationship annotations
- Richer annotations (15 categories vs 11)

**Source** (if needed later):
- **URL**: https://github.com/DS4SD/DocLayNet
- **Direct Download**:
  ```bash
  wget https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-doclaynet/1.0.0/DocLayNet_core.zip
  ```

---

## 📋 Summary Table

| Dataset | Status | Real/Synthetic | Size | Priority | ETA |
|---------|--------|----------------|------|----------|-----|
| **LISA** | ✅ Complete | Real | 4.3GB | N/A | Done |
| **Rico** | ✅ Complete | Real | 56K screens | N/A | Done |
| **OmniDocBench** | ✅ Ready | Real | 1.25GB | N/A | Done |
| **COIN** | ⏳ Pending | Synthetic* | 50MB (ann) | HIGH | 1 week |
| **CMAPSS** | ⏳ Pending | Synthetic* | 35MB | MEDIUM | 2 weeks |

\* Synthetic fallback implemented, real source identified

---

## 🎯 Action Plan

### Immediate (This Week)

1. **COIN Registration**:
   ```bash
   # Go to https://coin-dataset.github.io/
   # Fill form with:
   # - Name: José Vargas
   # - Institution: Research
   # - Purpose: Knowledge Representation Research
   # - Email: josejvargas@...
   ```

2. **CMAPSS Download** (no registration needed):
   ```bash
   kaggle datasets download -d behrad3d/nasa-cmaps
   unzip -d ~/Descargas/Datasets/CMAPSS/
   ```

3. **Implement CMAPSS Loader**:
   - Add `_load_real_cmapss()` to `benchmark_industrial_kr.py`
   - Parse sensor time series
   - Generate PRU-3 (causal) + PRU-7 (temporal) relations

### Next Week

1. **Wait for COIN Approval** (1-2 days)
2. **Download COIN Annotations** (~50MB)
3. **Implement COIN Loader**:
   - Add `_load_real_coin()` to `benchmark_industrial_kr.py`
   - Parse procedural step sequences
   - Generate PRU-2 (sequential) relations
4. **Run Full Benchmarks**:
   - COIN: 1,000 videos
   - CMAPSS: 100 engine units
   - OmniDocBench: 1,000 pages

### After Full Validation

1. **Update Documentation**:
   - `PHASE3_RESULTS.md` → 5/5 datasets (100%)
   - `PAPER_DRAFT.md` → Add COIN + CMAPSS results
2. **Paper Draft Completion** (expand to 6,000 words)
3. **Submission to KDD/AAAI**

---

## 📚 References

### COIN
- Paper: "COIN: A Large-scale Dataset for Comprehensive Instructional Video Analysis"
- Authors: Tang et al., CVPR 2019
- arXiv: https://arxiv.org/abs/1903.02874

### CMAPSS
- Paper: "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation"
- Authors: Saxena et al., NASA 2008
- URL: https://ti.arc.nasa.gov/publications/4346/

### OmniDocBench
- Paper: "OmniDocBench: Benchmarking Diverse PDF Document Parsing"
- Authors: OpenDataLab, 2024
- HuggingFace: https://huggingface.co/datasets/opendatalab/OmniDocBench

---

**Last Updated**: 2025-11-25
**Next Review**: After COIN approval
**Status**: 3/5 datasets validated (60%), 2/5 pending (40%)

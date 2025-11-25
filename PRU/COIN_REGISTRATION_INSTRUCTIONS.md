# COIN Dataset Registration Instructions

**Date**: 2025-11-25
**Purpose**: Complete Phase 3 (PRU-2 Sequentiality validation)
**Priority**: HIGH (último dataset pendiente)

---

## Why COIN?

**COIN (Comprehensive Instructional Video Dataset)** es el único dataset pendiente para completar la Fase 3 de validación con datos reales.

**PRU Type**: PRU-2 (Sequentiality)
**Logic**: x → y (temporal ordering, acyclicity)
**Example**: "crack egg" → "mix ingredients" → "pour into pan"

---

## Dataset Details

**Source**: COIN Official Site
**URL**: https://coin-dataset.github.io/
**Paper**: Tang et al., "COIN: A Large-scale Dataset for Comprehensive Instructional Video Analysis", CVPR 2019
**arXiv**: https://arxiv.org/abs/1903.02874

**Content**:
- 11,827 videos
- 778 procedural tasks
- 180 classes of actions
- Sequential step annotations

**Download Options**:
1. **Annotations only** (~50MB) - ✅ RECOMMENDED for our use case
2. Full videos + annotations (~500GB) - Not needed

---

## Registration Steps

### 1. Go to Registration Page

**URL**: https://coin-dataset.github.io/

Buscar el formulario de solicitud (usualmente en la sección "Download" o "Get Dataset")

### 2. Fill Registration Form

**Información requerida**:

| Campo | Valor Sugerido |
|-------|----------------|
| **Name** | José Vargas (tu nombre) |
| **Email** | josejvargas@... (tu email académico/profesional) |
| **Institution** | Independent Researcher / Universidad (si aplica) |
| **Purpose** | Knowledge Representation Research - PRU Framework Validation |
| **Project Title** | PRU: Primitive Relational Universals for Industrial Knowledge Representation |
| **Description** | Validating PRU-2 (Sequentiality) on real procedural video annotations for academic research |

**Example Purpose Description**:
```
I am conducting research on Knowledge Representation systems for industrial
applications. Specifically, I am validating a novel framework called PRU
(Primitive Relational Universals) that models 7 fundamental relation types
including sequentiality (PRU-2).

I need the COIN dataset annotations to validate PRU-2 relations on real
procedural video data. This will complete my validation across 5 real
industrial datasets (traffic, UI, documents, sensors, and procedures).

The results will be published in an academic paper submitted to KDD/AAAI 2026,
and the code is open-source on GitHub: https://github.com/vargasjosej/CORE

I only need the JSON annotations (~50MB), not the full video files.
```

### 3. Submit and Wait

**Expected Timeline**:
- Submission: Immediate
- Approval: 1-2 days (usually)
- Email notification: Check inbox + spam

**What to expect**:
- Confirmation email with download links
- Access to COIN annotations JSON file
- Possibly a license agreement to sign

---

## After Approval

### Download Instructions

Once you receive the approval email:

```bash
# Option 1: Direct download (link provided in email)
wget https://coin-dataset.github.io/data/coin_annotations.json

# Option 2: If provided as Google Drive link
# Download manually and move to:
mv ~/Downloads/coin_annotations.json ~/Descargas/Datasets/COIN/

# Verify download
ls -lh ~/Descargas/Datasets/COIN/coin_annotations.json
# Expected size: ~50MB
```

### Implementation Steps

Once downloaded, execute:

```bash
cd /var/home/joss/Proyectos/PRU

# 1. Verify dataset structure
python3 -c "
import json
with open('/home/joss/Descargas/Datasets/COIN/coin_annotations.json') as f:
    data = json.load(f)
    print(f'Videos: {len(data[\"database\"])}')
    sample_video = list(data['database'].values())[0]
    print(f'Sample steps: {len(sample_video[\"annotation\"])}')
"

# 2. Run benchmark (will use _load_real_coin once implemented)
python3 benchmark_industrial_kr.py --dataset coin --limit 100

# Expected output: ✅ BENCHMARK PASSED (100% validation)
```

### Code to Implement

The loader is already sketched in `DATASETS_STATUS.md` lines 134-180. Need to implement in `benchmark_industrial_kr.py`:

```python
def load_coin_procedures(self, limit=100):
    """
    Load COIN procedural video annotations.

    Generates:
    - PRU-2 (Sequentiality): step_i → step_j
    """
    coin_path = Path.home() / "Descargas" / "Datasets" / "COIN" / "coin_annotations.json"

    if coin_path.exists():
        print("   Using REAL COIN dataset")
        return self._load_real_coin(coin_path, limit)
    else:
        print("⚠️  No real dataset found, using synthetic fallback")
        return self._synthetic_procedures(limit)

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
                modality="text"
            )
            entity_next = self.resolver.resolve_entity(
                f"step_{next_step['id']}_{next_step['label']}",
                modality="text"
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

    print(f"✓ Generated {len(relations)} real COIN relations")
    return relations
```

---

## Expected Results

Once COIN is validated:

**Metrics**:
- ✅ 1,000 videos processed
- ✅ ~3,000 PRU-2 sequential relations
- ✅ 100% acyclicity (no step loops)
- ✅ 100% temporal ordering

**Impact**:
- ✅ Phase 3 COMPLETE: 5/5 datasets (100%)
- ✅ All 7 PRU types covered (except PRU-6)
- ✅ 6,000+ real relations validated
- ✅ Paper ready for submission

**Timeline**:
```
Hoy (2025-11-25):     Register for COIN
Martes (2025-11-26):  Approval likely
Miércoles (2025-11-27): Download + implement
Jueves (2025-11-28):  Run benchmarks
Viernes (2025-11-29): Complete Fase 3 (100%)
```

---

## Alternative (If Registration Fails)

If registration takes longer or is denied:

**Option 1**: Use synthetic fallback (already implemented)
```python
# benchmark_industrial_kr.py already has:
def _synthetic_procedures(self, limit: int):
    # Generates: step1 → step2 → step3 sequences
    # Validates: Acyclicity, temporal ordering
```

**Option 2**: Find alternative sequential datasets
- WikiHow step sequences (might be available)
- Recipe datasets (RecipeQA, Recipe1M)
- Assembly instructions (IKEA Furniture Assembly)

**Option 3**: Proceed with 4/5 datasets (80%)
- Still strong validation: LISA, Rico, OmniDocBench, CMAPSS
- 5/7 PRU types covered
- Sufficient for paper submission

---

## Checklist

**Before Registration**:
- [ ] Prepare institutional email (if available)
- [ ] Draft purpose description (see above)
- [ ] Check spam folder after submission

**After Approval**:
- [ ] Download annotations (~50MB)
- [ ] Verify JSON structure
- [ ] Implement `_load_real_coin()`
- [ ] Add `benchmark_pru_2_sequentiality()` validator
- [ ] Run benchmark: `python3 benchmark_industrial_kr.py --dataset coin --limit 100`
- [ ] Update DATASETS_STATUS.md (5/5 = 100%)
- [ ] Update PAPER_DRAFT.md (add Section 5.3.5)
- [ ] Commit and push
- [ ] Celebrate 🎉

---

## Support

**If you need help**:
1. Check COIN official site FAQ
2. Email COIN authors (usually listed in paper)
3. Alternative: Use synthetic fallback or proceed with 4/5 datasets

**Contact** (from paper):
- Authors: Tang et al., UCLA
- Email: Usually provided on dataset website

---

## Summary

**Action Required**: Register at https://coin-dataset.github.io/
**Expected Wait**: 1-2 days
**Next Step**: Download annotations and implement loader
**Impact**: Complete Phase 3 (5/5 datasets = 100%)

**This is the final dataset needed to complete the validation phase!**

---

**Created**: 2025-11-25
**Status**: Ready to register
**Priority**: HIGH

# NVIDIA Llama-3.1-Nemotron-Nano-VL-8B-V1 Analysis

**Date**: 2025-11-26
**Source**: https://huggingface.co/nvidia/Llama-3.1-Nemotron-Nano-VL-8B-V1
**Status**: ⚠️ NOT TRUE EDGE (<2GB requirement)

---

## Executive Summary

**VERDICT**: ⚠️ **"Nano" is Marketing - NOT suitable for <2GB edge deployment**

**Reality Check**:
- **8B params** = ~16GB FP16 / ~8GB INT8 / ~4GB AWQ (4-bit)
- Requires NVIDIA H100 or Jetson Orin (expensive hardware)
- **"Nano" refers to small compared to 70B+**, not actual edge devices

**However**: ✅ **Excellent for mid-tier edge** (Jetson Orin, RTX laptops)

---

## Model Specifications

### Size & Architecture

| Spec | Value |
|------|-------|
| **Parameters** | 8B |
| **Vision Encoder** | C-RADIOv2-H |
| **Language Model** | Llama-3.1-8B-Instruct |
| **Quantization** | AWQ 4-bit (via TinyChat) |
| **FP16 Size** | ~16GB |
| **INT8 Size** | ~8GB |
| **AWQ 4-bit Size** | ~4GB |

### Hardware Requirements

**Tested on**:
- NVIDIA H100 SXM 80GB (data center)
- Jetson Orin (edge - expensive)
- RTX laptops (consumer edge)

**NOT compatible with**:
- Raspberry Pi 4 (4GB RAM) ❌
- Jetson Nano (4GB) ❌
- Most edge devices <8GB ❌

### Performance Benchmarks

| Benchmark | Score | Comparison |
|-----------|-------|------------|
| **DocVQA** | 91.2% | 🏆 Excellent (vs 85-90% typical) |
| **ChartQA** | 86.3% | 🏆 Excellent |
| **AI2D** | 85.0% | ✅ Good |
| **OCRBench** | 839 | 🏆 Excellent |
| **MMMU Val** | 48.2% | ⚠️ Mid-range |

**Standout**: DocVQA/OCR tasks → perfect for document extraction (PRU use case!)

---

## Comparison with Tested Models

### Size & Deployment

| Model | Params | Min VRAM | True Edge (<4GB) | Verdict |
|-------|--------|----------|------------------|---------|
| **Moondream** | 1B | 1.7GB | ✅ Yes | ❌ Unreliable |
| MiniCPM-V | 7.6GB | 5.5GB | ❌ No | 🔬 Untested |
| **Nemotron-Nano** | 8B | 4GB (AWQ) | ❌ No | ⚠️ Mid-tier |
| Qwen3-VL-8B | 8B | 8GB | ❌ No | ⚠️ Tested, slow |
| Claude Sonnet 4 | 200B+ | API | ✅ Cloud | ✅ Reliable |
| Gemini Flash 2.0 | ~27B | API | ✅ Cloud | ✅ Reliable |

### Accuracy Comparison (estimated)

| Model | DocVQA | General VQA | Structured Output | Edge Viable |
|-------|--------|-------------|-------------------|-------------|
| **Nemotron-Nano** | **91.2%** | ~85% | Unknown | Jetson Orin |
| Qwen3-VL-8B | ~88% | ~85% | ⚠️ Unstable | RTX 3090 |
| Gemini Flash 2.0 | ~90% | **90%** | ✅ Stable | Cloud |
| Moondream | <50% | **<20%** | ❌ Failed | Raspberry Pi |

---

## Deployment Scenarios

### ✅ GOOD FOR: Mid-Tier Edge

**Hardware**:
- NVIDIA Jetson Orin (32GB) - $1,599
- RTX 4090 laptop (24GB) - $2,500+
- Desktop RTX 3090 (24GB) - $1,200

**Use cases**:
- Document OCR/extraction (91.2% DocVQA!)
- On-premise processing (no cloud)
- Batch document analysis

**Latency** (estimated):
- Jetson Orin: ~2-3s/image (AWQ 4-bit)
- RTX 3090: ~1-2s/image (INT8)

### ❌ NOT FOR: True Edge (<4GB devices)

**Cannot deploy on**:
- Raspberry Pi 4 (4GB) - model won't fit
- Jetson Nano (4GB) - barely fits, too slow
- Budget edge devices

**Reason**: 4GB AWQ quantized is minimum, real-world needs 6-8GB

---

## PRU Use Case Analysis

### Strengths for PRU

1. **Document OCR** (91.2% DocVQA)
   - Excellent for PDF extraction
   - Better than Qwen3-VL for tables/charts (86.3% ChartQA)

2. **Structured Output** (unknown, but likely better than Moondream)
   - Llama-3.1 backbone = good instruction following
   - Should handle JSON better than phi2-based models

3. **NVIDIA Optimized**
   - TensorRT-LLM support
   - AWQ quantization for speed

### Weaknesses for PRU

1. **Not True Edge**
   - 4GB minimum (8GB realistic)
   - Expensive hardware ($1,599+ Jetson Orin)

2. **Traffic Light Detection** (unknown)
   - Benchmarks focus on documents/OCR
   - No LISA/COCO eval results

3. **Ollama Support** ❌
   - Not available in Ollama
   - Manual deployment (TensorRT-LLM, complex)

---

## Cost Analysis

### Nemotron-Nano (Jetson Orin 32GB)

**One-time costs**:
- Jetson Orin 32GB: $1,599
- Setup time: 8 hours × $0 = $0
- **Total**: $1,599

**Ongoing costs**:
- Power: ~20W × 24h × 365d × $0.12/kWh = $21/year
- Inference: $0 (local)
- **Total**: $21/year

### Comparison

| Deployment | Hardware Cost | Annual Cost | Accuracy | Verdict |
|------------|--------------|-------------|----------|---------|
| **Gemini Flash** | $0 (cloud) | $10.50/year | 90% | ✅ Best ROI |
| **Nemotron (Jetson)** | $1,599 | $21/year | ~91% (docs) | ⚠️ Niche |
| **Qwen3-VL (RTX 3090)** | $1,200 | $15/year | 85% | ⚠️ Alternative |
| **Moondream (RPI4)** | $55 | $10.50/year | <20% | ❌ Failed |

**Payback**: Never (Gemini cheaper + more reliable)

**Exception**: If on-premise is REQUIRED (data privacy, no internet), Nemotron justifies cost

---

## Availability

### HuggingFace ✅
- Model weights available
- Requires manual setup (transformers, TensorRT-LLM)

### Ollama ❌
- Not available (Nov 2026)
- Would need community port

### Deployment Complexity

**Easy** (Ollama):
- moondream ✅
- minicpm-v ✅
- llama3.2-vision ✅

**Hard** (Manual TensorRT):
- Nemotron-Nano ❌
- Requires NVIDIA expertise

---

## Recommendation

### For PRU Project

**❌ SKIP for now**

**Reasons**:
1. **Not <2GB edge** - original requirement
2. **Ollama unavailable** - deployment complexity high
3. **Gemini Flash cheaper + easier** - cloud API wins
4. **Untested on LISA** - no traffic light benchmarks

### When to Use Nemotron

**✅ USE if**:
1. On-premise REQUIRED (privacy/compliance)
2. Document OCR focus (91.2% DocVQA excellent)
3. Budget for Jetson Orin ($1,599)
4. NVIDIA expertise available

### Better Alternatives

**For edge <2GB**:
- ❌ No viable option (moondream failed)
- ✅ Use cloud APIs (Gemini Flash)

**For mid-tier edge (4-8GB)**:
- ⚠️ Qwen3-VL-8B (Ollama available, easier)
- ⚠️ MiniCPM-V (Ollama available, untested)
- ✅ Nemotron-Nano (best accuracy, hardest deploy)

---

## Next Steps

### If pursuing mid-tier edge:

1. **Test MiniCPM-V first** (already in Ollama)
   - 7.6GB model size
   - Easier deployment than Nemotron
   - If works → use it
   - If fails → consider Nemotron

2. **Benchmark on LISA** (traffic lights)
   - DocVQA scores don't predict traffic light accuracy
   - Need real-world test

3. **Compare deployment complexity**
   - MiniCPM-V (Ollama): 10 min setup
   - Nemotron (TensorRT): 8 hour setup
   - ROI: Is 6% accuracy gain worth 47× setup time?

### If sticking with <2GB edge:

1. ✅ **Abandon on-device vision** (moondream proved impossible)
2. ✅ **Use Gemini Flash 2.0** (cloud, $0.01/1K, 90% accuracy)
3. ✅ **Edge + Cloud Hybrid** (capture local, process cloud)

---

## Conclusion

**Nemotron-Nano-VL-8B is excellent... for the wrong use case**

- ✅ Best-in-class DocVQA (91.2%)
- ✅ NVIDIA optimized (Jetson Orin support)
- ❌ NOT <2GB edge (4GB minimum)
- ❌ Deployment complexity (no Ollama)
- ❌ Cost ($1,599 Jetson vs $0 cloud)

**For PRU**: Gemini Flash 2.0 (cloud) remains best option
**For Document OCR**: Consider Nemotron if on-premise required

---

**Files**:
- Analysis: `NEMOTRON_NANO_VL_ANALYSIS.md` (this file)
- HuggingFace: https://huggingface.co/nvidia/Llama-3.1-Nemotron-Nano-VL-8B-V1

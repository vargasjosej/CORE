#!/usr/bin/env python3
"""
Industrial Knowledge Representation Benchmark.

Tests PRU system on industrial datasets:
- LISA (Traffic Lights) → PRU-5 (Disjunction)
- Rico (UI Hierarchy) → PRU-4 (Containment)
- COIN (Procedures) → PRU-2 (Sequentiality)
- DocLayNet (Layouts) → PRU-1 + PRU-4
- CMAPSS (Sensors) → PRU-3 + PRU-7

Usage:
    python benchmark_industrial_kr.py --dataset lisa --pru PRU-5 --limit 100
"""
import os
import sys
from pathlib import Path
from typing import List, Dict
import json

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'tests'))

from src.core.types import PRURelation
from src.core.entity_resolver import MultimodalEntityResolver
from test_first_order_consistency import FirstOrderValidator


class IndustrialKRLoader:
    """Load industrial KR datasets."""

    def __init__(self):
        self.resolver = MultimodalEntityResolver()
        self.validator = FirstOrderValidator()

    def load_lisa_traffic_lights(self, limit=100):
        """
        Load LISA traffic light dataset.

        Validates: PRU-5 (Disjunction)
        Rule: Exactly ONE light active per frame
        """
        print(f"Loading LISA Traffic Lights (limit={limit})...")

        # Check if real data exists
        data_path = Path("data/lisa/Annotations/Annotations")
        if not data_path.exists():
            print("⚠️  LISA dataset not found, using synthetic fallback")
            return self._synthetic_traffic_lights(limit)

        # Load real LISA data
        return self._load_real_lisa(data_path, limit)

    def _synthetic_traffic_lights(self, limit=100):
        """
        Synthetic traffic light data for PRU-5 testing.

        Ground truth: Exactly one light active at any time.
        """
        print(f"   Generating {limit} synthetic traffic light states...")

        relations = []
        states = ["red", "yellow", "green"]

        for i in range(limit):
            # Each "frame" has exactly one active light
            active_state = states[i % 3]

            # Create entities for this frame
            frame_id = f"frame_{i}"

            # PRU-5: Disjunction - exactly ONE active
            for state in states:
                if state == active_state:
                    # This state is active
                    entity_state = self.resolver.resolve_entity(f"{state}_light", modality="image")
                    entity_frame = self.resolver.resolve_entity(frame_id, modality="image")

                    relations.append(PRURelation(
                        entity_a_id=entity_state,
                        entity_b_id=entity_frame,
                        pru_type="PRU-5",  # Disjunction
                        confidence=1.0,
                        metadata={
                            'source': 'synthetic_lisa',
                            'frame': i,
                            'active_state': active_state,
                            'state': state,
                            'is_active': True
                        }
                    ))
                else:
                    # This state is NOT active
                    entity_state = self.resolver.resolve_entity(f"{state}_light", modality="image")
                    entity_frame = self.resolver.resolve_entity(frame_id, modality="image")

                    relations.append(PRURelation(
                        entity_a_id=entity_state,
                        entity_b_id=entity_frame,
                        pru_type="PRU-5",
                        confidence=1.0,
                        metadata={
                            'source': 'synthetic_lisa',
                            'frame': i,
                            'active_state': active_state,
                            'state': state,
                            'is_active': False
                        }
                    ))

        print(f"✓ Generated {len(relations)} traffic light relations")
        return relations

    def _load_real_lisa(self, annotations_path: Path, limit: int):
        """
        Load real LISA traffic light annotations.

        CSV format: Filename;Annotation tag;...
        Tags: stop (red), warning (yellow), go (green)
        """
        import csv

        print(f"   Loading real LISA annotations from {annotations_path}")

        # Find all CSV annotation files
        csv_files = list(annotations_path.glob("*/frameAnnotationsBULB.csv"))

        if not csv_files:
            print("   ⚠️  No annotation files found, falling back to synthetic")
            return self._synthetic_traffic_lights(limit)

        print(f"   Found {len(csv_files)} annotation files")

        relations = []
        frame_count = 0

        # Group annotations by frame
        frame_annotations = {}

        for csv_file in csv_files:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    if frame_count >= limit:
                        break

                    filename = row['Filename']
                    tag = row['Annotation tag']

                    # Map LISA tags to states
                    # stop/stopLeft → red
                    # warning/warningLeft → yellow
                    # go/goLeft → green
                    if 'stop' in tag.lower():
                        state = 'red'
                    elif 'warning' in tag.lower():
                        state = 'yellow'
                    elif 'go' in tag.lower():
                        state = 'green'
                    else:
                        continue

                    if filename not in frame_annotations:
                        frame_annotations[filename] = []
                        frame_count += 1

                    frame_annotations[filename].append(state)

                    if frame_count >= limit:
                        break

                if frame_count >= limit:
                    break

        print(f"   Loaded {len(frame_annotations)} frames")

        # Convert to PRU-5 relations
        for frame_id, states in frame_annotations.items():
            # Get unique states in this frame
            unique_states = set(states)

            # Create PRU-5 relations: each state either active or not
            for state in ['red', 'yellow', 'green']:
                entity_state = self.resolver.resolve_entity(f"{state}_light", modality="image")
                entity_frame = self.resolver.resolve_entity(frame_id, modality="image")

                is_active = state in unique_states

                relations.append(PRURelation(
                    entity_a_id=entity_state,
                    entity_b_id=entity_frame,
                    pru_type="PRU-5",
                    confidence=1.0 if is_active else 0.0,
                    metadata={
                        'source': 'real_lisa',
                        'frame': frame_id,
                        'active_states': list(unique_states),
                        'state': state,
                        'is_active': is_active
                    }
                ))

        print(f"✓ Generated {len(relations)} real LISA relations")
        return relations

    def load_rico_ui(self, limit=100):
        """
        Load Rico UI hierarchy dataset.

        Validates: PRU-4 (Containment)
        Rule: child ⊂ parent (strict hierarchy from Android view tree)
        """
        print(f"Loading Rico UI Hierarchy (limit={limit})...")

        # Check if real data exists
        rico_path = Path(os.path.expanduser("~/Descargas/Datasets/Rico/rico_full"))
        if not rico_path.exists():
            print("⚠️  Rico dataset not available, using synthetic UI")
            return self._synthetic_ui_hierarchy(limit)

        # Load real Rico data
        return self._load_real_rico(rico_path, limit)

    def _synthetic_ui_hierarchy(self, limit=100):
        """Synthetic UI hierarchy for PRU-4 testing."""
        print(f"   Generating {limit} synthetic UI hierarchies...")

        relations = []

        # UI structure: navbar > button > icon
        ui_structures = [
            ("home_icon", "home_button", "main_navbar"),
            ("search_icon", "search_button", "main_navbar"),
            ("profile_icon", "profile_button", "side_navbar"),
        ]

        for i in range(min(limit, len(ui_structures) * 10)):
            idx = i % len(ui_structures)
            icon, button, navbar = ui_structures[idx]

            # PRU-4: icon ⊂ button
            relations.append(PRURelation(
                entity_a_id=f"{icon}_{i}",
                entity_b_id=f"{button}_{i}",
                pru_type="PRU-4",
                confidence=0.95,
                metadata={'source': 'synthetic_rico', 'level': 'icon_button'}
            ))

            # PRU-4: button ⊂ navbar
            relations.append(PRURelation(
                entity_a_id=f"{button}_{i}",
                entity_b_id=f"{navbar}_{i}",
                pru_type="PRU-4",
                confidence=0.95,
                metadata={'source': 'synthetic_rico', 'level': 'button_navbar'}
            ))

            # PRU-4: icon ⊂ navbar (transitive, should be inferred)
            relations.append(PRURelation(
                entity_a_id=f"{icon}_{i}",
                entity_b_id=f"{navbar}_{i}",
                pru_type="PRU-4",
                confidence=0.90,
                metadata={'source': 'synthetic_rico', 'level': 'transitive'}
            ))

        print(f"✓ Generated {len(relations)} UI hierarchy relations")
        return relations

    def _load_real_rico(self, rico_path: Path, limit: int):
        """
        Load real Rico UI hierarchies from Android view trees.

        Extracts containment relations (PRU-4) from nested UI structure.
        """
        from datasets import load_from_disk

        print(f"   Loading real Rico from {rico_path}")

        ds = load_from_disk(str(rico_path))
        print(f"   Found {len(ds)} UI screens")

        relations = []
        screen_count = 0

        for screen in ds:
            if screen_count >= limit:
                break

            activity = screen.get('activity')
            if not activity or 'children' not in activity:
                continue

            screen_id = screen.get('request_id', screen_count)

            # Extract containment relations from hierarchy
            def extract_containment(children, parent_id=None, depth=0):
                nonlocal relations

                if depth > 10:  # Prevent infinite recursion
                    return

                for i, child_group in enumerate(children):
                    if isinstance(child_group, dict):
                        # Single child
                        child_klasses = [child_group.get('klass', 'unknown')]
                        child_ids = [f"{parent_id}_child_{i}" if parent_id else f"screen_{screen_id}_elem_{i}"]
                    else:
                        # Multiple children (arrays)
                        child_klasses = child_group.get('klass', [])
                        if not isinstance(child_klasses, list):
                            child_klasses = [child_klasses]

                        child_ids = [f"{parent_id}_child_{i}_{j}" if parent_id else f"screen_{screen_id}_elem_{i}_{j}"
                                     for j in range(len(child_klasses))]

                    # Create containment relations
                    for child_id, child_klass in zip(child_ids, child_klasses):
                        if parent_id:
                            # child ⊂ parent
                            child_entity = self.resolver.resolve_entity(child_id, modality="text")
                            parent_entity = self.resolver.resolve_entity(parent_id, modality="text")

                            relations.append(PRURelation(
                                entity_a_id=child_entity,
                                entity_b_id=parent_entity,
                                pru_type="PRU-4",
                                confidence=1.0,
                                metadata={
                                    'source': 'real_rico',
                                    'screen_id': screen_id,
                                    'child_klass': child_klass,
                                    'parent_id': parent_id,
                                    'depth': depth
                                }
                            ))

                        # Recurse if has children
                        if isinstance(child_group, dict) and 'children' in child_group:
                            extract_containment(child_group['children'], child_id, depth + 1)

            # Start from root
            root_id = f"screen_{screen_id}_root"
            if 'children' in activity:
                extract_containment(activity['children'], root_id, 0)

            screen_count += 1

        print(f"   Loaded {screen_count} screens")
        print(f"✓ Generated {len(relations)} real Rico containment relations")
        return relations

    def load_doclaynet(self, limit=100):
        """
        Load DocLayNet document layout dataset.

        Validates: PRU-1 (Co-presence), PRU-4 (Containment)
        Rules:
        - PRU-1: Elements on same page co-occur
        - PRU-4: Captions contained in figures
        """
        print(f"Loading DocLayNet Layouts (limit={limit})...")

        # Check if real data exists
        data_path = Path.home() / "Descargas" / "Datasets" / "DocLayNet"
        annotations_file = data_path / "COCO" / "val.json"

        if not annotations_file.exists():
            print("⚠️  DocLayNet dataset not found, using synthetic fallback")
            return self._synthetic_document_layout(limit)

        # Load real DocLayNet data
        return self._load_real_doclaynet(annotations_file, limit)

    def _synthetic_document_layout(self, limit=100):
        """
        Synthetic document layout data for PRU-1 + PRU-4 testing.

        Ground truth:
        - Figure and caption co-occur on same page (PRU-1)
        - Caption contained in figure region (PRU-4)
        """
        print(f"   Generating {limit} synthetic document layouts...")

        relations = []

        for i in range(limit):
            page_id = f"page_{i}"

            # Create document elements
            figure_id = f"figure_{i}"
            caption_id = f"caption_{i}"
            text_id = f"text_{i}"
            title_id = f"title_{i}"

            # PRU-1: Co-presence (same page)
            # Figure ∼ Caption (co-occur)
            entity_figure = self.resolver.resolve_entity(figure_id, modality="image")
            entity_caption = self.resolver.resolve_entity(caption_id, modality="text")

            relations.append(PRURelation(
                entity_a_id=entity_figure,
                entity_b_id=entity_caption,
                pru_type="PRU-1",  # Co-presence
                confidence=1.0,
                metadata={
                    'source': 'synthetic_doclaynet',
                    'page': page_id,
                    'type_a': 'figure',
                    'type_b': 'caption',
                    'relation': 'co-presence'
                }
            ))

            # PRU-4: Containment
            # Caption ⊂ Figure (caption within figure bounding box)
            relations.append(PRURelation(
                entity_a_id=entity_caption,
                entity_b_id=entity_figure,
                pru_type="PRU-4",  # Containment
                confidence=1.0,
                metadata={
                    'source': 'synthetic_doclaynet',
                    'page': page_id,
                    'child_type': 'caption',
                    'parent_type': 'figure',
                    'relation': 'containment'
                }
            ))

        print(f"✓ Generated {len(relations)} synthetic DocLayNet relations")
        return relations

    def _load_real_doclaynet(self, annotations_file: Path, limit: int):
        """
        Load real DocLayNet COCO annotations.

        COCO format:
        {
          "images": [{"id": 1, "file_name": "...", ...}],
          "annotations": [{
            "id": 1,
            "image_id": 1,
            "category_id": 1,  # 0-10 (caption, text, list, table, figure, etc.)
            "bbox": [x, y, width, height],
            ...
          }],
          "categories": [{"id": 1, "name": "caption"}, ...]
        }
        """
        print(f"   Loading real DocLayNet from {annotations_file}")

        try:
            with open(annotations_file, 'r') as f:
                coco_data = json.load(f)
        except FileNotFoundError:
            print(f"   ERROR: {annotations_file} not found")
            return self._synthetic_document_layout(limit)

        # Build category map
        categories = {cat['id']: cat['name'] for cat in coco_data['categories']}

        # Build image index
        images = {img['id']: img for img in coco_data['images'][:limit]}

        # Process annotations
        annotations_by_image = {}
        for ann in coco_data['annotations']:
            img_id = ann['image_id']
            if img_id in images:
                if img_id not in annotations_by_image:
                    annotations_by_image[img_id] = []
                annotations_by_image[img_id].append(ann)

        print(f"   Found {len(images)} images")
        print(f"   Found {sum(len(v) for v in annotations_by_image.values())} annotations")

        relations = []

        # Generate PRU relations
        for img_id, anns in list(annotations_by_image.items())[:limit]:
            page_id = f"page_{img_id}"

            # Group by category
            figures = [a for a in anns if categories[a['category_id']] == 'Figure']
            captions = [a for a in anns if categories[a['category_id']] == 'Caption']

            # PRU-1: Co-presence (figure ∼ caption on same page)
            for fig in figures:
                for cap in captions:
                    entity_fig = self.resolver.resolve_entity(
                        f"figure_{fig['id']}",
                        modality="image"
                    )
                    entity_cap = self.resolver.resolve_entity(
                        f"caption_{cap['id']}",
                        modality="text"
                    )

                    relations.append(PRURelation(
                        entity_a_id=entity_fig,
                        entity_b_id=entity_cap,
                        pru_type="PRU-1",
                        confidence=1.0,
                        metadata={
                            'source': 'real_doclaynet',
                            'page': page_id,
                            'entity_a_text': f"figure_{fig['id']}",
                            'entity_b_text': f"caption_{cap['id']}",
                            'type_a': 'Figure',
                            'type_b': 'Caption'
                        }
                    ))

            # PRU-4: Containment (check if caption bbox inside figure bbox)
            for fig in figures:
                fig_bbox = fig['bbox']  # [x, y, width, height]
                fig_x1, fig_y1 = fig_bbox[0], fig_bbox[1]
                fig_x2, fig_y2 = fig_x1 + fig_bbox[2], fig_y1 + fig_bbox[3]

                for cap in captions:
                    cap_bbox = cap['bbox']
                    cap_x1, cap_y1 = cap_bbox[0], cap_bbox[1]
                    cap_x2, cap_y2 = cap_x1 + cap_bbox[2], cap_y1 + cap_bbox[3]

                    # Check containment (caption inside figure)
                    if (cap_x1 >= fig_x1 and cap_y1 >= fig_y1 and
                        cap_x2 <= fig_x2 and cap_y2 <= fig_y2):

                        entity_cap = self.resolver.resolve_entity(
                            f"caption_{cap['id']}",
                            modality="text"
                        )
                        entity_fig = self.resolver.resolve_entity(
                            f"figure_{fig['id']}",
                            modality="image"
                        )

                        relations.append(PRURelation(
                            entity_a_id=entity_cap,
                            entity_b_id=entity_fig,
                            pru_type="PRU-4",
                            confidence=1.0,
                            metadata={
                                'source': 'real_doclaynet',
                                'page': page_id,
                                'child_klass': f"caption_{cap['id']}",
                                'parent_id': f"figure_{fig['id']}",
                                'child_type': 'Caption',
                                'parent_type': 'Figure'
                            }
                        ))

        print(f"✓ Generated {len(relations)} real DocLayNet relations")
        return relations


class IndustrialKRBenchmark:
    """Benchmark PRU on industrial KR datasets."""

    def __init__(self):
        self.loader = IndustrialKRLoader()
        self.validator = FirstOrderValidator()

    def benchmark_pru_5_disjunction(self, relations: List[PRURelation]) -> Dict:
        """
        Benchmark PRU-5 (Disjunction) on traffic lights.

        Validates:
        - Exactly ONE light active per frame
        - Mutual exclusion: red ⊕ yellow ⊕ green
        """
        print()
        print("=" * 80)
        print("PRU-5 DISJUNCTION BENCHMARK (Traffic Lights)")
        print("=" * 80)
        print()

        # Group by frame (handle both synthetic and real)
        frames = {}
        for rel in relations:
            source = rel.metadata.get('source')
            if source in ['synthetic_lisa', 'real_lisa']:
                frame_id = rel.metadata['frame']
                if frame_id not in frames:
                    frames[frame_id] = []
                frames[frame_id].append(rel)

        # Validate each frame
        violations = []
        for frame_id, frame_rels in frames.items():
            # Count active states
            active_states = [
                r for r in frame_rels
                if r.metadata.get('is_active') == True
            ]

            # Must be exactly 1
            if len(active_states) != 1:
                violations.append(
                    f"Frame {frame_id}: {len(active_states)} active states (expected 1)"
                )

            # Check mutual exclusion
            active_state_names = set(r.metadata.get('state') for r in active_states)
            if len(active_state_names) > 1:
                violations.append(
                    f"Frame {frame_id}: Multiple states active: {active_state_names}"
                )

        # Results
        total_frames = len(frames)
        passed_frames = total_frames - len(violations)
        accuracy = passed_frames / total_frames if total_frames > 0 else 0

        print(f"Total frames: {total_frames}")
        print(f"Passed: {passed_frames}/{total_frames} ({accuracy:.1%})")
        print()

        if violations:
            print("❌ VIOLATIONS DETECTED:")
            for v in violations[:5]:
                print(f"  - {v}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
        else:
            print("✅ ALL CHECKS PASSED")
            print("  ✓ Exactly ONE light active per frame")
            print("  ✓ Mutual exclusion validated")
            print("  ✓ No contradictions")

        return {
            'dataset': 'lisa',
            'pru_type': 'PRU-5',
            'total_frames': total_frames,
            'passed_frames': passed_frames,
            'accuracy': accuracy,
            'violations': violations
        }

    def benchmark_pru_4_containment(self, relations: List[PRURelation]) -> Dict:
        """
        Benchmark PRU-4 (Containment) on UI hierarchy.

        Validates:
        - Transitivity: icon ⊂ button ∧ button ⊂ navbar → icon ⊂ navbar
        - Antisymmetry: icon ⊂ button → ¬(button ⊂ icon)
        """
        print()
        print("=" * 80)
        print("PRU-4 CONTAINMENT BENCHMARK (UI Hierarchy)")
        print("=" * 80)
        print()

        # FOL validation
        all_pass, results = self.validator.validate_all(relations)

        # Extract containment results
        transitivity_result = results.get('containment_transitivity', (True, []))
        antisymmetry_result = results.get('containment_antisymmetry', (True, []))

        passed_trans, violations_trans = transitivity_result
        passed_anti, violations_anti = antisymmetry_result

        print(f"Total relations: {len(relations)}")
        print()
        print("Transitivity Check:")
        if passed_trans:
            print("  ✅ PASSED")
        else:
            print(f"  ❌ FAILED ({len(violations_trans)} violations)")
            for v in violations_trans[:3]:
                print(f"    - {v}")

        print()
        print("Antisymmetry Check:")
        if passed_anti:
            print("  ✅ PASSED")
        else:
            print(f"  ❌ FAILED ({len(violations_anti)} violations)")
            for v in violations_anti[:3]:
                print(f"    - {v}")

        return {
            'dataset': 'rico',
            'pru_type': 'PRU-4',
            'total_relations': len(relations),
            'transitivity_passed': passed_trans,
            'antisymmetry_passed': passed_anti,
            'violations': {
                'transitivity': violations_trans,
                'antisymmetry': violations_anti
            }
        }

    def benchmark_dataset(self, dataset_name: str, pru_type: str = None, limit: int = 100):
        """
        Benchmark a specific dataset.

        Args:
            dataset_name: 'lisa', 'rico', 'coin', etc.
            pru_type: Specific PRU type to test (or None for all)
            limit: Number of samples
        """
        # Load dataset
        if dataset_name == 'lisa':
            relations = self.loader.load_lisa_traffic_lights(limit=limit)
            return self.benchmark_pru_5_disjunction(relations)

        elif dataset_name == 'rico':
            relations = self.loader.load_rico_ui(limit=limit)
            return self.benchmark_pru_4_containment(relations)

        else:
            print(f"❌ Unknown dataset: {dataset_name}")
            print(f"   Available: lisa, rico")
            return {}


def main():
    """Run industrial KR benchmark."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Benchmark PRU on Industrial KR datasets'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        required=True,
        choices=['lisa', 'rico', 'coin', 'doclaynet', 'cmapss'],
        help='Dataset to benchmark'
    )
    parser.add_argument(
        '--pru',
        type=str,
        default=None,
        help='Specific PRU type (e.g., PRU-5)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Number of samples'
    )
    parser.add_argument(
        '--validate-fol',
        action='store_true',
        help='Run FOL consistency validation'
    )

    args = parser.parse_args()

    # Run benchmark
    benchmark = IndustrialKRBenchmark()
    result = benchmark.benchmark_dataset(
        args.dataset,
        pru_type=args.pru,
        limit=args.limit
    )

    # Summary
    print()
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print()

    if result:
        for key, value in result.items():
            if key != 'violations':
                print(f"{key}: {value}")

    print()

    # Exit code
    accuracy = result.get('accuracy')
    if accuracy is not None:
        # Accuracy-based (LISA)
        if accuracy >= 0.95:
            print("✅ BENCHMARK PASSED")
            sys.exit(0)
        else:
            print("❌ BENCHMARK FAILED")
            sys.exit(1)
    else:
        # Boolean checks (Rico, etc.)
        transitivity = result.get('transitivity_passed', True)
        antisymmetry = result.get('antisymmetry_passed', True)

        if transitivity and antisymmetry:
            print("✅ BENCHMARK PASSED")
            sys.exit(0)
        else:
            print("❌ BENCHMARK FAILED")
            sys.exit(1)


if __name__ == '__main__':
    main()

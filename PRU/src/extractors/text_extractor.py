"""
Text → PRU extractor using LLM.
REAL implementation using Claude API - no simulation.
"""
import json
import logging
import os
from typing import List, Dict, Optional
from anthropic import Anthropic

from ..core.entity_resolver import MultimodalEntityResolver
from ..core.types import PRURelation

logger = logging.getLogger(__name__)


class TextPRUExtractor:
    """
    Extract PRU relations from text using LLM.
    Uses Claude to identify entities and their relationships.
    """

    PRU_EXTRACTION_PROMPT = """Analyze this text and extract relational primitives (PRUs).

PRU Types:
1. PRU-1 (Co-presence): Entities that appear together or are structurally related
2. PRU-2 (Sequentiality): One entity/event precedes another (temporal causality)
3. PRU-3 (Modulation): One entity affects or modulates properties of another
4. PRU-4 (Containment): One entity is contained within another (spatial/hierarchical)
5. PRU-5 (Disjunction): Entities are mutually exclusive (either A or B)

Text to analyze:
{text}

Extract:
1. All meaningful entities (objects, concepts, events)
2. Relationships between entities according to PRU types above

Return JSON format:
{{
  "entities": ["entity1", "entity2", ...],
  "relations": [
    {{
      "entity_a": "entity1",
      "entity_b": "entity2",
      "pru_type": "PRU-2",
      "confidence": 0.9,
      "evidence": "brief explanation"
    }},
    ...
  ]
}}

Important:
- Only extract relations you're confident about (confidence > 0.7)
- Use entity names exactly as they appear in text (or normalized form)
- Provide brief evidence for each relation
- If no clear relations exist, return empty relations array"""

    def __init__(
        self,
        entity_resolver: MultimodalEntityResolver,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize text extractor.

        Args:
            entity_resolver: Entity resolver for cross-modal linking
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.resolver = entity_resolver
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var "
                "or pass api_key parameter"
            )

        # Support custom base_url for local/proxy servers
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        if base_url:
            self.client = Anthropic(api_key=self.api_key, base_url=base_url)
        else:
            self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def extract(self, text: str) -> List[PRURelation]:
        """
        Extract PRU relations from text.

        Args:
            text: Input text to analyze

        Returns:
            List of PRURelation objects
        """
        logger.info(f"Extracting PRUs from text ({len(text)} chars)")

        try:
            # Step 1: Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": self.PRU_EXTRACTION_PROMPT.format(text=text)
                }]
            )

            # Step 2: Parse response
            result_text = response.content[0].text

            # Extract JSON from response (might be wrapped in markdown)
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1]
                result_text = result_text.split("```")[0]
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                result_text = result_text.split("```")[0]

            parsed = json.loads(result_text.strip())

            logger.info(f"LLM extracted {len(parsed['entities'])} entities, "
                       f"{len(parsed['relations'])} relations")

            # Step 3: Resolve entities to IDs
            entity_ids = {}
            for entity_text in parsed["entities"]:
                entity_id = self.resolver.resolve_entity(
                    entity_text,
                    modality="text"
                )
                entity_ids[entity_text] = entity_id

            # Step 4: Create PRURelation objects
            pru_relations = []
            for rel in parsed["relations"]:
                try:
                    # Validate PRU type
                    if rel["pru_type"] not in PRURelation.VALID_PRU_TYPES:
                        logger.warning(f"Invalid PRU type: {rel['pru_type']}, skipping")
                        continue

                    # Validate confidence
                    confidence = float(rel["confidence"])
                    if confidence < 0.7:
                        logger.debug(f"Low confidence ({confidence}), skipping relation")
                        continue

                    # Get entity IDs
                    entity_a = rel["entity_a"]
                    entity_b = rel["entity_b"]

                    if entity_a not in entity_ids or entity_b not in entity_ids:
                        logger.warning(f"Entity not found: {entity_a} or {entity_b}")
                        continue

                    pru_relation = PRURelation(
                        entity_a_id=entity_ids[entity_a],
                        entity_b_id=entity_ids[entity_b],
                        pru_type=rel["pru_type"],
                        confidence=confidence,
                        metadata={
                            "source": "text_llm",
                            "evidence": rel.get("evidence", ""),
                            "text_snippet": text[:200]  # Store snippet for context
                        }
                    )

                    pru_relations.append(pru_relation)

                except Exception as e:
                    logger.error(f"Failed to create PRU relation: {e}")
                    continue

            logger.info(f"Created {len(pru_relations)} valid PRU relations")
            return pru_relations

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {result_text}")
            return []

        except Exception as e:
            logger.error(f"Failed to extract PRUs from text: {e}")
            return []

    def extract_batch(self, texts: List[str]) -> Dict[int, List[PRURelation]]:
        """
        Extract PRUs from multiple texts.

        Args:
            texts: List of text strings

        Returns:
            Dict mapping text index to list of PRURelations
        """
        results = {}

        for i, text in enumerate(texts):
            logger.info(f"Processing text {i+1}/{len(texts)}")
            results[i] = self.extract(text)

        total_relations = sum(len(rels) for rels in results.values())
        logger.info(f"Batch extraction complete: {total_relations} total relations "
                   f"from {len(texts)} texts")

        return results

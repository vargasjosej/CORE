"""
RAG interface for PRU Knowledge Base.
Natural language queries → Cypher → LLM reasoning.
REAL implementation using Claude API.
"""
import logging
import os
import json
from typing import List, Dict, Optional
from anthropic import Anthropic

from ..core.pru_knowledge_base import PRUKnowledgeBase
from ..core.entity_resolver import MultimodalEntityResolver

logger = logging.getLogger(__name__)


class PRURAG:
    """
    Retrieval-Augmented Generation over PRU knowledge graph.

    Query flow:
    1. User question (NL) → Extract mentioned entities
    2. Query PRU graph for relevant relations
    3. Format PRU context for LLM
    4. LLM generates answer using PRU knowledge
    """

    NL_TO_CYPHER_PROMPT = """You are a Cypher query generator for a PRU knowledge graph.

PRU Types:
- PRU_1: Co-presence (entities appear together)
- PRU_2: Sequentiality (A precedes B temporally)
- PRU_3: Modulation (A affects B)
- PRU_4: Containment (A contains B)
- PRU_5: Disjunction (A ⊕ B mutually exclusive)
- PRU_6: Perspective (relation changes by viewpoint)
- PRU_7: Temporal (relation evolves over time)

Schema:
- Nodes: (:Entity {{id, semantic_signature, visual_signature}})
- Relations: -[:PRU_X {{weight, confidence, metadata}}]→

User question: {question}

Generate a Cypher query to retrieve relevant PRU relations.
Focus on entities mentioned in the question.

Return ONLY the Cypher query, no explanation.

Example queries:

Q: "What happens after the sensor detects pressure?"
A: MATCH (sensor:Entity)-[r:PRU_2]->(other:Entity) WHERE sensor.semantic_signature CONTAINS 'sensor' RETURN other.semantic_signature, r.confidence, r.metadata LIMIT 10

Q: "What entities appear together with the motor?"
A: MATCH (motor:Entity)-[r:PRU_1]-(other:Entity) WHERE motor.semantic_signature CONTAINS 'motor' RETURN other.semantic_signature, type(r), r.confidence LIMIT 10

Now generate query for: {question}"""

    REASONING_PROMPT = """You are an AI assistant with access to a PRU (Universal Relational Primitives) knowledge graph.

PRU Types:
- PRU-1: Co-presence - entities appear together
- PRU-2: Sequentiality - A precedes B temporally
- PRU-3: Modulation - A affects/modulates B
- PRU-4: Containment - A is inside B
- PRU-5: Disjunction - A and B are mutually exclusive
- PRU-6: Perspective - relation changes by viewpoint
- PRU-7: Temporal - relation evolves over time

Retrieved PRU knowledge:
{pru_context}

User question: {question}

Instructions:
1. Analyze the PRU relations provided
2. Explain what the relations mean
3. Answer the user's question using this knowledge
4. If knowledge is insufficient, say so clearly
5. Cite specific PRU relations when relevant (e.g., "According to PRU-2 relation...")

Answer:"""

    def __init__(
        self,
        knowledge_base: PRUKnowledgeBase,
        entity_resolver: MultimodalEntityResolver,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize RAG system.

        Args:
            knowledge_base: PRU knowledge base
            entity_resolver: Entity resolver
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.kb = knowledge_base
        self.resolver = entity_resolver
        self.model = model

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

    def query(self, question: str, max_context_relations: int = 20) -> Dict:
        """
        Answer a question using PRU knowledge base.

        Args:
            question: Natural language question
            max_context_relations: Max PRU relations to include in context

        Returns:
            Dict with answer, cypher query, and retrieved PRUs
        """
        logger.info(f"RAG query: {question}")

        try:
            # Step 1: Generate Cypher query
            cypher_query = self._generate_cypher(question)
            logger.info(f"Generated Cypher: {cypher_query}")

            # Step 2: Execute query on knowledge base
            pru_results = self._execute_cypher(cypher_query, max_context_relations)
            logger.info(f"Retrieved {len(pru_results)} PRU relations")

            # Step 3: Format PRU context
            pru_context = self._format_pru_context(pru_results)

            # Step 4: LLM reasoning with PRU context
            answer = self._generate_answer(question, pru_context)

            return {
                "answer": answer,
                "cypher_query": cypher_query,
                "retrieved_prus": pru_results,
                "pru_count": len(pru_results)
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "cypher_query": None,
                "retrieved_prus": [],
                "pru_count": 0
            }

    def _generate_cypher(self, question: str) -> str:
        """Generate Cypher query from natural language question."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": self.NL_TO_CYPHER_PROMPT.format(question=question)
            }]
        )

        cypher = response.content[0].text.strip()

        # Clean up markdown code blocks if present
        if cypher.startswith("```"):
            cypher = cypher.split("```")[1]
            if cypher.startswith("cypher"):
                cypher = cypher[6:]
            cypher = cypher.strip()

        return cypher

    def _execute_cypher(
        self,
        cypher_query: str,
        max_results: int
    ) -> List[Dict]:
        """Execute Cypher query and return results."""
        try:
            # Add LIMIT if not present
            if "LIMIT" not in cypher_query.upper():
                cypher_query += f" LIMIT {max_results}"

            result_set = self.kb.find_pattern(cypher_query)

            # Convert result set to list of dicts
            results = []
            for row in result_set:
                if len(row) >= 3:
                    results.append({
                        "entity": row[0],
                        "relation_type": row[1] if len(row) > 1 else None,
                        "confidence": row[2] if len(row) > 2 else None,
                        "metadata": row[3] if len(row) > 3 else {}
                    })

            return results

        except Exception as e:
            logger.error(f"Cypher execution failed: {e}")
            return []

    def _format_pru_context(self, pru_results: List[Dict]) -> str:
        """Format PRU relations for LLM context."""
        if not pru_results:
            return "No relevant PRU relations found in knowledge base."

        lines = []
        for i, result in enumerate(pru_results, 1):
            entity = result.get("entity", "?")
            rel_type = result.get("relation_type", "?")
            confidence = result.get("confidence", 0)

            line = f"{i}. Relation: {rel_type}"
            line += f"\n   Entity: {entity}"
            line += f"\n   Confidence: {confidence:.2f}"

            metadata = result.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    pass

            if metadata and isinstance(metadata, dict):
                relevant_fields = ["latency_seconds", "latency_ms", "evidence", "source"]
                for field in relevant_fields:
                    if field in metadata:
                        line += f"\n   {field}: {metadata[field]}"

            lines.append(line)

        return "\n\n".join(lines)

    def _generate_answer(self, question: str, pru_context: str) -> str:
        """Generate answer using LLM with PRU context."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": self.REASONING_PROMPT.format(
                    question=question,
                    pru_context=pru_context
                )
            }]
        )

        return response.content[0].text.strip()

    def query_with_entity(
        self,
        entity_id: str,
        question_type: str = "relations"
    ) -> Dict:
        """
        Query about a specific entity.

        Args:
            entity_id: Entity ID to query
            question_type: "relations" | "incoming" | "outgoing"

        Returns:
            Dict with entity info and relations
        """
        entity = self.resolver.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity {entity_id} not found"}

        # Get relations
        if question_type == "incoming":
            direction = "incoming"
        elif question_type == "outgoing":
            direction = "outgoing"
        else:
            direction = "both"

        relations = self.kb.query_entity_relations(entity_id, direction=direction)

        return {
            "entity": {
                "id": entity.id,
                "semantic": entity.semantic_signature,
                "visual": entity.visual_signature,
                "sources": entity.sources
            },
            "relations": relations,
            "relation_count": len(relations)
        }

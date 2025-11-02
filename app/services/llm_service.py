import time
from typing import Any, Dict, List, Tuple

import tiktoken
from openai import OpenAI, RateLimitError, APIError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class LLMService:
    """
    Handles LLM interactions for Q&A and completeness checks.
    Implements retry logic and token management.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize tokenizer for token counting
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=60),
        retry=retry_if_exception_type((RateLimitError, APIError)),
    )
    def answer_question(
        self, question: str, context_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """
        Answer a question using RAG approach.

        Args:
            question: User's question
            context_chunks: Retrieved context chunks

        Returns:
            Tuple of (answer, confidence_score)
        """
        # Build context from chunks
        context = self._build_context(context_chunks)

        # Create prompt
        prompt = f"""You are a helpful AI assistant. Answer the question based on the provided context.
If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context}

Question: {question}

Answer:"""

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable assistant that answers questions based on provided context. Be concise and cite information when possible.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        answer = response.choices[0].message.content.strip()

        # Estimate confidence based on finish reason and response
        confidence = self._estimate_confidence(response, answer, context_chunks)

        return answer, confidence

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=60),
        retry=retry_if_exception_type((RateLimitError, APIError)),
    )
    def check_completeness(
        self, topic: str, context_chunks: List[Dict[str, Any]], required_aspects: List[str] = None
    ) -> Dict[str, Any]:
        """
        Check if the knowledge base has complete information on a topic.

        Args:
            topic: Topic to check
            context_chunks: Retrieved relevant chunks
            required_aspects: Specific aspects to verify (optional)

        Returns:
            Completeness assessment
        """
        context = self._build_context(context_chunks)

        aspects_prompt = ""
        if required_aspects:
            aspects_list = "\n".join(f"- {aspect}" for aspect in required_aspects)
            aspects_prompt = f"\n\nSpecifically check for these aspects:\n{aspects_list}"

        prompt = f"""Analyze the following context to determine if it provides complete information about: {topic}

Context:
{context}
{aspects_prompt}

Provide your assessment in the following format:
1. Overall completeness score (0-100)
2. List of covered aspects (bullet points)
3. List of missing or unclear aspects (bullet points)
4. Recommendations for additional information needed (bullet points)

Assessment:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an analytical assistant that assesses information completeness. Be thorough and specific.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=0.3,  # Lower temperature for more consistent analysis
        )

        assessment_text = response.choices[0].message.content.strip()

        # Parse the response (simplified parsing)
        return self._parse_completeness_response(assessment_text, required_aspects)

    def _build_context(self, chunks: List[Dict[str, Any]], max_tokens: int = 3000) -> str:
        """
        Build context string from chunks, respecting token limits.

        Args:
            chunks: Context chunks
            max_tokens: Maximum tokens for context

        Returns:
            Formatted context string
        """
        context_parts = []
        total_tokens = 0

        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            source = chunk.get("metadata", {}).get("filename", "Unknown")

            chunk_text = f"[Source {i+1}: {source}]\n{content}\n"
            chunk_tokens = self.count_tokens(chunk_text)

            if total_tokens + chunk_tokens > max_tokens:
                break

            context_parts.append(chunk_text)
            total_tokens += chunk_tokens

        return "\n---\n".join(context_parts)

    def _estimate_confidence(
        self, response: Any, answer: str, chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Estimate confidence in the answer.

        Simple heuristic based on:
        - Finish reason (complete vs truncated)
        - Number of context chunks available
        - Presence of uncertainty phrases in answer
        """
        confidence = 0.7  # Base confidence

        # Check finish reason
        if response.choices[0].finish_reason == "stop":
            confidence += 0.1

        # More context chunks = higher confidence (up to a point)
        chunk_bonus = min(len(chunks) * 0.05, 0.15)
        confidence += chunk_bonus

        # Check for uncertainty phrases
        uncertainty_phrases = [
            "i don't know",
            "not sure",
            "unclear",
            "insufficient information",
            "cannot determine",
            "not enough context",
            "doesn't contain",
        ]

        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in uncertainty_phrases):
            confidence -= 0.3

        return max(0.0, min(1.0, confidence))

    def _extract_score(self, lines: List[str]) -> float:
        """Extract the completeness score from response lines."""
        import re

        score = 50.0  # Default score
        for line in lines:
            if "score" in line.lower():
                numbers = re.findall(r"\b(\d{1,3})\b", line)
                if numbers:
                    score = float(numbers[0])
                    break
        return score

    def _identify_section(self, line: str) -> str:
        """Identify which section a line belongs to."""
        line_lower = line.lower()
        if "covered" in line_lower:
            return "covered"
        elif "missing" in line_lower or "unclear" in line_lower:
            return "missing"
        elif "recommendation" in line_lower:
            return "recommendations"
        return None

    def _is_list_item(self, line: str) -> bool:
        """Check if a line is a list item."""
        return line.startswith("-") or line.startswith("•") or line[0].isdigit()

    def _clean_list_item(self, line: str) -> str:
        """Clean a list item by removing bullets and numbers."""
        return line.lstrip("-•0123456789. ").strip()

    def _parse_sections(self, lines: List[str]) -> Tuple[List[str], List[str], List[str]]:
        """Parse the sections of the response."""
        covered = []
        missing = []
        recommendations = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            section = self._identify_section(line)
            if section:
                current_section = section
            elif self._is_list_item(line):
                item = self._clean_list_item(line)
                if current_section == "covered":
                    covered.append(item)
                elif current_section == "missing":
                    missing.append(item)
                elif current_section == "recommendations":
                    recommendations.append(item)

        return covered, missing, recommendations

    def _parse_completeness_response(
        self, text: str, required_aspects: List[str] = None
    ) -> Dict[str, Any]:
        """Parse the completeness assessment response."""
        lines = text.split("\n")

        # Extract score
        score = self._extract_score(lines)

        # Parse sections
        covered, missing, recommendations = self._parse_sections(lines)

        return {
            "score": score / 100.0,  # Normalize to 0-1
            "covered_aspects": covered,
            "missing_aspects": missing,
            "recommendations": recommendations,
        }

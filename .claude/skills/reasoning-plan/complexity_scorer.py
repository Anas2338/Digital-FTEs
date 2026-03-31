"""Complexity detection algorithm for task analysis.

Uses multi-factor heuristic to determine if a task requires structured planning:
- Word count (longer tasks are more complex)
- Action verb count (more actions = more steps)
- Dependency indicators (words like "after", "before", "depends on")
- Technical terms (API, database, integration, etc.)
- Conditional logic (if/then, when, unless)
"""

import re
from typing import Dict, Any, List
from pathlib import Path


class ComplexityScorer:
    """Scorer for task complexity analysis."""

    def __init__(self, threshold: int = 25):
        """Initialize complexity scorer.

        Args:
            threshold: Complexity score threshold (default: 25)
                      Tasks scoring >= threshold require planning
        """
        self.threshold = threshold

        # Action verbs that indicate discrete steps
        self.action_verbs = [
            'create', 'implement', 'build', 'develop', 'design', 'write',
            'update', 'modify', 'refactor', 'test', 'deploy', 'configure',
            'integrate', 'connect', 'setup', 'install', 'migrate', 'optimize',
            'validate', 'verify', 'analyze', 'research', 'investigate',
            'document', 'review', 'approve', 'schedule', 'monitor', 'track'
        ]

        # Dependency indicators
        self.dependency_words = [
            'after', 'before', 'depends on', 'requires', 'needs', 'must',
            'prerequisite', 'first', 'then', 'next', 'finally', 'once',
            'when', 'if', 'unless', 'until', 'following'
        ]

        # Technical complexity indicators
        self.technical_terms = [
            'api', 'database', 'integration', 'authentication', 'authorization',
            'endpoint', 'service', 'microservice', 'architecture', 'infrastructure',
            'deployment', 'migration', 'schema', 'model', 'controller', 'middleware',
            'webhook', 'queue', 'cache', 'session', 'token', 'encryption',
            'validation', 'serialization', 'transaction', 'rollback'
        ]

        # Conditional logic indicators
        self.conditional_words = [
            'if', 'then', 'else', 'when', 'unless', 'in case', 'otherwise',
            'depending on', 'based on', 'according to', 'conditional'
        ]

    def score(self, task_description: str) -> Dict[str, Any]:
        """Calculate complexity score for a task.

        Args:
            task_description: Task description text

        Returns:
            Score dict with total score and breakdown by factor
        """
        text_lower = task_description.lower()
        words = text_lower.split()
        word_count = len(words)

        # Factor 1: Word count (1 point per 20 words)
        word_score = word_count // 20

        # Factor 2: Action verb count (2 points per verb)
        action_count = sum(1 for verb in self.action_verbs if verb in text_lower)
        action_score = action_count * 2

        # Factor 3: Dependency indicators (3 points per indicator)
        dependency_count = sum(1 for word in self.dependency_words if word in text_lower)
        dependency_score = dependency_count * 3

        # Factor 4: Technical terms (2 points per term)
        technical_count = sum(1 for term in self.technical_terms if term in text_lower)
        technical_score = technical_count * 2

        # Factor 5: Conditional logic (3 points per conditional)
        conditional_count = sum(1 for word in self.conditional_words if word in text_lower)
        conditional_score = conditional_count * 3

        # Factor 6: Multiple sentences (1 point per sentence beyond first)
        sentence_count = len(re.findall(r'[.!?]+', task_description))
        sentence_score = max(0, sentence_count - 1)

        # Factor 7: List items (2 points per list item)
        list_items = len(re.findall(r'^\s*[-*•]\s+', task_description, re.MULTILINE))
        list_score = list_items * 2

        # Calculate total score
        total_score = (
            word_score +
            action_score +
            dependency_score +
            technical_score +
            conditional_score +
            sentence_score +
            list_score
        )

        # Determine if planning is required
        requires_planning = total_score >= self.threshold

        return {
            "total_score": total_score,
            "threshold": self.threshold,
            "requires_planning": requires_planning,
            "breakdown": {
                "word_count": word_count,
                "word_score": word_score,
                "action_count": action_count,
                "action_score": action_score,
                "dependency_count": dependency_count,
                "dependency_score": dependency_score,
                "technical_count": technical_count,
                "technical_score": technical_score,
                "conditional_count": conditional_count,
                "conditional_score": conditional_score,
                "sentence_count": sentence_count,
                "sentence_score": sentence_score,
                "list_items": list_items,
                "list_score": list_score
            },
            "complexity_level": self._get_complexity_level(total_score)
        }

    def _get_complexity_level(self, score: int) -> str:
        """Get human-readable complexity level.

        Args:
            score: Complexity score

        Returns:
            Complexity level string
        """
        if score < 10:
            return "trivial"
        elif score < 25:
            return "simple"
        elif score < 50:
            return "moderate"
        elif score < 75:
            return "complex"
        else:
            return "very_complex"

    def analyze_task_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a task file and return complexity score.

        Args:
            file_path: Path to task file

        Returns:
            Analysis dict with score and metadata
        """
        try:
            content = Path(file_path).read_text(encoding='utf-8')

            # Extract task description (skip frontmatter)
            description = self._extract_description(content)

            # Score the task
            score_result = self.score(description)

            return {
                "file_path": file_path,
                "description_length": len(description),
                **score_result
            }

        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "total_score": 0,
                "requires_planning": False
            }

    def _extract_description(self, content: str) -> str:
        """Extract task description from markdown content.

        Args:
            content: Full markdown content

        Returns:
            Task description without frontmatter
        """
        # Remove YAML frontmatter if present
        content_without_fm = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content,
                                    count=1, flags=re.DOTALL)
        return content_without_fm.strip()


if __name__ == "__main__":
    # Example usage
    scorer = ComplexityScorer(threshold=25)

    # Test cases
    test_cases = [
        {
            "name": "Simple task",
            "description": "Update the README file with installation instructions"
        },
        {
            "name": "Moderate task",
            "description": """Implement user authentication system:
            - Create login endpoint
            - Add JWT token generation
            - Implement password hashing
            - Add session management"""
        },
        {
            "name": "Complex task",
            "description": """Build a microservices architecture for the payment system.
            First, design the API gateway to handle routing. Then, implement the payment
            service with Stripe integration. After that, create the order service that
            depends on the payment service. Finally, add monitoring and logging across
            all services. If the payment fails, implement rollback logic. When the
            transaction completes, send confirmation emails."""
        }
    ]

    print("Complexity Scoring Examples\n" + "="*60)

    for test in test_cases:
        result = scorer.score(test["description"])
        print(f"\n{test['name']}:")
        print(f"Score: {result['total_score']} (threshold: {result['threshold']})")
        print(f"Requires Planning: {result['requires_planning']}")
        print(f"Complexity Level: {result['complexity_level']}")
        print(f"Breakdown:")
        for key, value in result['breakdown'].items():
            if not key.endswith('_count') and not key.endswith('_items'):
                print(f"  {key}: {value}")

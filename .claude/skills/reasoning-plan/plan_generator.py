"""Plan.md generator for complex tasks.

Generates structured execution plans with:
- Goal and context
- Sequential steps with dependencies
- Success criteria per step and overall
- Risk assessment
- Rollback procedures
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class PlanGenerator:
    """Generator for structured task execution plans."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize plan generator.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action_dir = self.vault_path / "Needs_Action"

    def generate(self, task_description: str, task_id: Optional[str] = None,
                complexity_score: Optional[int] = None) -> str:
        """Generate a Plan.md for a task.

        Args:
            task_description: Task description text
            task_id: Optional task identifier
            complexity_score: Optional complexity score

        Returns:
            Plan content as markdown string
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = f"task-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Extract goal from task description
        goal = self._extract_goal(task_description)

        # Extract context
        context = self._extract_context(task_description)

        # Generate steps
        steps = self._generate_steps(task_description)

        # Generate success criteria
        success_criteria = self._generate_success_criteria(task_description, steps)

        # Identify risks
        risks = self._identify_risks(task_description, steps)

        # Generate rollback procedure
        rollback = self._generate_rollback(task_description, steps)

        # Build plan content
        plan_content = self._build_plan_markdown(
            task_id=task_id,
            goal=goal,
            context=context,
            steps=steps,
            success_criteria=success_criteria,
            risks=risks,
            rollback=rollback,
            complexity_score=complexity_score
        )

        return plan_content

    def _extract_goal(self, task_description: str) -> str:
        """Extract goal from task description.

        Args:
            task_description: Task description

        Returns:
            Goal statement
        """
        # Take first sentence as goal
        sentences = re.split(r'[.!?]+', task_description)
        if sentences:
            goal = sentences[0].strip()
            # Make it imperative if not already
            if not goal.lower().startswith(('implement', 'create', 'build', 'develop')):
                goal = f"Complete: {goal}"
            return goal
        return "Complete the specified task"

    def _extract_context(self, task_description: str) -> str:
        """Extract context from task description.

        Args:
            task_description: Task description

        Returns:
            Context information
        """
        # Use everything after first sentence as context
        sentences = re.split(r'[.!?]+', task_description, maxsplit=1)
        if len(sentences) > 1:
            return sentences[1].strip()
        return "No additional context provided."

    def _generate_steps(self, task_description: str) -> List[Dict[str, Any]]:
        """Generate execution steps from task description.

        Args:
            task_description: Task description

        Returns:
            List of step dicts
        """
        steps = []

        # Check for explicit list items
        list_items = re.findall(r'^\s*[-*•]\s+(.+)$', task_description, re.MULTILINE)

        if list_items:
            # Use explicit list items as steps
            for i, item in enumerate(list_items, 1):
                steps.append({
                    "number": i,
                    "name": item.strip(),
                    "description": item.strip(),
                    "status": "pending",
                    "estimated_time": "30 minutes",
                    "dependencies": [] if i == 1 else [i - 1],
                    "success_criteria": [f"{item.strip()} completed successfully"]
                })
        else:
            # Generate steps from action verbs
            action_verbs = [
                'create', 'implement', 'build', 'develop', 'design', 'write',
                'update', 'modify', 'refactor', 'test', 'deploy', 'configure',
                'integrate', 'setup', 'install'
            ]

            # Find sentences with action verbs
            sentences = re.split(r'[.!?]+', task_description)
            step_num = 1

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Check if sentence contains action verb
                has_action = any(verb in sentence.lower() for verb in action_verbs)

                if has_action:
                    steps.append({
                        "number": step_num,
                        "name": sentence[:50] + "..." if len(sentence) > 50 else sentence,
                        "description": sentence,
                        "status": "pending",
                        "estimated_time": "1 hour",
                        "dependencies": [] if step_num == 1 else [step_num - 1],
                        "success_criteria": [f"Step {step_num} completed"]
                    })
                    step_num += 1

        # If no steps generated, create generic steps
        if not steps:
            steps = [
                {
                    "number": 1,
                    "name": "Analyze requirements",
                    "description": "Review task requirements and constraints",
                    "status": "pending",
                    "estimated_time": "30 minutes",
                    "dependencies": [],
                    "success_criteria": ["Requirements documented"]
                },
                {
                    "number": 2,
                    "name": "Implement solution",
                    "description": task_description,
                    "status": "pending",
                    "estimated_time": "2 hours",
                    "dependencies": [1],
                    "success_criteria": ["Implementation complete"]
                },
                {
                    "number": 3,
                    "name": "Test and validate",
                    "description": "Test implementation and validate results",
                    "status": "pending",
                    "estimated_time": "1 hour",
                    "dependencies": [2],
                    "success_criteria": ["All tests passing"]
                }
            ]

        return steps

    def _generate_success_criteria(self, task_description: str,
                                   steps: List[Dict[str, Any]]) -> List[str]:
        """Generate overall success criteria.

        Args:
            task_description: Task description
            steps: Generated steps

        Returns:
            List of success criteria
        """
        criteria = [
            "All steps completed",
            "All tests passing",
            "Documentation updated"
        ]

        # Add task-specific criteria based on keywords
        text_lower = task_description.lower()

        if 'api' in text_lower or 'endpoint' in text_lower:
            criteria.append("API endpoints functional and tested")

        if 'database' in text_lower or 'migration' in text_lower:
            criteria.append("Database schema updated and migrated")

        if 'authentication' in text_lower or 'auth' in text_lower:
            criteria.append("Authentication flow tested and secure")

        if 'integration' in text_lower:
            criteria.append("Integration tests passing")

        if 'deploy' in text_lower:
            criteria.append("Deployment successful")

        return criteria

    def _identify_risks(self, task_description: str,
                       steps: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identify potential risks.

        Args:
            task_description: Task description
            steps: Generated steps

        Returns:
            List of risk dicts
        """
        risks = []
        text_lower = task_description.lower()

        # Common risks based on keywords
        if 'api' in text_lower:
            risks.append({
                "risk": "API rate limiting",
                "likelihood": "Medium",
                "impact": "Medium",
                "mitigation": "Implement exponential backoff and caching"
            })

        if 'database' in text_lower or 'migration' in text_lower:
            risks.append({
                "risk": "Data loss during migration",
                "likelihood": "Low",
                "impact": "High",
                "mitigation": "Backup database before migration, test on staging first"
            })

        if 'authentication' in text_lower or 'auth' in text_lower:
            risks.append({
                "risk": "Security vulnerabilities",
                "likelihood": "Medium",
                "impact": "High",
                "mitigation": "Security audit, use established libraries, follow OWASP guidelines"
            })

        if 'integration' in text_lower:
            risks.append({
                "risk": "Third-party service downtime",
                "likelihood": "Low",
                "impact": "Medium",
                "mitigation": "Implement fallback mechanisms and error handling"
            })

        # Generic risks
        risks.append({
            "risk": "Scope creep",
            "likelihood": "Medium",
            "impact": "Medium",
            "mitigation": "Stick to defined success criteria, defer enhancements"
        })

        return risks

    def _generate_rollback(self, task_description: str,
                          steps: List[Dict[str, Any]]) -> List[str]:
        """Generate rollback procedure.

        Args:
            task_description: Task description
            steps: Generated steps

        Returns:
            List of rollback steps
        """
        rollback_steps = []
        text_lower = task_description.lower()

        if 'database' in text_lower or 'migration' in text_lower:
            rollback_steps.append("Revert database migrations")

        if 'api' in text_lower or 'endpoint' in text_lower:
            rollback_steps.append("Remove new API endpoints from routes")

        if 'deploy' in text_lower:
            rollback_steps.append("Rollback deployment to previous version")

        if 'config' in text_lower:
            rollback_steps.append("Restore previous configuration")

        # Generic rollback steps
        rollback_steps.extend([
            "Revert code changes via git",
            "Clear caches if applicable",
            "Notify stakeholders of rollback"
        ])

        return rollback_steps

    def _build_plan_markdown(self, task_id: str, goal: str, context: str,
                            steps: List[Dict[str, Any]],
                            success_criteria: List[str],
                            risks: List[Dict[str, str]],
                            rollback: List[str],
                            complexity_score: Optional[int] = None) -> str:
        """Build plan markdown content.

        Args:
            task_id: Task identifier
            goal: Goal statement
            context: Context information
            steps: Execution steps
            success_criteria: Success criteria
            risks: Risk assessment
            rollback: Rollback procedure
            complexity_score: Complexity score

        Returns:
            Plan markdown content
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Build frontmatter
        frontmatter = {
            "task_id": task_id,
            "status": "draft",
            "created": timestamp,
            "updated": timestamp
        }

        if complexity_score is not None:
            frontmatter["complexity_score"] = complexity_score

        # Build markdown
        md = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n"
        md += f"# Plan: {goal}\n\n"
        md += f"## Goal\n\n{goal}\n\n"
        md += f"## Context\n\n{context}\n\n"
        md += "## Steps\n\n"

        # Add steps
        for step in steps:
            md += f"### Step {step['number']}: {step['name']}\n"
            md += f"**Status**: {step['status']}\n"
            md += f"**Estimated Time**: {step['estimated_time']}\n"

            if step['dependencies']:
                deps = ", ".join(f"Step {d}" for d in step['dependencies'])
                md += f"**Dependencies**: {deps}\n"
            else:
                md += "**Dependencies**: None\n"

            md += f"\n{step['description']}\n\n"
            md += "**Success Criteria:**\n"
            for criterion in step['success_criteria']:
                md += f"- [ ] {criterion}\n"
            md += "\n---\n\n"

        # Add success criteria
        md += "## Success Criteria\n\n"
        md += "Overall task completion requires:\n\n"
        for criterion in success_criteria:
            md += f"- [ ] {criterion}\n"
        md += "\n"

        # Add risks
        md += "## Risks\n\n"
        md += "| Risk | Likelihood | Impact | Mitigation |\n"
        md += "|------|------------|--------|------------|\n"
        for risk in risks:
            md += f"| {risk['risk']} | {risk['likelihood']} | {risk['impact']} | {risk['mitigation']} |\n"
        md += "\n"

        # Add rollback
        md += "## Rollback Procedure\n\n"
        md += "If task fails or needs to be reverted:\n\n"
        for i, step in enumerate(rollback, 1):
            md += f"{i}. {step}\n"
        md += "\n"

        # Add lessons learned section
        md += "## Lessons Learned\n\n"
        md += "[To be added during execution or re-evaluation]\n"

        return md

    def save_plan(self, plan_content: str, task_file_path: str) -> str:
        """Save plan to file alongside task.

        Args:
            plan_content: Plan markdown content
            task_file_path: Path to task file

        Returns:
            Path to saved plan file
        """
        task_path = Path(task_file_path)
        plan_path = task_path.parent / f"{task_path.stem}-plan.md"

        plan_path.write_text(plan_content, encoding='utf-8')

        return str(plan_path)


if __name__ == "__main__":
    # Example usage
    generator = PlanGenerator()

    task_description = """Implement OAuth2 authentication with Google and GitHub providers.

    The system needs to support multiple OAuth providers for user login.
    Users should be able to link multiple accounts.

    - Create OAuth provider configuration
    - Implement authorization endpoint
    - Add token exchange logic
    - Store user credentials securely
    - Test with both providers"""

    plan = generator.generate(task_description, complexity_score=52)

    print(plan)

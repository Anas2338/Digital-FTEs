"""Plan re-evaluator for handling failures and requirement changes.

When a plan step fails or requirements change, this module:
- Analyzes failure reason
- Researches alternative approaches
- Updates plan with new steps
- Preserves completed work
- Documents lessons learned
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from claude.skills.reasoning_plan.plan_executor import PlanExecutor
from claude.skills.reasoning_plan.plan_generator import PlanGenerator
from claude.skills.reasoning_plan.config import MAX_REEVALUATIONS


class PlanReEvaluator:
    """Re-evaluator for failed or changed plans."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize plan re-evaluator.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.executor = PlanExecutor(str(vault_path))
        self.generator = PlanGenerator(str(vault_path))
        self.max_reevaluations = MAX_REEVALUATIONS

    def re_evaluate(self, plan_file_path: str, failure_reason: str,
                   failed_step_num: Optional[int] = None) -> Dict[str, Any]:
        """Re-evaluate a plan after failure or requirement change.

        Args:
            plan_file_path: Path to plan file
            failure_reason: Reason for re-evaluation
            failed_step_num: Optional step number that failed

        Returns:
            Re-evaluation result dict
        """
        # Load current plan
        plan = self.executor.load_plan(plan_file_path)

        # Check re-evaluation count
        reevaluation_count = plan["frontmatter"].get("reevaluation_count", 0)

        if reevaluation_count >= self.max_reevaluations:
            return {
                "success": False,
                "error": f"Max re-evaluations ({self.max_reevaluations}) exceeded",
                "recommendation": "Consider breaking task into smaller subtasks"
            }

        # Analyze failure
        analysis = self._analyze_failure(failure_reason, failed_step_num, plan)

        # Generate alternative approach
        alternative = self._generate_alternative_approach(
            analysis, plan, failed_step_num
        )

        # Update plan with alternative
        updated_plan = self._update_plan_with_alternative(
            plan_file_path, alternative, failure_reason, reevaluation_count
        )

        return {
            "success": True,
            "analysis": analysis,
            "alternative_approach": alternative,
            "reevaluation_count": reevaluation_count + 1,
            "updated_plan_path": updated_plan
        }

    def _analyze_failure(self, failure_reason: str, failed_step_num: Optional[int],
                        plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze failure reason and context.

        Args:
            failure_reason: Reason for failure
            failed_step_num: Failed step number
            plan: Plan dict

        Returns:
            Analysis dict
        """
        analysis = {
            "failure_reason": failure_reason,
            "failed_step": failed_step_num,
            "failure_category": self._categorize_failure(failure_reason),
            "completed_steps": [s for s in plan["steps"] if s["status"] in ["completed", "validated"]],
            "remaining_steps": [s for s in plan["steps"] if s["status"] == "pending"]
        }

        # Identify root cause
        if "api" in failure_reason.lower() and "deprecat" in failure_reason.lower():
            analysis["root_cause"] = "API version deprecated"
            analysis["suggested_fix"] = "Migrate to newer API version"
        elif "rate limit" in failure_reason.lower():
            analysis["root_cause"] = "Rate limiting"
            analysis["suggested_fix"] = "Implement exponential backoff and caching"
        elif "timeout" in failure_reason.lower():
            analysis["root_cause"] = "Operation timeout"
            analysis["suggested_fix"] = "Optimize query or increase timeout"
        elif "permission" in failure_reason.lower() or "auth" in failure_reason.lower():
            analysis["root_cause"] = "Authentication/authorization issue"
            analysis["suggested_fix"] = "Verify credentials and permissions"
        else:
            analysis["root_cause"] = "Unknown"
            analysis["suggested_fix"] = "Investigate error logs and stack trace"

        return analysis

    def _categorize_failure(self, failure_reason: str) -> str:
        """Categorize failure type.

        Args:
            failure_reason: Failure reason text

        Returns:
            Failure category
        """
        reason_lower = failure_reason.lower()

        if any(word in reason_lower for word in ["deprecat", "obsolete", "removed"]):
            return "deprecated_dependency"
        elif any(word in reason_lower for word in ["rate limit", "quota", "throttle"]):
            return "rate_limiting"
        elif any(word in reason_lower for word in ["timeout", "slow", "hang"]):
            return "performance"
        elif any(word in reason_lower for word in ["permission", "auth", "forbidden", "unauthorized"]):
            return "authorization"
        elif any(word in reason_lower for word in ["not found", "missing", "404"]):
            return "missing_resource"
        elif any(word in reason_lower for word in ["conflict", "duplicate", "exists"]):
            return "conflict"
        else:
            return "unknown"

    def _generate_alternative_approach(self, analysis: Dict[str, Any],
                                      plan: Dict[str, Any],
                                      failed_step_num: Optional[int]) -> Dict[str, Any]:
        """Generate alternative approach based on failure analysis.

        Args:
            analysis: Failure analysis
            plan: Current plan
            failed_step_num: Failed step number

        Returns:
            Alternative approach dict
        """
        alternative = {
            "approach_name": f"Alternative approach (v{plan['frontmatter'].get('reevaluation_count', 0) + 2})",
            "rationale": analysis["suggested_fix"],
            "new_steps": [],
            "modified_steps": [],
            "preserved_steps": []
        }

        # Preserve completed steps
        for step in plan["steps"]:
            if step["status"] in ["completed", "validated"]:
                alternative["preserved_steps"].append(step["number"])

        # Generate new steps for failed step
        if failed_step_num:
            failed_step = next((s for s in plan["steps"] if s["number"] == failed_step_num), None)

            if failed_step:
                # Create alternative step(s) based on failure category
                if analysis["failure_category"] == "deprecated_dependency":
                    alternative["new_steps"].append({
                        "number": failed_step_num,
                        "name": f"Migrate to newer version: {failed_step['name']}",
                        "description": f"Update implementation to use newer API version. Original approach: {failed_step['name']}",
                        "status": "pending"
                    })
                elif analysis["failure_category"] == "rate_limiting":
                    alternative["new_steps"].extend([
                        {
                            "number": failed_step_num,
                            "name": "Implement rate limiting handler",
                            "description": "Add exponential backoff and retry logic",
                            "status": "pending"
                        },
                        {
                            "number": failed_step_num + 0.5,  # Insert between steps
                            "name": f"Retry: {failed_step['name']}",
                            "description": f"Retry original step with rate limiting: {failed_step['name']}",
                            "status": "pending"
                        }
                    ])
                elif analysis["failure_category"] == "performance":
                    alternative["new_steps"].append({
                        "number": failed_step_num,
                        "name": f"Optimize: {failed_step['name']}",
                        "description": f"Optimize implementation for better performance. Original: {failed_step['name']}",
                        "status": "pending"
                    })
                else:
                    # Generic alternative
                    alternative["new_steps"].append({
                        "number": failed_step_num,
                        "name": f"Alternative: {failed_step['name']}",
                        "description": f"Alternative implementation. Original failed due to: {analysis['failure_reason']}",
                        "status": "pending"
                    })

        return alternative

    def _update_plan_with_alternative(self, plan_file_path: str,
                                     alternative: Dict[str, Any],
                                     failure_reason: str,
                                     current_reevaluation_count: int) -> str:
        """Update plan file with alternative approach.

        Args:
            plan_file_path: Path to plan file
            alternative: Alternative approach dict
            failure_reason: Failure reason
            current_reevaluation_count: Current re-evaluation count

        Returns:
            Path to updated plan file
        """
        content = Path(plan_file_path).read_text(encoding='utf-8')

        # Parse frontmatter and content
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return plan_file_path

        frontmatter = yaml.safe_load(match.group(1))
        plan_content = match.group(2)

        # Update frontmatter
        frontmatter["reevaluation_count"] = current_reevaluation_count + 1
        frontmatter["updated"] = datetime.utcnow().isoformat() + "Z"
        frontmatter["status"] = "in_progress"  # Reset to in_progress

        # Add lessons learned section
        lessons_section = f"\n\n## Lessons Learned\n\n"
        lessons_section += f"### Re-evaluation {current_reevaluation_count + 1} ({datetime.utcnow().strftime('%Y-%m-%d')})\n\n"
        lessons_section += f"**Failure Reason**: {failure_reason}\n\n"
        lessons_section += f"**Alternative Approach**: {alternative['approach_name']}\n\n"
        lessons_section += f"**Rationale**: {alternative['rationale']}\n\n"
        lessons_section += f"**Preserved Steps**: {', '.join(f'Step {n}' for n in alternative['preserved_steps'])}\n\n"
        lessons_section += f"**New Steps**: {len(alternative['new_steps'])} step(s) added\n"

        # Check if lessons learned section exists
        if "## Lessons Learned" in plan_content:
            # Replace existing lessons learned
            plan_content = re.sub(
                r'## Lessons Learned\s*\n.*$',
                lessons_section.strip(),
                plan_content,
                flags=re.DOTALL
            )
        else:
            # Append lessons learned
            plan_content += lessons_section

        # Rebuild content
        new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{plan_content}"

        # Write back
        Path(plan_file_path).write_text(new_content, encoding='utf-8')

        return plan_file_path

    def check_reevaluation_limit(self, plan_file_path: str) -> Dict[str, Any]:
        """Check if plan has exceeded re-evaluation limit.

        Args:
            plan_file_path: Path to plan file

        Returns:
            Check result dict
        """
        plan = self.executor.load_plan(plan_file_path)
        reevaluation_count = plan["frontmatter"].get("reevaluation_count", 0)

        return {
            "count": reevaluation_count,
            "limit": self.max_reevaluations,
            "exceeded": reevaluation_count >= self.max_reevaluations,
            "remaining": max(0, self.max_reevaluations - reevaluation_count)
        }


if __name__ == "__main__":
    # Example usage
    reevaluator = PlanReEvaluator()

    # Example: Re-evaluate plan after API deprecation
    # result = reevaluator.re_evaluate(
    #     "path/to/plan.md",
    #     "Google OAuth API v1 deprecated, endpoint returns 410 Gone",
    #     failed_step_num=3
    # )
    # print(f"Re-evaluation successful: {result['success']}")
    # print(f"Alternative approach: {result['alternative_approach']['approach_name']}")

    print("PlanReEvaluator initialized.")

"""Plan executor for tracking and updating plan execution status.

Manages plan execution lifecycle:
- Update step status (pending → in-progress → completed)
- Track execution progress
- Validate success criteria
- Handle step failures
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from claude.skills.reasoning_plan.config import STEP_STATUS, PLAN_STATUS


class PlanExecutor:
    """Executor for plan status tracking and updates."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize plan executor.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)

    def load_plan(self, plan_file_path: str) -> Dict[str, Any]:
        """Load plan from file.

        Args:
            plan_file_path: Path to plan file

        Returns:
            Plan dict with frontmatter and content
        """
        content = Path(plan_file_path).read_text(encoding='utf-8')

        # Parse frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            raise ValueError("Invalid plan format: missing frontmatter")

        frontmatter = yaml.safe_load(match.group(1))
        plan_content = match.group(2)

        # Extract steps from content
        steps = self._parse_steps(plan_content)

        return {
            "file_path": plan_file_path,
            "frontmatter": frontmatter,
            "content": plan_content,
            "steps": steps
        }

    def _parse_steps(self, content: str) -> List[Dict[str, Any]]:
        """Parse steps from plan content.

        Args:
            content: Plan markdown content

        Returns:
            List of step dicts
        """
        steps = []

        # Find all step sections
        step_pattern = r'### Step (\d+): (.+?)\n\*\*Status\*\*: (\w+)'
        matches = re.finditer(step_pattern, content)

        for match in matches:
            step_num = int(match.group(1))
            step_name = match.group(2)
            step_status = match.group(3)

            # Extract success criteria for this step
            criteria = self._extract_step_criteria(content, step_num)

            steps.append({
                "number": step_num,
                "name": step_name,
                "status": step_status,
                "success_criteria": criteria
            })

        return steps

    def _extract_step_criteria(self, content: str, step_num: int) -> List[Dict[str, Any]]:
        """Extract success criteria for a specific step.

        Args:
            content: Plan content
            step_num: Step number

        Returns:
            List of criteria dicts with text and completion status
        """
        criteria = []

        # Find the step section
        step_pattern = f'### Step {step_num}:.*?(?=### Step|## Success Criteria|$)'
        match = re.search(step_pattern, content, re.DOTALL)

        if match:
            step_content = match.group(0)

            # Find criteria checkboxes
            criteria_pattern = r'- \[([ Xx])\] (.+)'
            for criterion_match in re.finditer(criteria_pattern, step_content):
                checked = criterion_match.group(1).lower() == 'x'
                text = criterion_match.group(2)

                criteria.append({
                    "text": text,
                    "completed": checked
                })

        return criteria

    def update_step_status(self, plan_file_path: str, step_num: int,
                          new_status: str) -> bool:
        """Update step status in plan file.

        Args:
            plan_file_path: Path to plan file
            step_num: Step number to update
            new_status: New status value

        Returns:
            True if updated successfully
        """
        try:
            content = Path(plan_file_path).read_text(encoding='utf-8')

            # Find and replace step status
            pattern = f'(### Step {step_num}:.*?\n\\*\\*Status\\*\\*: )\\w+'
            replacement = f'\\g<1>{new_status}'

            updated_content = re.sub(pattern, replacement, content)

            # Update plan frontmatter timestamp
            updated_content = self._update_timestamp(updated_content)

            # Write back
            Path(plan_file_path).write_text(updated_content, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error updating step status: {e}")
            return False

    def mark_criterion_complete(self, plan_file_path: str, step_num: int,
                               criterion_text: str) -> bool:
        """Mark a success criterion as complete.

        Args:
            plan_file_path: Path to plan file
            step_num: Step number
            criterion_text: Criterion text to mark complete

        Returns:
            True if updated successfully
        """
        try:
            content = Path(plan_file_path).read_text(encoding='utf-8')

            # Find the step section
            step_pattern = f'(### Step {step_num}:.*?)(- \\[ \\] {re.escape(criterion_text)})'
            replacement = f'\\g<1>- [X] {criterion_text}'

            updated_content = re.sub(step_pattern, replacement, content, flags=re.DOTALL)

            # Update timestamp
            updated_content = self._update_timestamp(updated_content)

            # Write back
            Path(plan_file_path).write_text(updated_content, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error marking criterion complete: {e}")
            return False

    def update_plan_status(self, plan_file_path: str, new_status: str) -> bool:
        """Update overall plan status in frontmatter.

        Args:
            plan_file_path: Path to plan file
            new_status: New plan status

        Returns:
            True if updated successfully
        """
        try:
            content = Path(plan_file_path).read_text(encoding='utf-8')

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return False

            frontmatter = yaml.safe_load(match.group(1))
            plan_content = match.group(2)

            # Update status and timestamp
            frontmatter["status"] = new_status
            frontmatter["updated"] = datetime.utcnow().isoformat() + "Z"

            # Rebuild content
            new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{plan_content}"

            # Write back
            Path(plan_file_path).write_text(new_content, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error updating plan status: {e}")
            return False

    def _update_timestamp(self, content: str) -> str:
        """Update the 'updated' timestamp in frontmatter.

        Args:
            content: Plan content

        Returns:
            Updated content
        """
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            return content

        frontmatter = yaml.safe_load(match.group(1))
        plan_content = match.group(2)

        frontmatter["updated"] = datetime.utcnow().isoformat() + "Z"

        return f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{plan_content}"

    def get_plan_progress(self, plan_file_path: str) -> Dict[str, Any]:
        """Get plan execution progress.

        Args:
            plan_file_path: Path to plan file

        Returns:
            Progress dict with completion percentages
        """
        plan = self.load_plan(plan_file_path)

        total_steps = len(plan["steps"])
        completed_steps = sum(1 for step in plan["steps"]
                            if step["status"] in ["completed", "validated"])

        total_criteria = sum(len(step["success_criteria"]) for step in plan["steps"])
        completed_criteria = sum(
            sum(1 for c in step["success_criteria"] if c["completed"])
            for step in plan["steps"]
        )

        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "step_progress": round((completed_steps / total_steps) * 100, 1) if total_steps > 0 else 0,
            "total_criteria": total_criteria,
            "completed_criteria": completed_criteria,
            "criteria_progress": round((completed_criteria / total_criteria) * 100, 1) if total_criteria > 0 else 0,
            "current_status": plan["frontmatter"].get("status", "unknown")
        }

    def validate_step_completion(self, plan_file_path: str, step_num: int) -> Dict[str, Any]:
        """Validate if a step is complete based on success criteria.

        Args:
            plan_file_path: Path to plan file
            step_num: Step number to validate

        Returns:
            Validation result dict
        """
        plan = self.load_plan(plan_file_path)

        # Find the step
        step = next((s for s in plan["steps"] if s["number"] == step_num), None)
        if not step:
            return {
                "valid": False,
                "error": f"Step {step_num} not found"
            }

        # Check if all criteria are met
        total_criteria = len(step["success_criteria"])
        completed_criteria = sum(1 for c in step["success_criteria"] if c["completed"])

        all_complete = completed_criteria == total_criteria

        return {
            "valid": all_complete,
            "step_num": step_num,
            "step_name": step["name"],
            "total_criteria": total_criteria,
            "completed_criteria": completed_criteria,
            "remaining_criteria": [c["text"] for c in step["success_criteria"] if not c["completed"]]
        }


if __name__ == "__main__":
    # Example usage
    executor = PlanExecutor()

    # Example: Update step status
    # executor.update_step_status("path/to/plan.md", 1, "in_progress")

    # Example: Mark criterion complete
    # executor.mark_criterion_complete("path/to/plan.md", 1, "OAuth provider configured")

    # Example: Get progress
    # progress = executor.get_plan_progress("path/to/plan.md")
    # print(f"Progress: {progress['step_progress']}% steps, {progress['criteria_progress']}% criteria")

    print("PlanExecutor initialized. Use methods to track plan execution.")

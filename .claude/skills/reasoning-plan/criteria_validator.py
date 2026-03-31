"""Success criteria validator for plan execution.

Validates that all success criteria are met before marking tasks complete.
Supports automated checks (tests, file existence) and manual validation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from claude.skills.reasoning_plan.plan_executor import PlanExecutor
from claude.skills.reasoning_plan.config import VALIDATION_TIMEOUT


class SuccessCriteriaValidator:
    """Validator for plan success criteria."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize validator.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.executor = PlanExecutor(str(vault_path))
        self.timeout = VALIDATION_TIMEOUT

    def validate_all_criteria(self, plan_file_path: str) -> Dict[str, Any]:
        """Validate all success criteria for a plan.

        Args:
            plan_file_path: Path to plan file

        Returns:
            Validation result dict
        """
        plan = self.executor.load_plan(plan_file_path)

        # Validate each step
        step_results = []
        all_valid = True

        for step in plan["steps"]:
            step_result = self.executor.validate_step_completion(
                plan_file_path, step["number"]
            )
            step_results.append(step_result)

            if not step_result["valid"]:
                all_valid = False

        # Validate overall success criteria
        overall_criteria = self._extract_overall_criteria(plan["content"])
        overall_result = self._validate_overall_criteria(overall_criteria)

        return {
            "all_valid": all_valid and overall_result["all_complete"],
            "step_results": step_results,
            "overall_criteria": overall_result,
            "ready_for_completion": all_valid and overall_result["all_complete"]
        }

    def _extract_overall_criteria(self, content: str) -> List[Dict[str, Any]]:
        """Extract overall success criteria from plan content.

        Args:
            content: Plan markdown content

        Returns:
            List of criteria dicts
        """
        criteria = []

        # Find the "Success Criteria" section
        match = re.search(
            r'## Success Criteria\s*\n.*?\n\n((?:- \[[ Xx]\] .+\n?)+)',
            content,
            re.DOTALL
        )

        if match:
            criteria_text = match.group(1)

            # Parse each criterion
            for line in criteria_text.split('\n'):
                criterion_match = re.match(r'- \[([ Xx])\] (.+)', line)
                if criterion_match:
                    checked = criterion_match.group(1).lower() == 'x'
                    text = criterion_match.group(2)

                    criteria.append({
                        "text": text,
                        "completed": checked,
                        "validation_type": self._detect_validation_type(text)
                    })

        return criteria

    def _detect_validation_type(self, criterion_text: str) -> str:
        """Detect validation type from criterion text.

        Args:
            criterion_text: Criterion text

        Returns:
            Validation type (automated, manual, test)
        """
        text_lower = criterion_text.lower()

        # Test-based validation
        if any(keyword in text_lower for keyword in ['test', 'passing', 'coverage']):
            return "test"

        # File-based validation
        if any(keyword in text_lower for keyword in ['file', 'exists', 'created']):
            return "file"

        # Manual validation
        if any(keyword in text_lower for keyword in ['review', 'approve', 'confirm', 'verify']):
            return "manual"

        # Default to automated
        return "automated"

    def _validate_overall_criteria(self, criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate overall success criteria.

        Args:
            criteria: List of criteria dicts

        Returns:
            Validation result
        """
        total = len(criteria)
        completed = sum(1 for c in criteria if c["completed"])
        remaining = [c["text"] for c in criteria if not c["completed"]]

        return {
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "all_complete": completed == total,
            "completion_percentage": round((completed / total) * 100, 1) if total > 0 else 0
        }

    def run_automated_validation(self, criterion: Dict[str, Any],
                                 working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run automated validation for a criterion.

        Args:
            criterion: Criterion dict
            working_dir: Optional working directory for commands

        Returns:
            Validation result
        """
        validation_type = criterion.get("validation_type", "automated")

        if validation_type == "test":
            return self._run_test_validation(criterion, working_dir)
        elif validation_type == "file":
            return self._run_file_validation(criterion, working_dir)
        elif validation_type == "manual":
            return {
                "valid": False,
                "reason": "Manual validation required",
                "requires_user_confirmation": True
            }
        else:
            return {
                "valid": criterion.get("completed", False),
                "reason": "Marked as complete in plan"
            }

    def _run_test_validation(self, criterion: Dict[str, Any],
                            working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run test-based validation.

        Args:
            criterion: Criterion dict
            working_dir: Working directory

        Returns:
            Validation result
        """
        # Extract test command from criterion text
        text = criterion["text"]

        # Look for common test patterns
        test_commands = {
            "npm test": r"npm test|tests? pass",
            "pytest": r"pytest|python.*test",
            "go test": r"go test",
            "cargo test": r"cargo test"
        }

        for cmd, pattern in test_commands.items():
            if re.search(pattern, text, re.IGNORECASE):
                try:
                    result = subprocess.run(
                        cmd.split(),
                        cwd=working_dir,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout
                    )

                    return {
                        "valid": result.returncode == 0,
                        "reason": "Tests passed" if result.returncode == 0 else "Tests failed",
                        "output": result.stdout[:500]  # Truncate output
                    }

                except subprocess.TimeoutExpired:
                    return {
                        "valid": False,
                        "reason": f"Test command timed out after {self.timeout}s"
                    }
                except Exception as e:
                    return {
                        "valid": False,
                        "reason": f"Test execution failed: {str(e)}"
                    }

        # No test command found
        return {
            "valid": False,
            "reason": "Could not determine test command",
            "requires_user_confirmation": True
        }

    def _run_file_validation(self, criterion: Dict[str, Any],
                            working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run file-based validation.

        Args:
            criterion: Criterion dict
            working_dir: Working directory

        Returns:
            Validation result
        """
        text = criterion["text"]

        # Extract file paths from criterion text
        # Look for patterns like "file.txt exists" or "created file.txt"
        file_pattern = r'[\w\-./]+\.\w+'
        matches = re.findall(file_pattern, text)

        if not matches:
            return {
                "valid": False,
                "reason": "Could not extract file path from criterion"
            }

        # Check if files exist
        base_dir = Path(working_dir) if working_dir else Path.cwd()
        missing_files = []

        for file_path in matches:
            full_path = base_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            return {
                "valid": False,
                "reason": f"Missing files: {', '.join(missing_files)}"
            }

        return {
            "valid": True,
            "reason": "All files exist"
        }

    def mark_all_criteria_complete(self, plan_file_path: str) -> bool:
        """Mark all success criteria as complete.

        Args:
            plan_file_path: Path to plan file

        Returns:
            True if successful
        """
        try:
            content = Path(plan_file_path).read_text(encoding='utf-8')

            # Replace all unchecked boxes with checked boxes
            updated_content = re.sub(r'- \[ \]', '- [X]', content)

            # Write back
            Path(plan_file_path).write_text(updated_content, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error marking criteria complete: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    validator = SuccessCriteriaValidator()

    # Example: Validate all criteria
    # result = validator.validate_all_criteria("path/to/plan.md")
    # print(f"All valid: {result['all_valid']}")
    # print(f"Ready for completion: {result['ready_for_completion']}")

    print("SuccessCriteriaValidator initialized.")

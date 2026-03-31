"""Action safety classifier for approval workflow.

Classifies actions by safety level:
- Level 0 (Auto-Execute): Read-only operations
- Level 1 (Notify): Low-risk writes (drafts)
- Level 2 (Confirm): Medium-risk (send emails, post to social media)
- Level 3 (Explicit Approval): High-risk (financial transactions, delete operations)
"""

from typing import Dict, Any


class ActionClassifier:
    """Classifier for action safety levels."""

    def __init__(self):
        """Initialize action classifier with safety rules."""
        # Action type to safety level mapping
        self.action_levels = {
            # Level 0: Auto-execute (read-only)
            "get-emails": 0,
            "list-notifications": 0,
            "get-messages": 0,

            # Level 1: Notify (drafts, low-risk)
            "create-draft": 1,
            "save-note": 1,

            # Level 2: Confirm (send, post, medium-risk)
            "send-email": 2,
            "linkedin-post": 2,
            "whatsapp-send": 2,

            # Level 3: Explicit approval (financial, delete, high-risk)
            "delete-email": 3,
            "transfer-money": 3,
            "delete-account": 3,
        }

    def classify(self, action_type: str, parameters: Dict[str, Any]) -> int:
        """Classify an action by safety level.

        Args:
            action_type: Type of action (e.g., send-email)
            parameters: Action parameters

        Returns:
            Safety level (0-3)
        """
        # Get base level from action type
        base_level = self.action_levels.get(action_type, 2)  # Default to Level 2

        # Apply parameter-based adjustments
        adjusted_level = self._adjust_for_parameters(action_type, parameters, base_level)

        return adjusted_level

    def _adjust_for_parameters(self, action_type: str, parameters: Dict[str, Any],
                               base_level: int) -> int:
        """Adjust safety level based on parameters.

        Args:
            action_type: Type of action
            parameters: Action parameters
            base_level: Base safety level

        Returns:
            Adjusted safety level
        """
        # Example adjustments (can be extended)

        # Email to external domains might be higher risk
        if action_type == "send-email":
            recipient = parameters.get("recipient", "")
            # If sending to unknown domain, keep Level 2
            # If sending to known safe domain, could reduce to Level 1
            # For now, keep base level
            pass

        # LinkedIn posts with certain keywords might need higher approval
        if action_type == "linkedin-post":
            content = parameters.get("content", "").lower()
            sensitive_keywords = ["confidential", "internal", "private", "secret"]
            if any(keyword in content for keyword in sensitive_keywords):
                return max(base_level, 3)  # Escalate to Level 3

        return base_level

    def requires_approval(self, safety_level: int) -> bool:
        """Check if action requires approval.

        Args:
            safety_level: Safety level (0-3)

        Returns:
            True if approval required (Level 2+)
        """
        return safety_level >= 2

    def get_level_description(self, safety_level: int) -> str:
        """Get human-readable description of safety level.

        Args:
            safety_level: Safety level (0-3)

        Returns:
            Description string
        """
        descriptions = {
            0: "Auto-Execute (read-only)",
            1: "Notify (low-risk writes)",
            2: "Confirm (medium-risk actions)",
            3: "Explicit Approval (high-risk actions)"
        }
        return descriptions.get(safety_level, "Unknown")

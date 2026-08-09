"""Research eligibility rules for pull requests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EligibilityStatus(StrEnum):
    """Possible research eligibility outcomes."""

    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"


class ExclusionReason(StrEnum):
    """Reasons a pull request may be excluded."""

    NOT_MERGED = "not_merged"
    NO_MERGE_COMMIT = "no_merge_commit"
    NO_CHANGED_FILES = "no_changed_files"
    NO_SOURCE_CODE_CHANGES = "no_source_code_changes"


@dataclass(frozen=True)
class PullRequestEligibility:
    """Research eligibility decision for a pull request."""

    status: EligibilityStatus
    reason: str | None = None

    @property
    def is_eligible(self) -> bool:
        """Return whether the pull request is eligible."""
        return self.status == EligibilityStatus.ELIGIBLE

    @classmethod
    def eligible(cls) -> PullRequestEligibility:
        """Create an eligible result."""
        return cls(
            status=EligibilityStatus.ELIGIBLE,
            reason=None,
        )

    @classmethod
    def excluded(
            cls,
            reason: ExclusionReason,
    ) -> PullRequestEligibility:
        """Create an excluded result."""
        return cls(
            status=EligibilityStatus.EXCLUDED,
            reason=reason.value,
        )
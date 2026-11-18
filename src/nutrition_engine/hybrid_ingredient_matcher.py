"""SR Legacy first ingredient resolution with the existing NLP matcher fallback.

This module orchestrates the two stages without changing
``ingredient_matcher.IngredientMatcher`` or its scoring and query behavior.
Search functions are injected so API calls can be mocked in tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Literal, Sequence

from .ingredient_matcher import (
    ACCEPT_THRESHOLD,
    Candidate,
    IngredientMatcher,
    MEANINGFUL_MODIFIERS,
    MatchResult,
    apply_synonyms,
    normalize,
    normalize_data_type,
    normalize_text,
    score_candidate,
    is_composite,
)
from .usda_search import _to_candidate

SearchStatus = Literal[
    "matched", "no_suitable_candidate", "api_error", "not_attempted"
]
Stage = Literal["sr_legacy", "nlp_fallback"]
AsyncSearchFn = Callable[[str], Awaitable[Sequence[Candidate]]]


@dataclass(frozen=True)
class HybridMatchResult:
    """A match or review decision with stage-by-stage trace information."""

    raw_name: str
    queries: tuple[str, ...]
    candidate: Candidate | None
    stage: Stage | None
    accepted: bool
    review_required: bool
    reason: str
    sr_legacy_status: SearchStatus
    nlp_status: SearchStatus
    sr_legacy_error: str | None = None
    nlp_error: str | None = None
    nlp_result: MatchResult | None = None
    nlp_query_errors: tuple[tuple[str, str], ...] = ()

    @property
    def fdc_id(self) -> int | None:
        return self.candidate.fdc_id if self.candidate else None

    @property
    def description(self) -> str | None:
        return self.candidate.description if self.candidate else None

    @property
    def data_type(self) -> str | None:
        return self.candidate.data_type if self.candidate else None


class SearchBackendError(RuntimeError):
    """Raised inside the unchanged synchronous matcher for failed live queries."""


def _preparation_state(text: str) -> str | None:
    tokens = set(normalize_text(text).split())
    if tokens & {"uncooked", "raw"}:
        return "raw"
    if tokens & {"cooked", "boiled"}:
        return "cooked"
    return None


def _preparation_compatible(raw_name: str, description: str) -> bool:
    requested = _preparation_state(raw_name)
    returned = _preparation_state(description)
    if requested is None:
        # Preserve the original matcher policy: an explicitly transformed
        # cooked/boiled record is unsuitable when no such preparation was asked.
        return returned != "cooked"
    # Generic USDA descriptions do not contradict an explicit request. Reject
    # only when both sides state incompatible preparation states.
    return returned is None or returned == requested


_MODIFIER_VARIANTS = {
    "low-fat": ("low fat", "lowfat"),
    "lowfat": ("lowfat", "low fat"),
    "fat-free": ("fat free", "nonfat", "non fat"),
    "nonfat": ("nonfat", "non fat", "fat free"),
    "extra-firm": ("extra firm",),
    "low-sodium": ("low sodium", "reduced sodium"),
    "dry-roasted": ("dry roasted",),
}


def _modifier_compatible(raw_name: str, description: str) -> bool:
    """Require SR Legacy text to support requested meaningful modifiers."""
    ingredient_head = normalize_text(raw_name.split(",", 1)[0]).replace("-", " ")
    candidate = normalize_text(apply_synonyms(description)).replace("-", " ")
    padded_candidate = f" {candidate} "

    for modifier in MEANINGFUL_MODIFIERS:
        if modifier == "raw":  # handled by the preparation compatibility rule
            continue
        normalized_modifier = modifier.replace("-", " ")
        if f" {normalized_modifier} " not in f" {ingredient_head} ":
            continue
        variants = _MODIFIER_VARIANTS.get(modifier, (normalized_modifier,))
        if not any(f" {variant} " in padded_candidate for variant in variants):
            return False
    return True


class HybridIngredientMatcher:
    """Try filtered SR Legacy results, then the original NLP matcher.

    ``sr_legacy_search`` must use USDA's data type filter. ``nlp_search``
    retrieves candidates using the same unfiltered backend used by the
    existing matcher. Both may raise; failures remain distinct from empty
    successful responses in the returned result.
    """

    def __init__(
        self,
        sr_legacy_search: AsyncSearchFn,
        nlp_search: AsyncSearchFn,
        *,
        accept_threshold: float = ACCEPT_THRESHOLD,
    ) -> None:
        self.sr_legacy_search = sr_legacy_search
        self.nlp_search = nlp_search
        self.accept_threshold = accept_threshold

    @classmethod
    def from_usda_client(cls, client, *, page_size: int = 50) -> "HybridIngredientMatcher":
        """Build live search functions around an already-open ``USDAClient``."""

        async def sr_legacy_search(query: str) -> Sequence[Candidate]:
            foods = await client.search_foods(
                query, page_size=page_size, data_types=["SR Legacy"]
            )
            return [_to_candidate(food) for food in foods]

        async def nlp_search(query: str) -> Sequence[Candidate]:
            foods = await client.search_foods(query, page_size=page_size)
            return [_to_candidate(food) for food in foods]

        return cls(sr_legacy_search, nlp_search)

    async def match(self, raw_name: str) -> HybridMatchResult:
        queries = tuple(normalize(raw_name))
        if is_composite(raw_name):
            return HybridMatchResult(
                raw_name, queries, None, None, False, True, "composite_requires_review",
                "not_attempted", "not_attempted",
            )

        sr_error: str | None = None
        for query in queries:
            try:
                candidates = await self.sr_legacy_search(query)
            except Exception as exc:
                sr_error = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
                break

            suitable = [
                candidate for candidate in candidates
                if normalize_data_type(candidate.data_type) == "sr legacy"
                and score_candidate(query, candidate) >= self.accept_threshold
                and _preparation_compatible(raw_name, candidate.description)
                and _modifier_compatible(raw_name, candidate.description)
            ]
            if suitable:
                candidate = max(suitable, key=lambda item: score_candidate(query, item))
                return HybridMatchResult(
                    raw_name, queries, candidate, "sr_legacy", True, False,
                    "accepted_sr_legacy", "matched", "not_attempted",
                )

        sr_status: SearchStatus = "api_error" if sr_error else "no_suitable_candidate"

        # Fetch by the original matcher's normalized query list, then delegate
        # all selection, ranking, and acceptance decisions to that matcher.
        fetched: dict[str, Sequence[Candidate]] = {}
        fetch_errors: dict[str, str] = {}
        for query in queries:
            try:
                fetched[query] = await self.nlp_search(query)
            except Exception as exc:
                fetch_errors[query] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"

        def search(query: str) -> Sequence[Candidate]:
            if query in fetch_errors:
                raise SearchBackendError(fetch_errors[query])
            return fetched.get(query, ())

        matcher = IngredientMatcher(search, accept_threshold=self.accept_threshold)
        try:
            nlp_result = matcher.match(raw_name)
        except SearchBackendError as exc:
            return HybridMatchResult(
                raw_name, queries, None, None, False, True,
                "nlp_api_error", sr_status, "api_error", sr_error, str(exc),
                nlp_query_errors=tuple(fetch_errors.items()),
            )

        if nlp_result.matched:
            selected = next(
                (candidate for values in fetched.values() for candidate in values
                 if candidate.fdc_id == nlp_result.fdc_id
                 and candidate.description == nlp_result.description),
                Candidate(nlp_result.fdc_id, nlp_result.description or "", None),
            )
            return HybridMatchResult(
                raw_name, queries, selected, "nlp_fallback", True, False,
                "accepted_nlp_fallback", sr_status, "matched", sr_error,
                nlp_result=nlp_result, nlp_query_errors=tuple(fetch_errors.items()),
            )

        return HybridMatchResult(
            raw_name, queries, None, None, False, True,
            "nlp_no_suitable_candidate", sr_status, "no_suitable_candidate",
            sr_error, nlp_result=nlp_result,
            nlp_query_errors=tuple(fetch_errors.items()),
        )


__all__ = ["HybridIngredientMatcher", "HybridMatchResult", "SearchBackendError"]

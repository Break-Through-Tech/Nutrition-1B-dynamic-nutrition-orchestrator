"""Keyword/NLP ingredient matching (Task 6).

Resolves a raw recipe ingredient string from `data/ingredients.csv` to a USDA
FoodData Central record, so the deterministic macro engine has a verified
nutrient source instead of a hand-written catalog entry.

Three stages, each independently testable:

  1. `normalize()`   raw string -> one or more clean search queries.
                     "low-fat paneer, crumbled" -> "paneer"
  2. `search_fn()`   query -> candidate USDA records. Injected, not hardcoded,
                     so tests run offline and Task 1's client stays the only
                     place that talks to the network.
  3. `score_candidate()`  query + candidate -> 0.0-1.0 confidence.

Deliberately dependency-free (stdlib `difflib`), matching the approach already
taken in `benchmarks.py` for F1 — the September baseline should not pull in an
ML stack to do string comparison.

Composite entries ("kadhai spice mix", "quinoa-rice blend") cannot map to a
single FDC ID and are reported as `unmatched` with reason "composite" rather
than being forced onto a wrong record. That is a correct answer, not a failure.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Indian/Hindi ingredient names mapped to the English terms USDA actually
# indexes. This table is the single biggest lever on F1 — USDA has no entry
# for "hing", but it does have "asafoetida".
SYNONYMS: dict[str, str] = {
    "hing": "asafoetida",
    "atta": "whole wheat flour",
    "maida": "white wheat flour",
    "besan": "chickpea flour",
    "sooji": "semolina",
    "rava": "semolina",
    "dahi": "yogurt",
    "curd": "yogurt",
    "paneer": "paneer cheese",
    "ghee": "butter oil clarified",
    "jeera": "cumin",
    "haldi": "turmeric",
    "dhania": "coriander",
    "methi": "fenugreek",
    "kasuri methi": "fenugreek leaves dried",
    "ajwain": "carom seeds",
    "carom seeds": "carom seeds",
    "kala namak": "black salt",
    "degi mirch": "paprika",
    "kashmiri red chili powder": "paprika",
    "moong dal": "mung beans",
    "raw sprouted moong": "mung beans sprouted",
    "split moong dal": "mung beans split",
    "urad dal": "black gram",
    "whole black urad dal": "black gram",
    "split urad dal": "black gram split",
    "chana dal": "chickpeas split",
    "split chana dal": "chickpeas split",
    "kala chana": "chickpeas black",
    "kabuli chana": "chickpeas",
    "dry-roasted chana": "chickpeas roasted",
    "toor dal": "pigeon peas",
    "arhar dal": "pigeon peas",
    "rajma": "kidney beans",
    "soya chunks": "textured vegetable protein soy",
    "soya granules": "textured vegetable protein soy",
    "soya nuts": "soy nuts roasted",
    "poha": "rice flattened",
    "capsicum": "bell pepper",
    "curry leaves": "curry leaves",
    "green chili": "peppers hot chili green",
    "green chilies": "peppers hot chili green",
    "red chili powder": "chili powder",
    "cilantro": "coriander leaves",
    "low-sodium": "reduced sodium",
    "low sodium": "reduced sodium",
}

# Preparation state, not identity. Stripped before searching: USDA indexes
# "Tofu, firm", not "tofu, cubed and seared".
PREP_TERMS: frozenset[str] = frozenset({
    "soaked", "overnight", "boiled", "squeezed", "hard", "triple", "crumbled",
    "grated", "cubed", "diced", "chopped", "minced", "finely", "mashed",
    "steamed", "sliced", "shredded", "julienned", "seared", "processed",
    "ground", "into", "thick", "freshly", "prepared", "washed", "drained",
    "for", "rotis", "roti", "needed", "taste", "to", "as", "pods",
})

# Terms that make an entry a recipe sub-component rather than one purchasable
# food. These get reported as unmatched-composite instead of force-matched.
COMPOSITE_MARKERS: tuple[str, ...] = (
    "/", " and ", " blend", " mix", "gravy base", "chutney", "spice mix",
)

# States that transform a food rather than identify it. A recipe naming
# "quinoa" means the grain, not "Quinoa, cooked"; "almonds" means plain nuts,
# not "Almonds, flavored". Penalised when the description carries one the
# query never asked for -- the macro difference is large (mung beans are
# 23.9g protein raw against 6.5g cooked).
TRANSFORMED_STATES: frozenset[str] = frozenset({
    "cooked", "boiled", "fried", "flavored", "sweetened", "salted", "canned",
    "sauce", "juice", "frozen", "creamed", "breaded", "stewed", "baked",
    "smoked", "pickled", "candied", "seasoned", "marinated", "glazed",
})

DERIVATIVE_FORMS: frozenset[str] = frozenset({
    "flour", "meal", "extract", "concentrate", "starch",
})

# Modifiers worth keeping in the query — USDA descriptions carry them and they
# change the macros materially (low-fat paneer vs paneer).
MEANINGFUL_MODIFIERS: frozenset[str] = frozenset({
    "low-fat", "lowfat", "fat-free", "nonfat", "full-fat", "whole", "skim",
    "extra-firm", "firm", "soft", "silken", "low-sodium", "unflavored",
    "dry", "raw", "roasted", "dry-roasted", "fresh", "sweet", "mild",
})


# ---------------------------------------------------------------------------
# Data carriers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    """One USDA record returned by a search backend.

    `data_type` is optional because Task 1's `USDAFood` does not currently
    expose it. When present it improves ranking (Foundation/SR Legacy records
    are curated whole foods; Branded records are commercial products with
    noisier descriptions).
    """

    fdc_id: int
    description: str
    data_type: str | None = None


@dataclass(frozen=True)
class MatchResult:
    raw_name: str
    queries: tuple[str, ...]
    fdc_id: int | None
    description: str | None
    score: float
    confidence: str          # "high" | "medium" | "low" | "none"
    reason: str | None = None   # populated when fdc_id is None
    considered: tuple[tuple[int, str, float], ...] = field(default=())

    @property
    def matched(self) -> bool:
        return self.fdc_id is not None

    def to_dict(self) -> dict:
        return {
            "raw_name": self.raw_name,
            "queries": list(self.queries),
            "fdc_id": self.fdc_id,
            "description": self.description,
            "score": self.score,
            "confidence": self.confidence,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Stage 1 — normalization
# ---------------------------------------------------------------------------

def normalize_text(value: str) -> str:
    """Lowercase and strip punctuation, preserving internal hyphens."""
    lowered = value.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\-/ ]+", " ", lowered)
    return " ".join(cleaned.split())


def is_composite(raw_name: str) -> bool:
    """True when the entry names a prepared mixture, not a single food.

    Only the head (before the first comma) is examined. Preparation tails
    routinely contain "and" -- "kala chana, soaked overnight and boiled" is a
    single ingredient, not a mixture.
    """
    head = raw_name.split(",")[0]
    padded = f" {normalize_text(head)} "
    return any(marker in padded for marker in COMPOSITE_MARKERS)


def strip_prep_terms(text: str) -> str:
    kept = [token for token in text.split() if token not in PREP_TERMS]
    return " ".join(kept)


def apply_synonyms(text: str) -> str:
    """Replace Indian ingredient names with USDA-indexed English terms.

    Longest keys first so "split moong dal" wins over "moong dal".
    """
    result = text
    for term in sorted(SYNONYMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(term)}\b", result):
            result = re.sub(rf"\b{re.escape(term)}\b", SYNONYMS[term], result)
    return " ".join(result.split())


def normalize(raw_name: str) -> list[str]:
    """Turn one raw recipe string into ordered search queries, best first.

    "kala namak (black salt)" -> ["black salt", "kala namak"]
    "low-fat paneer, crumbled" -> ["low-fat paneer cheese", "paneer cheese"]
    """
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise ValueError("Ingredient name must be a non-empty string.")

    lowered = raw_name.lower().strip()

    # A parenthetical is usually the more searchable synonym of the head term,
    # e.g. "whole wheat flour (atta)" or "kala namak (black salt)".
    parenthetical = None
    match = re.search(r"\(([^)]+)\)", lowered)
    if match:
        parenthetical = normalize_text(match.group(1))
        lowered = lowered[: match.start()] + " " + lowered[match.end():]

    # Everything after the first comma is preparation state, not identity.
    head = normalize_text(lowered.split(",")[0])
    head = strip_prep_terms(head)

    queries: list[str] = []

    def add(candidate: str) -> None:
        cleaned = " ".join(candidate.split())
        if cleaned and cleaned not in queries:
            queries.append(cleaned)

    # The parenthetical, when present, is tried first — it is usually the term
    # USDA indexes under.
    if parenthetical:
        add(apply_synonyms(strip_prep_terms(parenthetical)))

    add(apply_synonyms(head))

    # A bare form with modifiers dropped, as a fallback when the modified
    # phrase returns nothing (e.g. "low-fat paneer" -> "paneer").
    bare = " ".join(t for t in head.split() if t not in MEANINGFUL_MODIFIERS)
    add(apply_synonyms(bare))

    add(head)

    return queries


# ---------------------------------------------------------------------------
# Stage 3 — scoring
# ---------------------------------------------------------------------------

# USDA spells these differently in the API ("Foundation", "SR Legacy") and in
# the bulk CSV download ("foundation_food"). Compare on a normalized form so
# both work.
CURATED_TYPES = {"foundation", "sr legacy", "survey fndds", "survey"}
BRANDED_TYPES = {"branded"}


def normalize_data_type(data_type: str | None) -> str | None:
    if not data_type:
        return None
    cleaned = data_type.lower().replace("_", " ").replace("(", " ").replace(")", " ")
    cleaned = " ".join(cleaned.split())
    for suffix in (" food",):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return cleaned.strip()


def score_candidate(query: str, candidate: Candidate) -> float:
    """Score a USDA record against a query on a 0.0-1.0 scale.

    Token recall dominates because USDA descriptions are comma-separated
    attribute lists ("Tofu, raw, firm, prepared with calcium sulfate") where
    word order carries little meaning.
    """
    query_tokens = set(normalize_text(query).split())
    desc_tokens = set(normalize_text(candidate.description).split())
    if not query_tokens or not desc_tokens:
        return 0.0

    # How much of what we asked for actually appears in the record.
    recall = len(query_tokens & desc_tokens) / len(query_tokens)

    # Character-level similarity catches near-misses recall alone would zero
    # out ("chickpea" vs "chickpeas").
    ratio = SequenceMatcher(
        None,
        " ".join(sorted(query_tokens)),
        " ".join(sorted(desc_tokens)),
    ).ratio()

    score = 0.70 * recall + 0.30 * ratio

    # Long descriptions are usually branded products loaded with marketing
    # words; a concise record is more likely to be the generic ingredient.
    surplus = max(0, len(desc_tokens) - len(query_tokens))
    score -= min(0.12, 0.012 * surplus)

    # USDA lists prepared dishes alongside plain ingredients: "Kidney beans
    # with meat", "Beans and brown rice", "Almond chicken". A conjunction is
    # a reliable marker that the record is a dish containing the ingredient
    # rather than the ingredient itself.
    # Only the head segment counts. "Kidney beans with meat" is a dish, but
    # "Tofu, raw, firm, prepared with calcium sulfate" is plain tofu described
    # with its setting agent -- the conjunction there is in a trailing
    # qualifier, not in the food's name.
    desc_head = f" {normalize_text(candidate.description.split(',')[0])} "
    if any(joiner in desc_head for joiner in (" and ", " with ")):
        score -= 0.20

    # A transformation the query never requested changes the food's macros
    # materially, so it is penalised unless the recipe asked for that state.
    unrequested = (desc_tokens & TRANSFORMED_STATES) - query_tokens
    if unrequested:
        score -= 0.25

    # A derivative product is not the ingredient: "Flour, rice, brown" is
    # milled rice, with different macros and a different role in a recipe.
    if (desc_tokens & DERIVATIVE_FORMS) - query_tokens:
        score -= 0.25

    # Record-quality preference. Deliberately modest: a hard tier made a
    # poor curated match outrank a perfect branded one (a black-bean
    # record beat 'BLACK SALT' for kala namak).
    kind = normalize_data_type(candidate.data_type)
    if kind in CURATED_TYPES:
        score += 0.10

        # Curated descriptions lead with the food and qualify afterwards:
        # "Quinoa, uncooked" is the grain, "Flour, quinoa" is a product made
        # from it. Applied only to curated records -- a terse branded name
        # ("QUINOA") is entirely head, so rewarding head position generally
        # would promote exactly the records this is meant to demote.
        head_segment = normalize_text(candidate.description.split(",")[0])
        if head_segment and query_tokens & set(head_segment.split()):
            score += 0.10
    elif kind in BRANDED_TYPES:
        score -= 0.06

    return max(0.0, min(1.0, round(score, 4)))


def candidate_tier(candidate: Candidate) -> int:
    """Rank tier for a candidate: lower sorts first.

    A short branded name scores a perfect token match ("QUINOA" against the
    query "quinoa") while the better curated record ("Quinoa, uncooked") loses
    points for its extra words. Scoring alone therefore prefers the worse
    record, so record quality is applied as a tier ahead of the score rather
    than as a bonus inside it.

    Recipe ingredients are generic foods, not commercial products, and USDA
    Branded entries carry label values that are often rounded or incomplete.
    A branded record is still used when nothing curated matches at all.
    """
    kind = normalize_data_type(candidate.data_type)
    if kind in CURATED_TYPES:
        return 0
    if kind is None:
        return 1  # unknown provenance sorts between curated and branded
    return 2


def confidence_band(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    if score > 0.0:
        return "low"
    return "none"


# ---------------------------------------------------------------------------
# Stage 2 + orchestration
# ---------------------------------------------------------------------------

SearchFn = Callable[[str], Sequence[Candidate]]

# Chosen by sweeping 0.30-0.90 against the validation set: F1 rises from
# 81.8% at 0.55 to 90.5% at 0.80, then falls as real matches start being
# rejected. See `python scripts/evaluate_matcher.py --sweep`.
ACCEPT_THRESHOLD = 0.80


class IngredientMatcher:
    """Resolve recipe ingredient strings to USDA FDC IDs.

    The search backend is injected so this class has no network dependency:
    pass `usda_search_fn(client)` in production, a dict-backed fake in tests.
    """

    def __init__(
        self,
        search_fn: SearchFn,
        accept_threshold: float = ACCEPT_THRESHOLD,
        allow_composite: bool = False,
    ) -> None:
        self.search_fn = search_fn
        self.accept_threshold = accept_threshold
        self.allow_composite = allow_composite
        # Recipe ingredient lists repeat heavily ("low-fat paneer" appears in
        # four recipes); cache keeps the API call count near the unique count.
        self._cache: dict[str, MatchResult] = {}

    def match(self, raw_name: str) -> MatchResult:
        cache_key = normalize_text(raw_name)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._match_uncached(raw_name)
        self._cache[cache_key] = result
        return result

    def match_all(self, raw_names: Iterable[str]) -> list[MatchResult]:
        return [self.match(name) for name in raw_names]

    def _match_uncached(self, raw_name: str) -> MatchResult:
        if not self.allow_composite and is_composite(raw_name):
            return MatchResult(
                raw_name=raw_name,
                queries=(),
                fdc_id=None,
                description=None,
                score=0.0,
                confidence="none",
                reason="composite",
            )

        queries = normalize(raw_name)
        # The same record surfaces under several queries at different scores:
        # "extra-firm tofu" matches "Tofu, raw, firm" weakly while the fallback
        # query "tofu" matches it well. Keep each record's best score, not its
        # first.
        best_by_id: dict[int, tuple[float, Candidate, str]] = {}

        for query in queries:
            for candidate in self.search_fn(query):
                score = score_candidate(query, candidate)
                previous = best_by_id.get(candidate.fdc_id)
                if previous is None or score > previous[0]:
                    best_by_id[candidate.fdc_id] = (score, candidate, query)
            # Stop early once a query produces a confident hit; later queries
            # are progressively looser fallbacks.
            if best_by_id and max(item[0] for item in best_by_id.values()) >= 0.75:
                break

        scored = list(best_by_id.values())

        if not scored:
            return MatchResult(
                raw_name=raw_name,
                queries=tuple(queries),
                fdc_id=None,
                description=None,
                score=0.0,
                confidence="none",
                reason="no_candidates",
            )

        scored.sort(key=lambda item: -item[0])
        best_score, best, _ = scored[0]
        considered = tuple(
            (c.fdc_id, c.description, s) for s, c, _ in scored[:5]
        )

        if best_score < self.accept_threshold:
            return MatchResult(
                raw_name=raw_name,
                queries=tuple(queries),
                fdc_id=None,
                description=None,
                score=best_score,
                confidence=confidence_band(best_score),
                reason="below_threshold",
                considered=considered,
            )

        return MatchResult(
            raw_name=raw_name,
            queries=tuple(queries),
            fdc_id=best.fdc_id,
            description=best.description,
            score=best_score,
            confidence=confidence_band(best_score),
            considered=considered,
        )


__all__ = [
    "ACCEPT_THRESHOLD",
    "Candidate",
    "IngredientMatcher",
    "MatchResult",
    "SYNONYMS",
    "apply_synonyms",
    "candidate_tier",
    "confidence_band",
    "is_composite",
    "normalize",
    "normalize_data_type",
    "normalize_text",
    "score_candidate",
    "strip_prep_terms",
]

""" Module recommendation and suggestion engine for students.

    Provides smart module proposals based on:
    1. The student's study course (usability ids) and current semester.
    2. Curated topic clusters (AI, Graphics/Games, Systems, Scientific Computing).
    3. Exclusion of already saved/planned modules to avoid redundancy.
    4. Explanations for why each module was recommended.
"""

from dataclasses import dataclass
import re
from typing import NamedTuple, Sequence
from loguru import logger

from util.database import get_database
from util.enums import LanguageCode, StudyCourse
from util.filter_categorys import MODULE_FILTER_CATEGORIES
from util.module import Module, get_module_list
from util.translations import STUDY_COURSES


CATEGORY_NAMES: dict[str, dict[LanguageCode, str]] = {
    "ALL": {
        LanguageCode.DE: "🎯 Passend zu meinem Studiengang",
        LanguageCode.EN: "🎯 Fitting my study programme",
    },
    "AI": {
        LanguageCode.DE: "🤖 Künstliche Intelligenz (KI)",
        LanguageCode.EN: "🤖 Artificial Intelligence (AI)",
    },
    "ComputerGame": {
        LanguageCode.DE: "🎮 Computergrafik & Digitale Spiele",
        LanguageCode.EN: "🎮 Computer Graphics & Games",
    },
    "SystemsEngineering": {
        LanguageCode.DE: "💻 Software & Systems Engineering",
        LanguageCode.EN: "💻 Software & Systems Engineering",
    },
    "ScientificComputing": {
        LanguageCode.DE: "🔬 Wissenschaftliches Rechnen",
        LanguageCode.EN: "🔬 Scientific Computing",
    },
}


@dataclass(frozen=True)
class ModuleSuggestion:
    """Represents a recommended module with an explanation."""
    module: Module
    score: int
    reason_de: str
    reason_en: str


class UserContext(NamedTuple):
    """Encapsulates user study profile and saved modules."""
    saved_ids: set[int]
    major: StudyCourse | None
    semester: int | None


def _score_category_keywords(module: Module, category_key: str) -> int:
    """Calculates keyword match score for a specific category using word boundaries."""
    keywords = MODULE_FILTER_CATEGORIES.get(category_key, [])
    if not keywords:
        return 0

    score = 0
    text_corpus_de = (
        f"{module.get_title(LanguageCode.DE)} "
        f"{module.get_learning_goals(LanguageCode.DE)} "
        f"{module.get_content(LanguageCode.DE)}"
    ).lower()
    text_corpus_en = (
        f"{module.get_title(LanguageCode.EN)} "
        f"{module.get_learning_goals(LanguageCode.EN)} "
        f"{module.get_content(LanguageCode.EN)}"
    ).lower()

    title_de = module.get_title(LanguageCode.DE).lower()
    title_en = module.get_title(LanguageCode.EN).lower()

    for kw in keywords:
        kw_clean = kw.lower().strip()
        if not kw_clean:
            continue
        pattern = re.compile(rf"\b{re.escape(kw_clean)}\b")
        if pattern.search(text_corpus_de):
            score += 3
        if pattern.search(text_corpus_en):
            score += 3
        if pattern.search(title_de):
            score += 10
        if pattern.search(title_en):
            score += 10
    return score


def _get_user_context(user_id: int | None) -> UserContext:
    """Fetches user preferences and saved module IDs safely."""
    saved_ids: set[int] = set()
    major: StudyCourse | None = None
    semester: int | None = None

    if user_id is None:
        return UserContext(saved_ids=saved_ids, major=major, semester=semester)

    db = get_database()
    try:
        plan = db.get_semesterplan(user_id)
        saved_ids = {m.id_ for m in plan}
    except (KeyError, ValueError) as exc:
        logger.debug(f"Could not read the semester plan of a user: {exc}")

    try:
        prefs = db.get_preferences(user_id)
        if prefs:
            major = prefs.get("major")
            semester = prefs.get("semester")
    except (KeyError, ValueError) as exc:
        logger.debug(f"Could not read the preferences of a user: {exc}")

    return UserContext(saved_ids=saved_ids, major=major, semester=semester)


def _score_single_module(
    module: Module,
    cat: str,
    ctx: UserContext,
) -> ModuleSuggestion | None:
    """Computes relevance score and reasons for a single candidate module."""
    score = 0
    reasons_de: list[str] = []
    reasons_en: list[str] = []

    if ctx.major is not None:
        usability = module.get_usability_ids(ctx.major)
        if usability:
            score += 20
            major_de = STUDY_COURSES.get(ctx.major, {}).get(LanguageCode.DE, ctx.major.name)
            major_en = STUDY_COURSES.get(ctx.major, {}).get(LanguageCode.EN, ctx.major.name)
            reasons_de.append(f"Wählbar in {major_de}")
            reasons_en.append(f"Eligible in {major_en}")
        else:
            score -= 10

    # `getattr` only falls back when the attribute is missing, and this one exists
    # and held `None` for the 15 rows the Tables API sends without a `Fachsemester`.
    # `util.module.without_nulls` keeps those out now, but a caller may hand in its
    # own modules, and a crash here takes the whole command down.
    raw_sem = getattr(module, "_academic_semester", -1) or -1
    if ctx.semester is not None and raw_sem > 0:
        if raw_sem == ctx.semester:
            score += 15
            reasons_de.append(f"Empfohlen für Semester {ctx.semester}")
            reasons_en.append(f"Recommended for semester {ctx.semester}")
        elif abs(raw_sem - ctx.semester) <= 1:
            score += 5

    if cat in MODULE_FILTER_CATEGORIES:
        cat_score = _score_category_keywords(module, cat)
        score += cat_score
        cat_de = CATEGORY_NAMES.get(cat, {}).get(LanguageCode.DE, cat)
        cat_en = CATEGORY_NAMES.get(cat, {}).get(LanguageCode.EN, cat)
        if cat_score > 0:
            reasons_de.append(f"Schwerpunkt: {cat_de}")
            reasons_en.append(f"Focus area: {cat_en}")
        elif cat != "ALL":
            return None
    elif "5" in module.credit_points:
        score += 5

    if score <= 0 and cat != "ALL":
        return None

    reason_de = " • ".join(reasons_de) if reasons_de else "Passendes Modulangebot"
    reason_en = " • ".join(reasons_en) if reasons_en else "Recommended module offering"
    return ModuleSuggestion(module=module, score=score, reason_de=reason_de, reason_en=reason_en)


def get_module_suggestions(
    user_id: int | None = None,
    category_key: str | None = None,
    limit: int = 5,
    all_modules: Sequence[Module] | None = None,
) -> list[ModuleSuggestion]:
    """Computes ranked module recommendations.

    Parameters:
        user_id: Discord user ID to read preferences and exclude saved modules.
        category_key: Optional filter category key ('AI', 'ComputerGame', etc.).
        limit: Maximum number of suggestions to return.
        all_modules: Pre-loaded modules list (defaults to fetching full catalogue).

    Returns:
        List of ModuleSuggestion instances sorted by score.
    """
    if all_modules is None:
        try:
            candidates: list[Module] = get_module_list()
        except (KeyError, ValueError) as exc:
            logger.warning(f"Could not load module catalogue: {exc}")
            return []
    else:
        candidates = list(all_modules)

    if not candidates:
        return []

    ctx = _get_user_context(user_id)
    available = [m for m in candidates if m.id_ not in ctx.saved_ids]
    if not available:
        available = candidates

    cat = (category_key or "ALL").strip()
    suggestions: list[ModuleSuggestion] = []

    for module in available:
        sug = _score_single_module(module, cat, ctx)
        if sug is not None:
            suggestions.append(sug)

    suggestions.sort(key=lambda s: s.score, reverse=True)
    return suggestions[:limit]

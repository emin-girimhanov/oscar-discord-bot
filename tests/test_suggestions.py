""" Unit tests for the module recommendation and suggestion system (Issue #42).

    Verifies keyword scoring, student major usability boosting, semester matching,
    exclusion of already planned modules, and interactive SuggestView construction.
"""

import unittest
from unittest.mock import MagicMock, patch

from oscar.ui.suggest_view import SuggestView
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module
from util.suggestions import (
    CATEGORY_NAMES,
    ModuleSuggestion,
    UserContext,
    _get_user_context,
    _score_category_keywords,
    _score_single_module,
    get_module_suggestions,
)


def _make_dummy_module(
    id_: int = 1001,
    title_de: str = "Einführung in die KI",
    title_en: str = "Introduction to AI",
    content: str = "Grundlagen maschinelles lernen und künstliche intelligenz.",
    credit_points: str = "5",
    academic_semester: int = 4,
    usability_bsc_inf: list[int] | None = None,
) -> Module:
    """Helper to create a populated Module object for testing."""
    return Module(
        id_=id_,
        language=ModuleLanguage.DE,
        title=title_de,
        title_en=title_en,
        content=content,
        credit_points=credit_points,
        academic_semester=academic_semester,
        teaching_form_sws="2V + 2Ü",
        lecturer="Prof. Dr. Max Mustermann",
        usability_bsc_inf=usability_bsc_inf or [1, 2],
    )


class TestSuggestions(unittest.TestCase):
    """Test suite for module recommendation algorithms."""

    def test_score_category_keywords_ai(self):
        """Tests scoring based on AI keywords."""
        mod = _make_dummy_module(
            title_de="Künstliche Intelligenz und Deep Learning",
            title_en="Artificial Intelligence and Deep Learning",
            content="Neuronale Netze und Maschinelles Lernen",
        )
        score = _score_category_keywords(mod, "AI")
        self.assertGreater(score, 20)

    def test_score_category_keywords_invalid_category(self):
        """Invalid category should return 0 score."""
        mod = _make_dummy_module()
        score = _score_category_keywords(mod, "UNKNOWN_CATEGORY")
        self.assertEqual(score, 0)

    def test_get_user_context_none(self):
        """User context with user_id=None should return empty profile."""
        ctx = _get_user_context(None)
        self.assertEqual(ctx.saved_ids, set())
        self.assertIsNone(ctx.major)
        self.assertIsNone(ctx.semester)

    @patch("util.suggestions.get_database")
    def test_get_user_context_with_data(self, mock_get_db):
        """User context should read plan and preferences from database."""
        mock_db = MagicMock()
        mock_db.get_semesterplan.return_value = [_make_dummy_module(id_=1001)]
        mock_db.get_preferences.return_value = {
            "major": StudyCourse.BSC_INF,
            "semester": 4,
        }
        mock_get_db.return_value = mock_db

        ctx = _get_user_context(12345)
        self.assertIn(1001, ctx.saved_ids)
        self.assertEqual(ctx.major, StudyCourse.BSC_INF)
        self.assertEqual(ctx.semester, 4)

    def test_score_single_module_matching_major_and_semester(self):
        """Module matching major usability and semester should receive boosts."""
        mod = _make_dummy_module(
            academic_semester=3,
            usability_bsc_inf=[1],
        )
        ctx = UserContext(
            saved_ids=set(),
            major=StudyCourse.BSC_INF,
            semester=3,
        )
        sug = _score_single_module(mod, "ALL", ctx)
        self.assertIsNotNone(sug)
        self.assertGreater(sug.score, 30)
        self.assertIn("Semester 3", sug.reason_de)
        self.assertIn("Wählbar in", sug.reason_de)

    def test_score_single_module_filtering_non_matching_category(self):
        """Module lacking keywords for a specific category should be excluded."""
        mod = _make_dummy_module(
            title_de="Lineare Algebra für Mathematiker",
            title_en="Linear Algebra",
            content="Matrizen, Vektorräume und Gleichungssysteme.",
        )
        ctx = UserContext(saved_ids=set(), major=None, semester=None)
        sug = _score_single_module(mod, "ComputerGame", ctx)
        self.assertIsNone(sug)

    def test_get_module_suggestions_excludes_saved(self):
        """Modules already present in the user's semester plan must be excluded."""
        mod1 = _make_dummy_module(id_=101, title_de="Modul 1")
        mod2 = _make_dummy_module(id_=102, title_de="Modul 2")

        with patch("util.suggestions.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_semesterplan.return_value = [mod1]
            mock_db.get_preferences.return_value = None
            mock_get_db.return_value = mock_db

            results = get_module_suggestions(
                user_id=999,
                category_key="ALL",
                limit=5,
                all_modules=[mod1, mod2],
            )
            result_ids = [s.module.id_ for s in results]
            self.assertNotIn(101, result_ids)
            self.assertIn(102, result_ids)

    def test_get_module_suggestions_ranking_order(self):
        """Modules with higher relevance score must appear first."""
        mod_ai = _make_dummy_module(
            id_=201,
            title_de="Künstliche Intelligenz und Maschinelles Lernen",
            title_en="Artificial Intelligence and Machine Learning",
            content="Deep Learning, KI, Neural Networks",
        )
        mod_basic = _make_dummy_module(
            id_=202,
            title_de="Grundlagen der Betriebswirtschaftslehre",
            title_en="Basics of Business Administration",
            content="Einführung BWL",
        )

        with patch("util.suggestions.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_semesterplan.return_value = []
            mock_db.get_preferences.return_value = None
            mock_get_db.return_value = mock_db

            results = get_module_suggestions(
                user_id=999,
                category_key="AI",
                limit=2,
                all_modules=[mod_basic, mod_ai],
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].module.id_, 201)

    def test_suggest_view_construction(self):
        """Tests building SuggestView components."""
        view = SuggestView(
            user_id=123,
            initial_category="AI",
            default_language=LanguageCode.DE,
        )
        self.assertEqual(view.category_key, "AI")
        self.assertEqual(view.language_code, LanguageCode.DE)
        self.assertGreater(len(view.children), 0)

    def test_suggest_view_render_card(self):
        """Tests rendering suggestion card formatting."""
        mod = _make_dummy_module()
        sug = ModuleSuggestion(
            module=mod,
            score=50,
            reason_de="Perfekt für KI-Interessierte",
            reason_en="Perfect for AI interests",
        )
        view = SuggestView(user_id=123)
        display = view._render_suggestion_card(sug, 1)
        self.assertIn("Einführung in die KI", display.content)
        self.assertIn("Perfekt für KI-Interessierte", display.content)


if __name__ == "__main__":
    unittest.main()

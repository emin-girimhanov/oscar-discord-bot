""" Achievement badges and personal study progress tracker for OSCAR.

    Implements gamification badges (Issue #11) and personal study progress analytics
    (Issue #48) while strictly preserving user privacy (no cohort tracking without consent).
"""

from dataclasses import dataclass
import re

from util.database import get_database
from util.enums import LanguageCode, ModuleLanguage, StudyCourse
from util.module import Module


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class Badge:
    """Represents an achievement badge earned or locked by a student."""
    id: str
    emoji: str
    name_de: str
    name_en: str
    desc_de: str
    desc_en: str
    unlocked: bool
    current: int
    target: int

    @property
    def progress_pct(self) -> int:
        """Progress percentage capped at 100%."""
        if self.target <= 0:
            return 100 if self.unlocked else 0
        return min(100, int((self.current / self.target) * 100))

    def status_text(self, lang: LanguageCode) -> str:
        """Formatted progress status string."""
        if self.unlocked:
            return "Freigeschaltet 🎉" if lang == LanguageCode.DE else "Unlocked 🎉"
        return f"{self.current} / {self.target} ({self.progress_pct}%)"


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class UserProgress:
    """Summary of a student's personal study progress and achievements."""
    user_id: int
    has_profile: bool
    major: StudyCourse | None
    po: int | None
    semester: int | None
    planned_modules_count: int
    planned_cp: int
    target_cp: int
    study_groups_count: int
    feedback_count: int
    badges: tuple[Badge, ...]

    @property
    def unlocked_badges_count(self) -> int:
        """Number of unlocked badges."""
        return sum(1 for b in self.badges if b.unlocked)

    @property
    def total_badges_count(self) -> int:
        """Total number of available badges."""
        return len(self.badges)

    @property
    def completion_pct(self) -> int:
        """Percentage of semester CP goal (30 CP)."""
        if self.target_cp <= 0:
            return 0
        return min(100, int((self.planned_cp / self.target_cp) * 100))

    def progress_bar(self, length: int = 10) -> str:
        """Renders a text progress bar like [██████░░░░] 60%."""
        pct = self.completion_pct
        filled = int((pct / 100.0) * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}] {pct}%"


def extract_module_cp(module: Module) -> int:
    """Extracts integer credit points from a module."""
    if not module.credit_points:
        return 0
    numbers = re.findall(r"\d+", str(module.credit_points))
    return int(numbers[0]) if numbers else 0


def check_language_diversity(modules: list[Module]) -> int:
    """Counts distinct teaching languages in the module list (max 2: DE and EN)."""
    has_de = any(
        m.language in (ModuleLanguage.DE, ModuleLanguage.EN_DE)
        for m in modules
    )
    has_en = any(
        m.language in (ModuleLanguage.EN, ModuleLanguage.EN_DE)
        for m in modules
    )
    return (1 if has_de else 0) + (1 if has_en else 0)


# pylint: disable=too-many-arguments,too-many-positional-arguments
def _build_all_badges(
    has_profile: bool,
    num_modules: int,
    planned_cp: int,
    study_groups_count: int,
    feedback_count: int,
    lang_count: int,
    golf_count: int = 0,
) -> tuple[Badge, ...]:
    """Instantiates the catalog of user badges evaluated with current metrics."""
    return (
        Badge(
            id="profile_setup",
            emoji="🎯",
            name_de="Startklar",
            name_en="Ready to Go",
            desc_de="Profil eingerichtet mit Studiengang und Semester via /start",
            desc_en="Profile configured with major and semester via /start",
            unlocked=has_profile,
            current=1 if has_profile else 0,
            target=1,
        ),
        Badge(
            id="first_module",
            emoji="📌",
            name_de="Erste Schritte",
            name_en="First Steps",
            desc_de="Erstes Modul im Semesterplan gespeichert",
            desc_en="First module saved to semester plan",
            unlocked=num_modules >= 1,
            current=min(1, num_modules),
            target=1,
        ),
        Badge(
            id="planner_15cp",
            emoji="📝",
            name_de="Auf Kurs (15 CP)",
            name_en="On Track (15 CP)",
            desc_de="Mindestens 15 CP im Semesterplan hinterlegt",
            desc_en="At least 15 CP planned in semester schedule",
            unlocked=planned_cp >= 15,
            current=min(15, planned_cp),
            target=15,
        ),
        Badge(
            id="semester_master",
            emoji="⚖️",
            name_de="Semestermeister (30 CP)",
            name_en="Semester Master (30 CP)",
            desc_de="Volle 30 CP Regelstudienleistung geplant",
            desc_en="Full 30 CP standard semester workload planned",
            unlocked=planned_cp >= 30,
            current=min(30, planned_cp),
            target=30,
        ),
        Badge(
            id="power_planner",
            emoji="🚀",
            name_de="Power-Planer (45+ CP)",
            name_en="Power Planner (45+ CP)",
            desc_de="Ambitionierte 45+ CP oder 8+ Module geplant",
            desc_en="Ambitious 45+ CP or 8+ modules planned",
            unlocked=(planned_cp >= 45 or num_modules >= 8),
            current=min(45, max(planned_cp, num_modules * 5)),
            target=45,
        ),
        Badge(
            id="study_buddy",
            emoji="👥",
            name_de="Teamplayer",
            name_en="Team Player",
            desc_de="Einer Lerngruppe für ein Modul beigetreten via /studybuddy",
            desc_en="Joined a study group for a module via /studybuddy",
            unlocked=study_groups_count >= 1,
            current=min(1, study_groups_count),
            target=1,
        ),
        Badge(
            id="polyglot",
            emoji="🌐",
            name_de="Polyglott",
            name_en="Polyglot",
            desc_de="Sowohl deutsch- als auch englischsprachige Module im Plan",
            desc_en="Planned modules in both German and English",
            unlocked=lang_count >= 2,
            current=min(2, lang_count),
            target=2,
        ),
        Badge(
            id="feedback_hero",
            emoji="💬",
            name_de="OSCAR-Pate",
            name_en="OSCAR Patron",
            desc_de="Feedback zur Verbesserung des Bots eingereicht via /feedback",
            desc_en="Submitted feedback to improve OSCAR via /feedback",
            unlocked=feedback_count >= 1,
            current=min(1, feedback_count),
            target=1,
        ),
        Badge(
            id="code_golfer",
            emoji="⛳",
            name_de="Code-Golfer",
            name_en="Code Golfer",
            desc_de="Eine Lösung für eine Code-Golf-Challenge eingereicht",
            desc_en="Submitted a solution for a code golf challenge",
            unlocked=golf_count >= 1,
            current=min(1, golf_count),
            target=1,
        ),
    )


# pylint: disable=too-many-locals
def compute_user_progress(user_id: int) -> UserProgress:
    """Calculates all progress indicators and badges for the specified user."""
    db = get_database()
    prefs = db.get_preferences(user_id)
    has_profile = prefs is not None and prefs.get("major") is not None

    major_raw = prefs.get("major") if prefs else None
    major: StudyCourse | None = None
    if major_raw is not None:
        try:
            major = StudyCourse(int(major_raw))
        except (ValueError, TypeError):
            major = None

    po = prefs.get("po") if prefs else None
    semester = prefs.get("semester") if prefs else None

    # Get modules in semester plan
    modules = db.get_semesterplan(user_id)
    planned_cp = sum(extract_module_cp(m) for m in modules)

    # Get study buddy groups
    study_groups = db.get_study_buddy_modules(user_id)

    # Get user feedback and challenge submissions count from export_user_data
    user_data = db.export_user_data(user_id)
    feedback_count = len(user_data.get("feedback") or [])
    golf_count = len(user_data.get("challenge_submissions") or [])
    lang_count = check_language_diversity(modules)

    badges = _build_all_badges(
        has_profile=has_profile,
        num_modules=len(modules),
        planned_cp=planned_cp,
        study_groups_count=len(study_groups),
        feedback_count=feedback_count,
        lang_count=lang_count,
        golf_count=golf_count,
    )

    return UserProgress(
        user_id=user_id,
        has_profile=has_profile,
        major=major,
        po=po,
        semester=semester,
        planned_modules_count=len(modules),
        planned_cp=planned_cp,
        target_cp=30,
        study_groups_count=len(study_groups),
        feedback_count=feedback_count,
        badges=badges,
    )

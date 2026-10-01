""" This Module defines various typed dictionarys for representationg strucutured data."""

from typing import Required, TypedDict

from util.enums import LanguageCode, StudyCourse



# pylint: disable=C0103 # (invalid-name)
# Disabled because the spaces in the dictionary keys force us to use the functional syntax
TablesModuleDict = TypedDict(
    # """ Defines the shape of the data of a Module as provided by the tables (nextcloud) api."""
    'TablesModuleDict',
    {
        "Status": int,
        "Identifizierung": Required[int],
        "Modultitel": str,
        "Modultitel (englisch)": str,
        "Lehrstuhl": int,
        "Modulverantwortung": str,
        "Dozent:in": str,
        "Modulkürzel": str,
        "Credit Points": str,
        "Semesterlage": int,
        "Fachsemester": int,
        "Dauer": int,
        "Modulsprache": int,
        "Niveau": list[int],
        "Angestrebte Lernergebnisse": str,
        "Inhalt": str,
        "Arbeitsaufwand": str,
        "Studien-/Prüfungsleistung": str,
        "Lehrform / SWS": str,
        "Voraussetzungen nach Prüfungsordnung": str,
        "Empfohlene Voraussetzungen": str,
        "Medienformen": str,
        "Literatur": str,
        "Hinweise": str,
        "Erstprüfer": str,
        "Zweitprüfer": str,
        "Stellvertreter": str,
        "Verwendbarkeit B.Sc. INF": list[int],
        "Verwendbarkeit B.Sc. CV": list[int],
        "Verwendbarkeit B.Sc. INGINF": list[int],
        "Verwendbarkeit B.Sc. WIF": list[int],
        "Verwendbarkeit B.Sc. INF (bilingual)": list[int],
        "Verwendbarkeit M.Sc. INF": list[int],
        "Verwendbarkeit M.Sc. INGINF": list[int],
        "Verwendbarkeit M.Sc. WIF": list[int],
        "Verwendbarkeit M.Sc. DKE": list[int],
        "Verwendbarkeit M.Sc. DE": list[int],
        "Verwendbarkeit M.Sc. VC": list[int],
        "Moduluntertitel": str,
        "Exportiert nach": list[int],
        "Importiert von": str,
        "Freigabe am": str,
        "Lehrveranstaltungen": str,
        "Unregelmäßig": str,
        "Prüfungsvorleistung": str,
        "Translation": str,
    }, total=False
)


class ModuleDict(TypedDict, total=False):
    """ Defines the shape of the data of a Module."""
    status: int
    id: Required[int]
    title: str
    title_en: str
    chair: int
    responsibility: str
    lecturer: str
    abbreviation: str
    credit_points: str
    semester_position: int
    academic_semester: int
    duration: int
    language: Required[int]
    level: list[int]
    learning_goals: str
    content: str
    workload: str
    study_exam_type: str
    teaching_form_sws: str
    requirements_by_exam_regulations: str
    recommended_prerequisites: str
    media_forms: str
    literature: str
    notes: str
    first_examiner: str
    second_examiner: str
    substitute: str
    usability_bsc_inf: list[int]
    usability_bsc_cv: list[int]
    usability_bsc_inginf: list[int]
    usability_bsc_wif: list[int]
    usability_bsc_inf_bilingual: list[int]
    usability_msc_inf: list[int]
    usability_msc_inginf: list[int]
    usability_msc_wif: list[int]
    usability_msc_dke: list[int]
    usability_msc_de: list[int]
    usability_msc_vc: list[int]
    subtitle: str
    exported_to: list[int]
    imported_from: str
    released_on: str
    courses: str
    irregular: str
    exam_prerequisite: str
    translation: str


class PrefsDict(TypedDict, total=False):
    """ Defines the shape of the Preference data."""
    user_id: Required[int]
    language: Required[LanguageCode]
    major: StudyCourse
    spo: int
    winter_semester: bool
    semester: int


class FeedbackDict(TypedDict, total=False):
    """ Defines the shape of the provided Feedback data."""
    user_id: Required[int]
    intuitiveness: Required[int]      # should be from 1-4
    discoverability: Required[int]    # should be from 1-4
    usefulness: Required[int]         # should be from 1-4
    improvements: str
    wishes: str
    bugs: str

class FeedbackReviewDict(TypedDict):
    """ Defines the shape of the stored Feedback review data."""
    id: int
    user_id: int
    language: str
    timestamp: int    # as unix epoch time (eg. seconds) since Jan 01 1970. (UTC)
    intuitiveness: int
    discoverability: int
    usefulness: int
    improvements: str
    wishes: str
    bugs: str


class ModuleRatingDict(TypedDict):
    """ Defines the summary shape of ratings for a module."""
    count: int
    avg_rating: float | None
    avg_difficulty: float | None


class UserDataDict(TypedDict):
    """ Defines the shape of everything the database stores about one student.

        One entry per table that carries a discord id. The values are the stored
        rows themselves, not a prettier reading of them, because this is what a
        student gets handed out when they ask what we hold about them.
    """
    user_id: int
    account: dict[str, object] | None        # the row in `users`
    preferences: dict[str, object] | None    # the row in `preferences`
    semester_plan: list[dict[str, object]]   # the rows in `semester_plans`
    feedback: list[dict[str, object]]        # the rows in `feedback`
    study_buddies: list[dict[str, object]]   # the rows in `study_buddies`
    module_ratings: list[dict[str, object]]  # the rows in `module_ratings`
    challenge_submissions: list[dict[str, object]]  # rows in `challenge_submissions`


class ChallengeSubmissionDict(TypedDict):
    """ Defines the shape of a code golf challenge submission."""
    user_id: int
    challenge_id: str
    language: str
    code_length: int
    code_snippet: str
    timestamp: int


class LeaderboardEntryDict(TypedDict):
    """ Defines an entry on the code golf leaderboard."""
    user_id: int
    name: str | None
    language: str
    code_length: int
    timestamp: int
    rank: int


class TopModuleDict(TypedDict):
    """ Defines the shape of a popular module in cohort statistics."""
    id: int
    title: str
    title_en: str
    count: int
    percentage: int


class MajorDistDict(TypedDict):
    """ Defines student distribution per study course."""
    major: str
    count: int
    percentage: int


class CohortStatsDict(TypedDict):
    """ Defines the aggregate cohort statistics shape."""
    has_sufficient_data: bool
    min_cohort_size: int
    cohort_size: int
    major_size: int
    total_registered_students: int
    avg_modules_planned: float | None
    avg_cp_planned: float | None
    top_modules: list[TopModuleDict]
    major_distribution: list[MajorDistDict]

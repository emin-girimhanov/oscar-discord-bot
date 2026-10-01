""" The portals a student at the FIN actually uses, and what to log in with.

    Answers Issue #51, "which learning management system does the faculty use?". The
    answer turned out to be shorter than the first version of this file assumed.

    **Every address here was resolved and opened.** The list used to name four hosts
    that do not exist. `moodle2.cs.ovgu.de`, `webwork.cs.ovgu.de`, `gitlab.cs.ovgu.de`
    and `handbook.cs.ovgu.de` all answer NXDOMAIN, from the university's own resolver
    as well as from outside. A student following `/lms` landed in a browser error, and
    the module card sent them to the same place.

    So the guide names the four portals that answer:

    * `elearning.ovgu.de` is the Moodle. There is one, it is the central one, and the
      URZ documents it as the e-learning platform of the whole university.
    * `lsf.ovgu.de` is where an exam registration legally counts.
    * `bookstack.cs.ovgu.de` holds the module handbooks, and `util.bookstack` already
      deep links into it.
    * `isggit3.cs.ovgu.de` is the faculty GitLab. OSCAR itself lives there.

    Add nothing here you have not opened. A dead portal in a guide is worse than no
    guide, because the student believes the bot.
"""

from dataclasses import dataclass


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class LearningPlatform:
    """Represents an academic learning platform or examination portal."""
    key: str
    name: str
    emoji: str
    url: str
    login_type_de: str
    login_type_en: str
    scope_de: str
    scope_en: str
    description_de: str
    description_en: str
    tips_de: str
    tips_en: str


# The Moodle comes first. It is where the material of a course is, which is what a
# student is looking for when they open the guide at all.
FIN_PLATFORMS: tuple[LearningPlatform, ...] = (
    LearningPlatform(
        key="elearning",
        name="eLearning (Moodle)",
        emoji="🎓",
        url="https://elearning.ovgu.de",
        login_type_de="OvGU-Account, Knopf „Login mit OvGU-Account“ (Shibboleth)",
        login_type_en="OvGU account, the “Login mit OvGU-Account” button (Shibboleth)",
        scope_de="Vorlesungsmaterial, Übungsblätter, Abgaben und Foren",
        scope_en="Lecture material, exercise sheets, submissions and forums",
        description_de=(
            "Die E-Learning-Plattform der Otto-von-Guericke-Universität, betrieben vom "
            "Universitätsrechenzentrum. Hier liegen Folien, Übungsblätter, Abgaben und "
            "die Einschreibung in Übungsgruppen, auch für die Informatik-Module."
        ),
        description_en=(
            "The e-learning platform of Otto von Guericke University, run by the "
            "computing centre. It holds slides, exercise sheets, submissions and the "
            "enrolment into tutorial groups, for computer science modules as well."
        ),
        tips_de=(
            "💡 **Tipp:** Viele Kurse brauchen einen Einschreibeschlüssel. Er wird in "
            "der ersten Vorlesung genannt. Eine Einschreibung hier ist **keine** "
            "Prüfungsanmeldung, die läuft über das LSF."
        ),
        tips_en=(
            "💡 **Tip:** Many courses need an enrolment key, announced in the first "
            "lecture. Enrolling here is **not** an exam registration, that happens "
            "on LSF."
        ),
    ),
    LearningPlatform(
        key="lsf",
        name="LSF Portal (HISinOne)",
        emoji="📅",
        url="https://lsf.ovgu.de",
        login_type_de="Zentraler Uni-Account",
        login_type_en="Central Uni Account",
        scope_de="Rechtsverbindliche Prüfungsanmeldungen, Notenspiegel & Raumpläne",
        scope_en="Legally binding exam registrations, transcript of records & room schedules",
        description_de=(
            "Das offizielle Campus-Management-System der Universität. "
            "Unverzichtbar für Vorlesungszeiten, Hörsaalbelegungen, rechtssichere "
            "Prüfungsan- und -abmeldungen sowie den Notenspiegel."
        ),
        description_en=(
            "The official campus management portal. Indispensable for lecture schedules, "
            "room bookings, legally binding exam registrations and withdrawals, and transcripts."
        ),
        tips_de=(
            "⚠️ **Achtung Prüfungen:** Eine Einschreibung im Moodle ist KEINE Prüfungsanmeldung! "
            "Prüfungen müssen ausnahmslos im LSF angemeldet werden. Die Fristen stehen "
            "in `/help` unter „Öffnen“."
        ),
        tips_en=(
            "⚠️ **Exam Warning:** Enrolling in Moodle is NOT an exam registration! "
            "Examinations must strictly be registered on LSF. The deadlines are in "
            "`/help` under “Open”."
        ),
    ),
    LearningPlatform(
        key="handbook",
        name="Modulhandbuch (BookStack)",
        emoji="📖",
        url="https://bookstack.cs.ovgu.de",
        login_type_de="Öffentlich, kein Login zum Lesen",
        login_type_en="Public, no login needed to read",
        scope_de="Offizielle Modulbeschreibungen, Lehrinhalte & Prüfungsformen",
        scope_en="Official module specifications, syllabus contents & exam formats",
        description_de=(
            "Die offizielle Wissensdatenbank der FIN für alle Studien- und Prüfungsordnungen. "
            "Enthält vollständige Modulbeschreibungen, SWS, Leistungspunkte und Verwendbarkeiten."
        ),
        description_en=(
            "The official FIN knowledge base for all examination regulations. "
            "Contains comprehensive module descriptions, credit points, prerequisites, and scope."
        ),
        tips_de=(
            "💡 **Tipp:** OSCAR verlinkt bei jedem Modul direkt auf die passende "
            "Handbuchseite deines Studiengangs (`/module`)."
        ),
        tips_en=(
            "💡 **Tip:** OSCAR provides direct links to the relevant handbook page "
            "for your study programme on every module overview (`/module`)."
        ),
    ),
    LearningPlatform(
        key="gitlab",
        name="FIN GitLab",
        emoji="🦊",
        url="https://isggit3.cs.ovgu.de",
        login_type_de="FIN-Account (LDAP)",
        login_type_en="FIN CS Account (LDAP)",
        scope_de="Programmierpraktika, Softwareprojekte & Lehrstuhl-Repositories",
        scope_en="Programming labs, software projects & chair repositories",
        description_de=(
            "Die Git-Plattform der Fakultät für Quellcode, Issues, Code Reviews und "
            "CI/CD-Pipelines in praktischen Projekten."
        ),
        description_en=(
            "The faculty Git platform for source code, issues, code reviews and CI/CD "
            "pipelines in practical projects."
        ),
        tips_de=(
            "💡 **Tipp:** Login per FIN-Passwort oder SSH-Schlüssel. OSCAR selbst wird "
            "auf diesem Server entwickelt."
        ),
        tips_en=(
            "💡 **Tip:** Log in with your FIN password or an SSH key. OSCAR itself is "
            "developed on this server."
        ),
    ),
)


# What the module card and the `/lms` guide open when nothing else is picked.
DEFAULT_PLATFORM_KEY: str = "elearning"


def get_platform_by_key(key: str) -> LearningPlatform | None:
    """Finds a platform by its unique key."""
    for p in FIN_PLATFORMS:
        if p.key == key:
            return p
    return None


def get_default_platform() -> LearningPlatform:
    """The platform to open when a student did not name one.

        Returns:
            The eLearning Moodle, which is where course material lives.
    """
    platform = get_platform_by_key(DEFAULT_PLATFORM_KEY)
    assert platform is not None, "the default platform has to be in the list"
    return platform

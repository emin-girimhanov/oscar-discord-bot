""" This module contains various translation dictionarys for the OSCAR Discord bot."""
# pylint: disable=too-many-lines


from loguru import logger

from util.enums import LanguageCode, ModuleLanguage, StudyCourse, PO


def t(lang: LanguageCode, key: str, translations: dict[str, dict[LanguageCode, str]]) -> str:
    """Gibt die Übersetzung für einen Key in der angegebenen Sprache zurück."""
    return translations.get(key, {}).get(lang, f"[{key}]")


def ratings_label(lang: LanguageCode, count: int) -> str:
    """ The word after a number of ratings, in the right number.

        Parameters:
            lang: The language the student reads in.
            count: How many ratings there are.

        Returns:
            "Bewertung" for one, "Bewertungen" for anything else.
    """
    key = "ratings_count_one" if count == 1 else "ratings_count"
    # imported late, RATING_TEXTS is defined further down this module
    return t(lang, key, RATING_TEXTS)



LANGUAGES: dict[LanguageCode, dict[LanguageCode, str]] = {
    LanguageCode.DE: {
        LanguageCode.DE: "Deutsch",
        LanguageCode.EN: "German",
    },
    LanguageCode.EN: {
        LanguageCode.DE: "Englisch",
        LanguageCode.EN: "English",
    },
}


# The names of the module languages. The entries for a single language are the ones
# of `LANGUAGES`, so a module and the bot itself never name a language differently.
MODULE_LANGUAGES: dict[ModuleLanguage, dict[LanguageCode, str]] = {
    ModuleLanguage.EN: LANGUAGES[LanguageCode.EN],
    ModuleLanguage.DE: LANGUAGES[LanguageCode.DE],
    ModuleLanguage.EN_DE: {
        LanguageCode.DE: "Englisch/Deutsch",
        LanguageCode.EN: "english/deutsch",
    },
}


def module_language_name(
    module_language: ModuleLanguage | LanguageCode | int | str,
    display_language: LanguageCode = LanguageCode.EN
) -> str:
    """ Returns the name of a modules language in the requested display language.

        The value comes straight from the `Modulsprache` column or from the name a
        module was stored with, so it can also be something we do not know yet. An
        unknown value is named english instead of raising, the same way
        `Module.from_tables_dict` reads one.

        Parameters:
            module_language: The language a module is taught in.
            display_language: The language the name is rendered in.

        Returns:
            The name of the module language, for example `english/deutsch`.
    """
    language: ModuleLanguage = ModuleLanguage.EN
    try:
        if isinstance(module_language, str):
            language = ModuleLanguage.from_language_code(module_language)
        else:
            language = ModuleLanguage(int(module_language))
    except (KeyError, ValueError):
        logger.warning(f"unknown module language: '{module_language}', assuming english")

    names: dict[LanguageCode, str] = MODULE_LANGUAGES[language]
    return names.get(display_language, names[LanguageCode.EN])


STUDY_COURSES: dict[StudyCourse, dict[LanguageCode, str]] = {
    StudyCourse.BSC_INF: {
        LanguageCode.DE: "B.Sc. Informatik",
        LanguageCode.EN: "B.Sc. Computer Science",
    },
    StudyCourse.BSC_CV: {
        LanguageCode.DE: "B.Sc. Computervisualistik",
        LanguageCode.EN: "B.Sc. Computervisualistik",
    },
    StudyCourse.BSC_INGINF: {
        LanguageCode.DE: "B.Sc. Ingenieurinformatik",
        LanguageCode.EN: "B.Sc. Ingenieurinformatik",
    },
    StudyCourse.BSC_WIF: {
        LanguageCode.DE: "B.Sc. Wirtschaftsinformatik",
        LanguageCode.EN: "B.Sc. Wirtschaftsinformatik",
    },
    StudyCourse.BSC_INF_BILINGUAL: {
        LanguageCode.DE: "B.Sc. Informatik (bilingual)",
        LanguageCode.EN: "B.Sc. Computer Science (bilingual)",
    },
    StudyCourse.MSC_INF: {
        LanguageCode.DE: "M.Sc. Informatik",
        LanguageCode.EN: "M.Sc. Computer Science",
    },
    StudyCourse.MSC_INGINF: {
        LanguageCode.DE: "M.Sc. Ingenieurinformatik",
        LanguageCode.EN: "M.Sc. Ingenieurinformatik",
    },
    StudyCourse.MSC_WIF: {
        LanguageCode.DE: "M.Sc. Wirtschaftsinformatik",
        LanguageCode.EN: "M.Sc. Wirtschaftsinformatik",
    },
    StudyCourse.MSC_DKE: {
        LanguageCode.DE: "M.Sc. Data and Knowledge Engineering",
        LanguageCode.EN: "M.Sc. Data and Knowledge Engineering",
    },
    StudyCourse.MSC_DE: {
        LanguageCode.DE: "M.Sc. Digital Engineering",
        LanguageCode.EN: "M.Sc. Digital Engineering",
    },
    StudyCourse.MSC_VC: {
        LanguageCode.DE: "M.Sc. Visual Computing",
        LanguageCode.EN: "M.Sc. Visual Computing",
    }
}


HELP_LANGUAGES: dict[str, dict[LanguageCode, str]] = {
    "help": {
        LanguageCode.DE: "Hilfe",
        LanguageCode.EN: "Help",
    },
    "description": {
        LanguageCode.DE: """Hey, willkommen bei OSCAR.

**Öffnen** startet eine Funktion direkt.
**Befehl** erklärt einen der Befehle im Slash-Menü.
**Frage** beantwortet, was Studierende am häufigsten fragen.""",
        LanguageCode.EN: """Hey, welcome to OSCAR.

**Open** starts a feature right away.
**Command** explains one of the commands in the slash menu.
**Question** answers what students ask most often.""",
    },
    "select_option_1": {
        LanguageCode.DE: "Modulinformationen",
        LanguageCode.EN: "Module information",
    },
    "select_option_2": {
        LanguageCode.DE: "Modulsuche",
        LanguageCode.EN: "Module search",
    },
    "select_option_3": {
        LanguageCode.DE: "Modulfilterung",
        LanguageCode.EN: "Module filtering",
    },
    "select_option_4": {
        LanguageCode.DE: "Semesterplanung",
        LanguageCode.EN: "Semester Planning",
    },
    "select_option_5": {
        LanguageCode.DE: "Sonstiges",
        LanguageCode.EN: "Other",
    },
    "faq_placeholder": {
        LanguageCode.DE: "Frage: Was Studierende oft fragen",
        LanguageCode.EN: "Question: what students often ask",
    },
    "open_placeholder": {
        LanguageCode.DE: "Öffnen: eine Funktion starten",
        LanguageCode.EN: "Open: start a feature",
    },
    "command_placeholder": {
        LanguageCode.DE: "Befehl: was ein Slash-Befehl tut",
        LanguageCode.EN: "Command: what a slash command does",
    },
    "core_note": {
        LanguageCode.DE: (
            "Das Slash-Menü führt nur die Befehle, die du beim Tippen brauchst. "
            "Alles andere startest du oben unter **Öffnen**."
        ),
        LanguageCode.EN: (
            "The slash menu only lists the commands you need while typing. "
            "Everything else starts under **Open** above."
        ),
    },
}


START_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "welcome_title": {
        LanguageCode.DE: "# WILLKOMMEN BEI OSCAR",
        LanguageCode.EN: "# WELCOME TO OSCAR",
    },
    "welcome_text": {
        LanguageCode.DE: "Willkommenstext hier",
        LanguageCode.EN: "Welcome text here",
    },
    "before_info": {
        LanguageCode.DE: "Bevor wir starten, brauchen wir ein paar Informationen über dich.",
        LanguageCode.EN: "Before we start, we need some information about you.",
    },
    "language_question": {
        LanguageCode.DE: "Bevorzugst du Englisch oder Deutsch als Sprache?",
        LanguageCode.EN: "Do you prefer English or German as your language of choice?",
    },
    "semester_question": {
        LanguageCode.DE: """**Basierend auf deiner Serverrolle bist du im {semester}. Semester.
Stimmt das?**""",
        LanguageCode.EN: """**Based on your server role, you are in the {semester} semester.
Is this true?**""",
    },
    "commands_info": {
        LanguageCode.DE: "**Hier sind die Befehle, die du nutzen kannst:**",
        LanguageCode.EN: "**Here are the commands you can use:**",
    },
    "thank_you": {
        LanguageCode.DE: "Danke, dass du OSCAR benutzt.",
        LanguageCode.EN: "Thank you for using OSCAR.",
    },
    "more_commands": {
        LanguageCode.DE: (
            "\nEs gibt noch mehr, zum Beispiel `/klausuren`, `/fristen`, "
            "`/ansprechpartner` und `/standard_plan`. **`/help` erklärt jeden Befehl** "
            "und startet ihn auch, wenn du den Namen noch nicht kennst."
        ),
        LanguageCode.EN: (
            "\nThere are more, for example `/klausuren`, `/fristen`, "
            "`/ansprechpartner` and `/standard_plan`. **`/help` explains every command** "
            "and starts it too, if you do not know the name yet."
        ),
    },
    "subject":{
        LanguageCode.DE: "Welchen Studiengang studierst du?",
        LanguageCode.EN: "Which subject are you studying?"
    }
}


# One entry per registered slash command. The keys are the command names, so a typo
# here is visible next to the real name instead of hiding in a view.
COMMAND_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "rate": {
        LanguageCode.DE: "bewertet ein Modul mit Sternen, Schwierigkeit und Erfahrungsbericht",
        LanguageCode.EN: "rates a module with stars, a difficulty and a written review",
    },
    "klausuren": {
        LanguageCode.DE: "zeigt die Altklausuren-Archive der Fachschaftsräte",
        LanguageCode.EN: "shows the past exam archives of the student councils",
    },
    "lms": {
        LanguageCode.DE: "erklärt die Portale der Uni: eLearning, LSF, Modulhandbuch, GitLab",
        LanguageCode.EN: "explains the university portals: eLearning, LSF, handbook, GitLab",
    },
    "codegolf": {
        LanguageCode.DE: "zeigt die wöchentliche Programmier-Challenge und die Rangliste",
        LanguageCode.EN: "shows the weekly programming challenge and the leaderboard",
    },
    "cohort": {
        LanguageCode.DE: "vergleicht deinen Stand anonym mit deinem Jahrgang",
        LanguageCode.EN: "compares your progress with your cohort, anonymously",
    },
    "here": {
        LanguageCode.DE: "zeigt das Modul, nach dem der aktuelle Kanal benannt ist",
        LanguageCode.EN: "shows the module the current channel is named after",
    },
    "start": {
        LanguageCode.DE: "richtet dich ein und speichert Studiengang, Prüfungsordnung und Semester",
        LanguageCode.EN: "sets you up and saves your programme, regulations and semester",
    },
    "my_data": {
        LanguageCode.DE: "zeigt dir alles, was wir über dich speichern, und löscht es auf Wunsch",
        LanguageCode.EN: "shows you everything we store about you, and deletes it on request",
    },
    "module": {
        LanguageCode.DE: "findet ein Modul und zeigt die Infos dazu",
        LanguageCode.EN: "finds a module and shows its details",
    },
    "compare": {
        LanguageCode.DE: "stellt zwei oder drei Module nebeneinander",
        LanguageCode.EN: "puts two or three modules side by side",
    },
    "filter": {
        LanguageCode.DE: "filtert Module nach Kriterien wie CP, SWS und Thema",
        LanguageCode.EN: "filters modules by criteria such as CP, SWS and topic",
    },
    "semesterplan": {
        LanguageCode.DE: "zeigt deine gemerkten Module und vergleicht sie mit dem Regelstudienplan",
        LanguageCode.EN: "shows your saved modules and compares them to the standard study plan",
    },
    "standard_plan": {
        LanguageCode.DE: "zeigt den Regelstudienplan für deinen Studiengang und deine PO",
        LanguageCode.EN: "shows the standard study plan for your programme and regulations",
    },
    "feedback": {
        LanguageCode.DE: "schickt uns Rückmeldung zum Bot",
        LanguageCode.EN: "sends us feedback about the bot",
    },
    "help": {
        LanguageCode.DE: "öffnet die Hilfe",
        LanguageCode.EN: "opens the help dialog",
    },
    "studybuddy": {
        LanguageCode.DE: "findet oder gründet Lerngruppen für deine Module",
        LanguageCode.EN: "finds or creates study groups for your modules",
    },
    "ansprechpartner": {
        LanguageCode.DE: "zeigt wichtige Ansprechpartner der FIN und OVGU",
        LanguageCode.EN: "shows key contacts at FIN and OVGU",
    },
    "badges": {
        LanguageCode.DE: "zeigt deine freigeschalteten Badges und Erfolge",
        LanguageCode.EN: "shows your unlocked badges and achievements",
    },
    "progress": {
        LanguageCode.DE: "zeigt deinen Studienfortschritt und Credit Points",
        LanguageCode.EN: "shows your study progress and credit points",
    },
    "fristen": {
        LanguageCode.DE: "zeigt Semester- und Prüfungsfristen der FIN & OVGU",
        LanguageCode.EN: "shows semester and exam deadlines at FIN & OVGU",
    },
    "suggest": {
        LanguageCode.DE: "schlägt passende Module nach Studiengang, Semester und Schwerpunkt vor",
        LanguageCode.EN: "proposes fitting modules by programme, semester, and focus area",
    },
}


# What `/help` answers once a command is picked. Same keys as `COMMAND_TEXTS`, so a
# new command cannot appear in the list without an answer behind it.
HELP_ANSWERS: dict[str, dict[LanguageCode, str]] = {
    "rate": {
        LanguageCode.DE: (
            "**/rate**\n"
            "Bewerte ein Modul, das du belegt hast: ein bis fünf Sterne, dazu eine "
            "Schwierigkeit von eins bis fünf.\n\n"
            "Das Kommentarfeld ist freiwillig und der wichtigste Teil. Der Schnitt "
            "sagt nur *wie gut*, dein Satz sagt *warum*.\n\n"
            "Du kannst ein Modul nur einmal bewerten. Eine neue Bewertung ersetzt "
            "deine alte. Bewertungen werden ohne Namen gezeigt, deine eigene löschst "
            "du mit `/my_data`.\n\n"
            "Lesen kannst du sie auf der Modulkarte unter **💬 Erfahrungen**."
        ),
        LanguageCode.EN: (
            "**/rate**\n"
            "Rate a module you have taken: one to five stars, plus a difficulty from "
            "one to five.\n\n"
            "The comment field is optional and the important part. The average only "
            "says *how good*, your sentence says *why*.\n\n"
            "You can rate a module once. A new rating replaces your old one. Reviews "
            "are shown without a name, delete your own with `/my_data`.\n\n"
            "Read them on the module card under **💬 Reviews**."
        ),
    },
    "klausuren": {
        LanguageCode.DE: (
            "**/klausuren**\n"
            "Zeigt die Altklausuren-Archive der Fachschaftsräte, mit einem Knopf pro "
            "Archiv.\n\n"
            "FaRaFIN für Informatik, FaraWiwi für die FWW-Module der "
            "Wirtschaftsinformatik, FaraMath für Mathe.\n\n"
            "OSCAR speichert keine Klausur selbst. Das Urheberrecht liegt beim "
            "Lehrstuhl."
        ),
        LanguageCode.EN: (
            "**/klausuren**\n"
            "Shows the past exam archives of the student councils, one button each.\n\n"
            "FaRaFIN for computer science, FaraWiwi for the FWW modules of Business "
            "Informatics, FaraMath for maths.\n\n"
            "OSCAR stores no exam itself. The copyright sits with the chair."
        ),
    },
    "lms": {
        LanguageCode.DE: (
            "**/lms**, auch **/elearning**\n"
            "Erklärt die vier Portale der Uni und was du wo brauchst.\n\n"
            "**eLearning** (elearning.ovgu.de) hat das Kursmaterial.\n"
            "**LSF** (lsf.ovgu.de) ist die einzige Stelle, an der eine "
            "Prüfungsanmeldung zählt.\n"
            "**BookStack** hat die Modulhandbücher, **FIN GitLab** den Code."
        ),
        LanguageCode.EN: (
            "**/lms**, also **/elearning**\n"
            "Explains the four portals and what each one is for.\n\n"
            "**eLearning** (elearning.ovgu.de) holds the course material.\n"
            "**LSF** (lsf.ovgu.de) is the only place an exam registration counts.\n"
            "**BookStack** holds the module handbooks, **FIN GitLab** the code."
        ),
    },
    "codegolf": {
        LanguageCode.DE: (
            "**/codegolf**, auch **/challenge**\n"
            "Die wöchentliche Programmier-Aufgabe. Gewertet wird die Länge deiner "
            "Lösung in Bytes, kürzer ist besser.\n\n"
            "Dein Code wird nicht ausgeführt. Die Einsendungen schaut ein Mensch an."
        ),
        LanguageCode.EN: (
            "**/codegolf**, also **/challenge**\n"
            "The weekly puzzle. Your solution is scored by its length in bytes, "
            "shorter is better.\n\n"
            "Your code is never executed. A human looks at the submissions."
        ),
    },
    "cohort": {
        LanguageCode.DE: (
            "**/cohort**, auch **/statistik**\n"
            "Vergleicht deinen Studienstand mit deinem Jahrgang: "
            "durchschnittlich geplante Module, Credit Points, beliebteste Kurse.\n\n"
            "Die Zahlen erscheinen erst ab drei Personen in einer Gruppe. Damit lässt "
            "sich niemand einzeln herauslesen."
        ),
        LanguageCode.EN: (
            "**/cohort**, also **/statistik**\n"
            "Compares your progress with your cohort: average planned modules, credit "
            "points, most planned courses.\n\n"
            "Numbers only appear from three people in a group upwards, so nobody can "
            "be singled out."
        ),
    },
    "here": {
        LanguageCode.DE: (
            "**/here**\n"
            "Der Server hat einen Kanal pro Modul. `/here` liest den Kanalnamen und "
            "öffnet die passende Modulkarte. Du tippst keinen Titel.\n\n"
            "Passt der Name auf mehrere Module, fragt OSCAR nach. Passt er auf keines, "
            "sagt er das und du nutzt `/module`.\n\n"
            "`/here` funktioniert nur in einem Server-Kanal, nicht in einer "
            "Direktnachricht."
        ),
        LanguageCode.EN: (
            "**/here**\n"
            "The server keeps one channel per module. `/here` reads the channel name "
            "and opens that module card. You type no title.\n\n"
            "If the name fits several modules, OSCAR asks. If it fits none, it says so "
            "and you use `/module`.\n\n"
            "`/here` only works in a server channel, not in a direct message."
        ),
    },
    "start": {
        LanguageCode.DE: (
            "Nutze `/start` einmal am Anfang.\n"
            "Du wählst Sprache, Semester, Studiengang und Prüfungsordnung.\n"
            "Ohne diese Angaben können `/semesterplan` und `/standard_plan` nichts zeigen.\n"
            "Du kannst `/start` jederzeit erneut aufrufen und alles ändern."
        ),
        LanguageCode.EN: (
            "Run `/start` once at the beginning.\n"
            "You pick your language, semester, programme and examination regulations.\n"
            "Without them `/semesterplan` and `/standard_plan` have nothing to show.\n"
            "You can run `/start` again at any time and change everything."
        ),
    },
    "my_data": {
        LanguageCode.DE: (
            "`/my_data` zeigt dir alles, was wir über dich gespeichert haben.\n"
            "Die Antwort sieht nur du, und der Knopf `⤓` lädt alles als JSON-Datei herunter.\n"
            "Der rote Knopf löscht Einstellungen, Semesterplan und dein Feedback.\n"
            "Vor dem Löschen fragen wir nach, danach ist nichts davon wiederherstellbar."
        ),
        LanguageCode.EN: (
            "`/my_data` shows you everything we have stored about you.\n"
            "Only you see the answer, and the `⤓` button downloads all of it as JSON.\n"
            "The red button deletes your preferences, your semester plan and your feedback.\n"
            "We ask before deleting, and afterwards none of it can be brought back."
        ),
    },
    "module": {
        LanguageCode.DE: (
            "Tippe `/module` und dann den Anfang des Modulnamens.\n"
            "Wähle einen Vorschlag aus der Liste, freier Text findet nichts.\n"
            "Die Karte zeigt Kürzel, SWS, Sprache, Dozent und Creditpoints.\n"
            "Über die Knöpfe kommst du ins LSF, ins Modulhandbuch oder zu mehr Infos."
        ),
        LanguageCode.EN: (
            "Type `/module` and then the start of the module name.\n"
            "Pick a suggestion from the list, free text finds nothing.\n"
            "The card shows the abbreviation, SWS, language, lecturer and credit points.\n"
            "The buttons take you to the LSF, to the handbook or to more details."
        ),
    },
    "compare": {
        LanguageCode.DE: (
            "`/compare` stellt zwei oder drei Module nebeneinander.\n"
            "Wähle die Module wie bei `/module` aus den Vorschlägen aus.\n"
            "Verglichen werden CP, Lehrform, Sprache, Prüfung und Dozent.\n"
            "Unten steht, worin sich die Module unterscheiden."
        ),
        LanguageCode.EN: (
            "`/compare` puts two or three modules next to each other.\n"
            "Pick them from the suggestions, the same way `/module` works.\n"
            "It compares CP, teaching form, language, exam and lecturer.\n"
            "The line at the bottom names what differs."
        ),
    },
    "filter": {
        LanguageCode.DE: (
            "`/filter` öffnet eine Maske mit Knöpfen.\n"
            "Angeklickte Knöpfe werden grün und zählen als Kriterium.\n"
            "Mehrere Knöpfe in einer Zeile gelten als oder, etwa 5 CP und mehr als 5 CP.\n"
            "Verschiedene Zeilen gelten als und, etwa 5 CP und Klausur.\n"
            "Drücke am Ende auf Suchen, das Ergebnis kommt als Liste mit Seiten.\n"
            "Über der Liste sortierst du nach Creditpoints oder nach Titel."
        ),
        LanguageCode.EN: (
            "`/filter` opens a mask made of buttons.\n"
            "A pressed button turns green and counts as a criterion.\n"
            "Several buttons in one row count as an or, say 5 CP and more than 5 CP.\n"
            "Different rows count as an and, say 5 CP and written exam.\n"
            "Press Search at the end, the result comes as a list with pages.\n"
            "Above the list you sort by credit points or by title."
        ),
    },
    "semesterplan": {
        LanguageCode.DE: (
            "`/semesterplan` zeigt die Module, die du dir gemerkt hast.\n"
            "Merken kannst du sie über den Knopf in der Modulkarte von `/module`.\n"
            "Darunter steht der Regelstudienplan für dein Semester.\n"
            "Ein Haken heißt, das Modul ist abgedeckt, ein Kreuz heißt, es fehlt noch."
        ),
        LanguageCode.EN: (
            "`/semesterplan` shows the modules you saved.\n"
            "You save them with the button on the module card from `/module`.\n"
            "Below that you see the standard study plan for your semester.\n"
            "A tick means the module is covered, a cross means it is still missing."
        ),
    },
    "standard_plan": {
        LanguageCode.DE: (
            "`/standard_plan` zeigt den ganzen Regelstudienplan als Bild und als Text.\n"
            "Er richtet sich nach deinem Studiengang, deiner PO und deinem Startsemester.\n"
            "Ein Haken markiert jedes Modul, das du schon gespeichert hast.\n"
            "OSCAR kennt keine Noten, der Haken sagt also nichts über das Bestehen.\n"
            "Blasse Kästen sind Wahlpflichtfächer, dort wählst du selbst ein Modul.\n"
            "Der Knopf führt zum offiziellen Modulhandbuch deines Studiengangs."
        ),
        LanguageCode.EN: (
            "`/standard_plan` shows the whole standard study plan as a picture and as text.\n"
            "It follows your programme, your regulations and your starting semester.\n"
            "A tick marks every module you already saved.\n"
            "OSCAR knows no grades, so a tick says nothing about passing.\n"
            "Pale boxes are electives, there you pick a module yourself.\n"
            "The button opens the official module handbook of your programme."
        ),
    },
    "feedback": {
        LanguageCode.DE: (
            "`/feedback` schickt uns deine Rückmeldung.\n"
            "Du bewertest drei Punkte und kannst freien Text dazu schreiben.\n"
            "Wir lesen alles, es hilft uns bei der nächsten Version."
        ),
        LanguageCode.EN: (
            "`/feedback` sends us your feedback.\n"
            "You rate three points and can add free text.\n"
            "We read all of it, it guides the next version."
        ),
    },
    "help": {
        LanguageCode.DE: (
            "Das hier ist die Hilfe.\n"
            "Wähle oben einen Befehl aus, dann erkläre ich ihn Schritt für Schritt.\n"
            "Mit dem Knopf rechts oben wechselst du die Sprache."
        ),
        LanguageCode.EN: (
            "This is the help.\n"
            "Pick a command above and I explain it step by step.\n"
            "The button in the top right switches the language."
        ),
    },
    "studybuddy": {
        LanguageCode.DE: (
            "`/studybuddy` hilft dir beim Finden von Lerngruppen.\n"
            "Wähle ein Modul aus und schließe dich der Lerngruppe an.\n"
            "Du siehst andere interessierte Studierende und kannst direkt einen Thread starten."
        ),
        LanguageCode.EN: (
            "`/studybuddy` helps you find study groups.\n"
            "Select a module and join the study group.\n"
            "You see other interested students and can start a study thread right away."
        ),
    },
    "ansprechpartner": {
        LanguageCode.DE: (
            "`/ansprechpartner` (oder `/contacts`) zeigt alle wichtigen Kontakte an der FIN.\n"
            "Enthält Studiendekanat, Prüfungsamt, FaRaFIN, Studiengangsleiter,\n"
            "Deutschlandstipendium, Praktikumsamt, Erasmus und psychologische Beratung."
        ),
        LanguageCode.EN: (
            "`/ansprechpartner` (or `/contacts`) lists key faculty and university contacts.\n"
            "Includes Dean of Studies, Exam Office, FaRaFIN, programme advisors,\n"
            "Germany Scholarship, Internship Office, Erasmus, and counseling."
        ),
    },
    "badges": {
        LanguageCode.DE: (
            "`/badges` zeigt deine Auszeichnungen und Meilensteine bei OSCAR.\n"
            "Erhalte Badges für Semesterplanung, Lerngruppen, Feedback und mehr.\n"
            "Die Anzeige ist privat und wird nur dir angezeigt."
        ),
        LanguageCode.EN: (
            "`/badges` displays your achievements and milestones in OSCAR.\n"
            "Earn badges for study planning, study groups, feedback, and more.\n"
            "The display is private and only visible to you."
        ),
    },
    "progress": {
        LanguageCode.DE: (
            "`/progress` zeigt dir deine geplante Studienleistung und CP-Balken.\n"
            "Vergleicht deine gemerkten Module mit den 30 CP Regelstudienleistung.\n"
            "Bleibt vollständig vertraulich ohne externe Kohortenüberwachung."
        ),
        LanguageCode.EN: (
            "`/progress` displays your planned workload and CP progress bar.\n"
            "Compares your saved modules with the 30 CP semester recommendation.\n"
            "Remains completely private with no cohort surveillance."
        ),
    },
    "fristen": {
        LanguageCode.DE: (
            "`/fristen` (oder `/deadlines`) zeigt die offiziellen Termine der FIN.\n"
            "Enthält Prüfungsanmeldung, Rückmeldung, Prüfungszeitraum und Vorlesungszeit.\n"
            "Erinnert dich an wichtige Ausschlussfristen und die 3-Tage-Abmelderegel."
        ),
        LanguageCode.EN: (
            "`/fristen` (or `/deadlines`) shows official FIN academic milestones.\n"
            "Includes exam registration, re-registration, exam period, and lecture dates.\n"
            "Reminds you of critical deadlines and the 3-day withdrawal policy."
        ),
    },
    "suggest": {
        LanguageCode.DE: (
            "`/suggest` (oder `/recommend`) schlägt dir passende Module für dein Studium vor.\n"
            "Berücksichtigt deinen Studiengang, dein Semester und noch offene Credit Points.\n"
            "Du kannst gezielt Schwerpunkte wie KI, Software Engineering oder Games wählen\n"
            "und vorgeschlagene Module direkt per Klick in deinen Semesterplan übernehmen."
        ),
        LanguageCode.EN: (
            "`/suggest` (or `/recommend`) proposes fitting modules for your degree.\n"
            "Considers your study programme, current semester, and missing credits.\n"
            "Filter specifically by clusters like AI, Systems Engineering, or Games,\n"
            "and save suggested modules directly into your semester plan with one click."
        ),
    },
}


# The questions students actually ask, and the honest answer to each one.
#
# This is the only copy. `/help` reads it at runtime and `docs/features/faq.md` renders
# it at build time through the `show_faq` macro, so the page and the bot cannot drift
# apart. Add a question here, not in the markdown.
#
# Keep an answer short. It has to stay readable inside a discord message on a phone.
FAQ_QUESTIONS: dict[str, dict[LanguageCode, str]] = {
    "commands_missing": {
        LanguageCode.DE: "Ich sehe keine Befehle, wenn ich / tippe",
        LanguageCode.EN: "I see no commands when I type /",
    },
    "module_not_found": {
        LanguageCode.DE: "Mein Modul wird nicht gefunden",
        LanguageCode.EN: "My module is not found",
    },
    "data_source": {
        LanguageCode.DE: "Woher kommen die Moduldaten?",
        LanguageCode.EN: "Where does the module data come from?",
    },
    "wrong_module_data": {
        LanguageCode.DE: "Bei einem Modul steht etwas Falsches",
        LanguageCode.EN: "A module shows something wrong",
    },
    "times_and_clashes": {
        LanguageCode.DE: "Warnt OSCAR mich vor Überschneidungen?",
        LanguageCode.EN: "Does OSCAR warn me about clashes?",
    },
    "remove_module": {
        LanguageCode.DE: "Wie werfe ich ein Modul wieder aus meinem Plan?",
        LanguageCode.EN: "How do I take a module out of my plan again?",
    },
    "change_settings": {
        LanguageCode.DE: "Ich habe mich beim Studiengang verklickt",
        LanguageCode.EN: "I picked the wrong programme",
    },
    "who_sees_plan": {
        LanguageCode.DE: "Wer sieht meinen Semesterplan?",
        LanguageCode.EN: "Who can see my semester plan?",
    },
    "stored_data": {
        LanguageCode.DE: "Was speichert OSCAR über mich?",
        LanguageCode.EN: "What does OSCAR store about me?",
    },
    "private_message": {
        LanguageCode.DE: "Kann ich OSCAR privat anschreiben?",
        LanguageCode.EN: "Can I use OSCAR in a private message?",
    },
    "mobile": {
        LanguageCode.DE: "Geht das auch am Handy?",
        LanguageCode.EN: "Does this work on a phone?",
    },
    "which_lms": {
        LanguageCode.DE: "Welche Plattformen nutzt die FIN?",
        LanguageCode.EN: "Which platforms does the FIN use?",
    },
}


# Same keys as FAQ_QUESTIONS, so a question cannot appear without an answer behind it.
FAQ_ANSWERS: dict[str, dict[LanguageCode, str]] = {
    "commands_missing": {
        LanguageCode.DE: (
            "Discord merkt sich die Befehlsliste und aktualisiert sie träge.\n"
            "Drücke `Strg+R`, das lädt den Client neu.\n"
            "Nach einer neuen Version kann es bis zu einer Stunde dauern.\n"
            "`!ping` und `!resync` sind Präfixbefehle und gehen auch ohne die Liste."
        ),
        LanguageCode.EN: (
            "Discord caches the command list and refreshes it lazily.\n"
            "Press `Ctrl+R`, that reloads the client.\n"
            "After a new version it can take up to an hour.\n"
            "`!ping` and `!resync` are prefix commands and work without the list."
        ),
    },
    "module_not_found": {
        LanguageCode.DE: (
            "`/module` arbeitet nur mit den Vorschlägen, nicht mit freiem Text.\n"
            "Tippe weniger und warte kurz, dann kommt die Liste.\n"
            "Wähle einen Eintrag aus, sonst findet der Befehl nichts.\n"
            "Wenn nichts passt, suche mit `/filter` über Kriterien."
        ),
        LanguageCode.EN: (
            "`/module` only works with the suggestions, not with free text.\n"
            "Type less and wait a moment, then the list appears.\n"
            "Pick an entry, otherwise the command finds nothing.\n"
            "If nothing fits, search by criteria with `/filter`."
        ),
    },
    "data_source": {
        LanguageCode.DE: (
            "Aus der Modultabelle der Fakultät auf `cloud.ovgu.de`.\n"
            "Die pflegt das Studiendekanat, nicht wir.\n"
            "OSCAR liest sie nur und schreibt nichts zurück.\n"
            "Der Knopf *zum Modulhandbuch* öffnet die offizielle Seite im BookStack."
        ),
        LanguageCode.EN: (
            "From the faculty module table on `cloud.ovgu.de`.\n"
            "The dean of studies office maintains it, not we.\n"
            "OSCAR only reads it and never writes back.\n"
            "The *to the handbook* button opens the official page in BookStack."
        ),
    },
    "wrong_module_data": {
        LanguageCode.DE: (
            "Die Daten gehören uns nicht, wir können sie nicht selbst ändern.\n"
            "Schick uns `/feedback` mit dem Modulnamen und dem, was falsch ist.\n"
            "Wir geben es weiter.\n"
            "Ein Vergleich mit dem Modulhandbuch hilft uns dabei sehr."
        ),
        LanguageCode.EN: (
            "The data is not ours, we cannot correct it ourselves.\n"
            "Send us `/feedback` with the module name and what is wrong.\n"
            "We pass it on.\n"
            "A comparison with the handbook helps us a lot."
        ),
    },
    "times_and_clashes": {
        LanguageCode.DE: (
            "Nein. OSCAR kennt keine Uhrzeiten.\n"
            "Das LSF bietet die Termine über keine offene Schnittstelle an.\n"
            "Prüfe Überschneidungen also selbst im LSF.\n"
            "Der Knopf *zum LSF-Modul* bringt dich direkt zur Suche."
        ),
        LanguageCode.EN: (
            "No. OSCAR does not know any times.\n"
            "LSF offers the dates through no open interface.\n"
            "So check clashes yourself in LSF.\n"
            "The *to LSF* button takes you straight to the search."
        ),
    },
    "remove_module": {
        LanguageCode.DE: (
            "Öffne `/semesterplan`.\n"
            "Neben jedem Modul steht ein rotes **X**.\n"
            "Ein Klick darauf nimmt das Modul sofort heraus.\n"
            "Hinzufügen geht über den Knopf in der Modulkarte von `/module`."
        ),
        LanguageCode.EN: (
            "Open `/semesterplan`.\n"
            "Next to every module there is a red **X**.\n"
            "One click takes the module out right away.\n"
            "You add one with the button on the module card from `/module`."
        ),
    },
    "change_settings": {
        LanguageCode.DE: (
            "Ruf `/start` einfach noch einmal auf.\n"
            "Deine Angaben werden dabei überschrieben.\n"
            "Das gilt für Sprache, Semester, Studiengang und Prüfungsordnung.\n"
            "Deine gemerkten Module bleiben erhalten."
        ),
        LanguageCode.EN: (
            "Just run `/start` again.\n"
            "It overwrites your settings.\n"
            "That covers language, semester, programme and examination regulations.\n"
            "The modules you saved stay."
        ),
    },
    "who_sees_plan": {
        LanguageCode.DE: (
            "Nur du.\n"
            "`/semesterplan`, `/start`, `/filter` und `/feedback` antworten dir privat.\n"
            "Andere im Kanal sehen die Nachricht nicht und können nichts anklicken.\n"
            "`/standard_plan` ist dagegen öffentlich, zeigt aber nur den offiziellen Plan."
        ),
        LanguageCode.EN: (
            "Only you.\n"
            "`/semesterplan`, `/start`, `/filter` and `/feedback` answer you privately.\n"
            "Others in the channel see nothing and can click nothing.\n"
            "`/standard_plan` is public, but it only shows the official plan."
        ),
    },
    "stored_data": {
        LanguageCode.DE: (
            "Deine Discord-ID, deine Sprache, dein Semester, deinen Studiengang "
            "und deine Prüfungsordnung.\n"
            "Dazu die Module, die du dir gemerkt hast, und dein Feedback.\n"
            "Keinen Namen, keine Mailadresse, keine Auswertung deines Verhaltens.\n"
            "Mehr steht in der Datenschutzerklärung auf der Doku-Seite."
        ),
        LanguageCode.EN: (
            "Your discord id, your language, your semester, your programme "
            "and your examination regulations.\n"
            "Plus the modules you saved and any feedback you sent.\n"
            "No name, no mail address, no tracking of what you do.\n"
            "The privacy policy on the documentation site has the details."
        ),
    },
    "private_message": {
        LanguageCode.DE: (
            "Nutze OSCAR lieber auf dem Server.\n"
            "`/start` liest dein Semester aus deiner Serverrolle.\n"
            "In einer Privatnachricht gibt es diese Rolle nicht.\n"
            "Die Antworten sind ohnehin privat, niemand liest mit."
        ),
        LanguageCode.EN: (
            "Better use OSCAR on the server.\n"
            "`/start` reads your semester from your server role.\n"
            "In a private message that role does not exist.\n"
            "The answers are private anyway, nobody reads along."
        ),
    },
    "mobile": {
        LanguageCode.DE: (
            "Ja, alles funktioniert in der Discord-App.\n"
            "Das Bild des Regelstudienplans ist breit.\n"
            "Dreh das Handy quer oder tippe das Bild an, dann kannst du zoomen."
        ),
        LanguageCode.EN: (
            "Yes, everything works in the discord app.\n"
            "The picture of the standard study plan is wide.\n"
            "Turn the phone sideways or tap the picture to zoom."
        ),
    },
    "which_lms": {
        LanguageCode.DE: (
            "**Kursmaterial:** eLearning, das Moodle der Uni (elearning.ovgu.de). "
            "Login mit deinem OvGU-Account.\n"
            "**Prüfungen:** LSF (lsf.ovgu.de). Nur dort zählt eine Anmeldung.\n"
            "**Modulhandbuch:** BookStack (bookstack.cs.ovgu.de), ohne Login lesbar.\n"
            "**Code:** FIN GitLab (isggit3.cs.ovgu.de), Login mit FIN-Account.\n\n"
            "Alle vier öffnest du in `/help` unter „Öffnen\u201c → Lernplattformen."
        ),
        LanguageCode.EN: (
            "**Course material:** eLearning, the university Moodle "
            "(elearning.ovgu.de). Log in with your OvGU account.\n"
            "**Exams:** LSF (lsf.ovgu.de). A registration only counts there.\n"
            "**Module handbook:** BookStack (bookstack.cs.ovgu.de), no login needed.\n"
            "**Code:** FIN GitLab (isggit3.cs.ovgu.de), FIN account.\n\n"
            "Open all four in `/help` under \u201cOpen\u201d, Learning platforms."
        ),
    },
}


# The labels of the `/compare` table. The row keys match `compare_view.ROW_KEYS`, so a
# row cannot be added without a heading for it.
COMPARE_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "title": {
        LanguageCode.DE: "Modulvergleich",
        LanguageCode.EN: "Module comparison",
    },
    "credit_points": {
        LanguageCode.DE: "Creditpoints",
        LanguageCode.EN: "Credit points",
    },
    "sws": {
        LanguageCode.DE: "Lehrform und SWS",
        LanguageCode.EN: "Teaching form and SWS",
    },
    "language": {
        LanguageCode.DE: "Sprache",
        LanguageCode.EN: "Language",
    },
    "exam": {
        LanguageCode.DE: "Prüfung",
        LanguageCode.EN: "Exam",
    },
    "lecturer": {
        LanguageCode.DE: "Dozent/Dozentin",
        LanguageCode.EN: "Lecturer",
    },
    "differs": {
        LanguageCode.DE: "Unterschiede:",
        LanguageCode.EN: "They differ in:",
    },
    "identical": {
        LanguageCode.DE: "In diesen Punkten sind die Module gleich.",
        LanguageCode.EN: "The modules match on all of these points.",
    },
    "too_few": {
        LanguageCode.DE: "Nenne zwei verschiedene Module, sonst gibt es nichts zu vergleichen.",
        LanguageCode.EN: "Name two different modules, otherwise there is nothing to compare.",
    },
}


# Shown when somebody presses a button in a message that belongs to another student.
VIEW_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "not_your_view": {
        LanguageCode.DE: (
            "Diese Ansicht gehört jemand anderem. "
            "Rufe den Befehl selbst auf, dann bekommst du deine eigene."
        ),
        LanguageCode.EN: (
            "This view belongs to somebody else. "
            "Run the command yourself to get your own."
        ),
    },
}


# Everything `/my_data` says. The command shows a student what is stored about them and
# deletes it on request, so these strings have to name the data, not describe it vaguely.
MY_DATA_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "title": {
        LanguageCode.DE: "Deine Daten",
        LanguageCode.EN: "Your data",
    },
    "intro": {
        LanguageCode.DE: "Das ist alles, was OSCAR über dich gespeichert hat. Nur du siehst es.",
        LanguageCode.EN: "This is everything OSCAR has stored about you. Only you can see it.",
    },
    "nothing_stored": {
        LanguageCode.DE: (
            "Wir haben nichts über dich gespeichert. "
            "Du hast entweder noch nie `/start` genutzt, oder deine Daten sind schon gelöscht.\n"
            "Es gibt also nichts zum Herunterladen und nichts zum Löschen."
        ),
        LanguageCode.EN: (
            "We have nothing stored about you. "
            "You either never ran `/start`, or your data is already deleted.\n"
            "So there is nothing to download and nothing to delete."
        ),
    },
    "account_heading": {
        LanguageCode.DE: "**Konto**",
        LanguageCode.EN: "**Account**",
    },
    "discord_id": {
        LanguageCode.DE: "Discord ID",
        LanguageCode.EN: "Discord ID",
    },
    "stored_name": {
        LanguageCode.DE: "Name",
        LanguageCode.EN: "Name",
    },
    "preferences_heading": {
        LanguageCode.DE: "**Einstellungen**",
        LanguageCode.EN: "**Preferences**",
    },
    "no_preferences": {
        LanguageCode.DE: "Du hast noch keine Einstellungen gespeichert.",
        LanguageCode.EN: "You have not saved any preferences yet.",
    },
    "preference_language": {
        LanguageCode.DE: "Sprache",
        LanguageCode.EN: "Language",
    },
    "preference_semester": {
        LanguageCode.DE: "Fachsemester",
        LanguageCode.EN: "Semester",
    },
    "preference_major": {
        LanguageCode.DE: "Studiengang",
        LanguageCode.EN: "Programme",
    },
    "preference_spo": {
        LanguageCode.DE: "Prüfungsordnung",
        LanguageCode.EN: "Examination regulations",
    },
    "preference_start": {
        LanguageCode.DE: "Studienbeginn",
        LanguageCode.EN: "Start of studies",
    },
    "winter_start": {
        LanguageCode.DE: "Wintersemester",
        LanguageCode.EN: "winter semester",
    },
    "summer_start": {
        LanguageCode.DE: "Sommersemester",
        LanguageCode.EN: "summer semester",
    },
    "not_stored": {
        LanguageCode.DE: "nicht gespeichert",
        LanguageCode.EN: "not stored",
    },
    "plan_heading": {
        LanguageCode.DE: "**Semesterplan ({count} Module)**",
        LanguageCode.EN: "**Semester plan ({count} modules)**",
    },
    "no_plan": {
        LanguageCode.DE: "Du hast dir noch kein Modul gemerkt.",
        LanguageCode.EN: "You have not saved a single module yet.",
    },
    "more_modules": {
        LanguageCode.DE: "… und {count} weitere. Die Datei enthält alle.",
        LanguageCode.EN: "… and {count} more. The file holds all of them.",
    },
    "unknown_module": {
        LanguageCode.DE: "Modul ohne Titel",
        LanguageCode.EN: "module without a title",
    },
    "feedback_heading": {
        LanguageCode.DE: "**Feedback ({count} Einträge)**",
        LanguageCode.EN: "**Feedback ({count} entries)**",
    },
    "no_feedback": {
        LanguageCode.DE: "Du hast uns noch kein Feedback geschickt.",
        LanguageCode.EN: "You have not sent us any feedback yet.",
    },
    "feedback_entry": {
        LanguageCode.DE: (
            "{date}: Intuitivität {intuitiveness}, "
            "Auffindbarkeit {discoverability}, Nutzen {usefulness}"
        ),
        LanguageCode.EN: (
            "{date}: intuitiveness {intuitiveness}, "
            "discoverability {discoverability}, usefulness {usefulness}"
        ),
    },
    "feedback_texts_note": {
        LanguageCode.DE: "-# Deine Freitexte stehen vollständig in der Datei.",
        LanguageCode.EN: "-# Your free text answers are in the file, in full.",
    },
    "download_button": {
        LanguageCode.DE: "⤓ Als JSON herunterladen",
        LanguageCode.EN: "⤓ Download as JSON",
    },
    "download_ready": {
        LanguageCode.DE: "Hier ist alles, was wir über dich gespeichert haben.",
        LanguageCode.EN: "Here is everything we have stored about you.",
    },
    "delete_button": {
        LanguageCode.DE: "Alles löschen",
        LanguageCode.EN: "Delete everything",
    },
    "confirm_title": {
        LanguageCode.DE: "Wirklich alles löschen?",
        LanguageCode.EN: "Really delete everything?",
    },
    "confirm_text": {
        LanguageCode.DE: (
            "Das löscht sofort und für immer:\n"
            "• deine Einstellungen: Sprache, Fachsemester, Studiengang, "
            "Prüfungsordnung und Studienbeginn\n"
            "• deinen Semesterplan mit {modules} gemerkten Modulen\n"
            "• deine {feedback} Feedback Einträge, samt Bewertungen und Freitexten\n"
            "• deine Discord ID, damit nichts mehr auf dich zeigt\n\n"
            "Es gibt kein Zurück. Lade deine Daten vorher herunter, wenn du sie behalten willst."
        ),
        LanguageCode.EN: (
            "This deletes, right now and for good:\n"
            "• your preferences: language, semester, programme, "
            "examination regulations and start of studies\n"
            "• your semester plan with {modules} saved modules\n"
            "• your {feedback} feedback entries, ratings and free text alike\n"
            "• your discord id, so nothing points at you any more\n\n"
            "There is no undo. Download your data first if you want to keep it."
        ),
    },
    "confirm_yes": {
        LanguageCode.DE: "Ja, alles löschen",
        LanguageCode.EN: "Yes, delete everything",
    },
    "confirm_no": {
        LanguageCode.DE: "Abbrechen",
        LanguageCode.EN: "Cancel",
    },
    "deleted": {
        LanguageCode.DE: (
            "Deine Daten sind gelöscht. Wir speichern nichts mehr über dich.\n"
            "Mit `/start` kannst du jederzeit neu anfangen."
        ),
        LanguageCode.EN: (
            "Your data is deleted. We store nothing about you any more.\n"
            "Run `/start` whenever you want to begin again."
        ),
    },
    "cancelled": {
        LanguageCode.DE: "Abgebrochen. Es wurde nichts gelöscht.",
        LanguageCode.EN: "Cancelled. Nothing was deleted.",
    },
}


INFO_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "responsibility":{
        LanguageCode.DE: "Verantwortung",
        LanguageCode.EN: "Responsibility"
    },
    "lecturer":{
        LanguageCode.DE: "Dozent/Dozentin",
        LanguageCode.EN: "Lecturer"
    },
    "course":{
        LanguageCode.DE: "Lehrveranstaltung",
        LanguageCode.EN: "Course"
    },
    "abbreviation":{
        LanguageCode.DE: "Kürzel",
        LanguageCode.EN: "Abbreviation"
    },
    "semester":{
        LanguageCode.DE: "Fachsemester",
        LanguageCode.EN: "Semester"
    },
    "duration":{
        LanguageCode.DE: "Dauer",
        LanguageCode.EN: "Duration"
    },
    "language":{
        LanguageCode.DE: "Sprache",
        LanguageCode.EN: "Language"
    },
    "level":{
        LanguageCode.DE: "Niveau",
        LanguageCode.EN: "Level"
    },"content":{
        LanguageCode.DE: "Inhalt",
        LanguageCode.EN: "Content"
    },
    "ilo":{
        LanguageCode.DE: "Angestrebte Lernergebnisse",
        LanguageCode.EN: "Intended learning outcomes"
    },
    "effort":{
        LanguageCode.DE: "Arbeitsaufwand",
        LanguageCode.EN: "Effort"
    },
    "module_number":{
        LanguageCode.DE: "Modulnummer",
        LanguageCode.EN: "Module number"
    },
}


# Every visible string of `/filter`, the mask as well as the result list. The option
# keys match the ones in `util.filter_options`, so a button cannot be added without a
# label in both languages. The buttons carry those keys as their value, so a click means
# the same thing no matter which language rendered it.
FILTER_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "title": {
        LanguageCode.DE: "Modulsuche",
        LanguageCode.EN: "Module search",
    },
    "hint": {
        LanguageCode.DE: (
            "Klicke an, was auf dich zutrifft. "
            "Mehrere Knöpfe in einer Zeile gelten als oder, "
            "verschiedene Zeilen gelten als und."
        ),
        LanguageCode.EN: (
            "Click whatever applies to you. "
            "Several buttons in one row count as an or, "
            "different rows count as an and."
        ),
    },
    "search": {
        LanguageCode.DE: "Suchen",
        LanguageCode.EN: "Search",
    },
    "heading_cp": {
        LanguageCode.DE: "Creditpoints",
        LanguageCode.EN: "Credit points",
    },
    "heading_sws": {
        LanguageCode.DE: "SWS",
        LanguageCode.EN: "SWS",
    },
    "heading_exam": {
        LanguageCode.DE: "Prüfungsformat",
        LanguageCode.EN: "Exam format",
    },
    "heading_position": {
        LanguageCode.DE: "Modulzeitraum",
        LanguageCode.EN: "Semester position",
    },
    "heading_category": {
        LanguageCode.DE: "Inhaltliche Interessen",
        LanguageCode.EN: "Topics of interest",
    },
    "cp_lt_5": {
        LanguageCode.DE: "< 5 CP",
        LanguageCode.EN: "< 5 CP",
    },
    "cp_eq_5": {
        LanguageCode.DE: "5 CP",
        LanguageCode.EN: "5 CP",
    },
    "cp_gt_5": {
        LanguageCode.DE: "> 5 CP",
        LanguageCode.EN: "> 5 CP",
    },
    "sws_lt_3": {
        LanguageCode.DE: "< 3",
        LanguageCode.EN: "< 3",
    },
    "sws_eq_3": {
        LanguageCode.DE: "3",
        LanguageCode.EN: "3",
    },
    "sws_gt_3": {
        LanguageCode.DE: "> 3",
        LanguageCode.EN: "> 3",
    },
    "exam_written": {
        LanguageCode.DE: "Klausur",
        LanguageCode.EN: "Written exam",
    },
    "exam_oral": {
        LanguageCode.DE: "Mündlich",
        LanguageCode.EN: "Oral exam",
    },
    "position_summer": {
        LanguageCode.DE: "Sommer",
        LanguageCode.EN: "Summer",
    },
    "position_winter": {
        LanguageCode.DE: "Winter",
        LanguageCode.EN: "Winter",
    },
    "position_every": {
        LanguageCode.DE: "Jedes Semester",
        LanguageCode.EN: "Every semester",
    },
    "interest_ai": {
        LanguageCode.DE: "KI",
        LanguageCode.EN: "AI",
    },
    "interest_games": {
        LanguageCode.DE: "Computerspiele",
        LanguageCode.EN: "Computer games",
    },
    "interest_systems": {
        LanguageCode.DE: "Systementwicklung",
        LanguageCode.EN: "Systems engineering",
    },
    "interest_scientific": {
        LanguageCode.DE: "Wissenschaftliches Rechnen",
        LanguageCode.EN: "Scientific computing",
    },
    # The result list. `page_header` is formatted with `page` and `pages`.
    "page_header": {
        LanguageCode.DE: "Module (Seite {page}/{pages})",
        LanguageCode.EN: "Modules (page {page}/{pages})",
    },
    "more_info": {
        LanguageCode.DE: "Mehr Infos",
        LanguageCode.EN: "More info",
    },
    "no_results": {
        LanguageCode.DE: "Kein Modul passt zu dieser Auswahl. Nimm ein Kriterium heraus.",
        LanguageCode.EN: "No module matches this selection. Take one criterion out.",
    },
    "sort_cp_asc": {
        LanguageCode.DE: "CP ↑",
        LanguageCode.EN: "CP ↑",
    },
    "sort_cp_desc": {
        LanguageCode.DE: "CP ↓",
        LanguageCode.EN: "CP ↓",
    },
    "sort_title_asc": {
        LanguageCode.DE: "Titel A-Z",
        LanguageCode.EN: "Title A-Z",
    },
    "sort_title_desc": {
        LanguageCode.DE: "Titel Z-A",
        LanguageCode.EN: "Title Z-A",
    },
}


FEEDBACK_REVIEW: dict[str, dict[LanguageCode, str]] = {
    "review_feedback": {
        LanguageCode.DE: "Feedback überprüfen",
        LanguageCode.EN: "Review Feedback",
    },
    "zoom": {
        LanguageCode.DE: "Zoom:",
        LanguageCode.EN: "Zoom:",
    },
    "intuitiveness": {
        LanguageCode.DE: "Intuitivität",
        LanguageCode.EN: "Intuitiveness",
    },
    "discoverability": {
        LanguageCode.DE: "Auffindbarkeit",
        LanguageCode.EN: "Discoverability",
    },
    "usefulness": {
        LanguageCode.DE: "Nützlichkeit",
        LanguageCode.EN: "Usefulness",
    },
    "houre_suffix": {
        LanguageCode.DE: "h",
        LanguageCode.EN: "h"
    },
    "day_suffix": {
        LanguageCode.DE: "T",
        LanguageCode.EN: "d"
    },
    "week_suffix": {
        LanguageCode.DE: "W",
        LanguageCode.EN: "w"
    },
    "month_suffix": {
        LanguageCode.DE: "M",
        LanguageCode.EN: "mo"
    },
    "year_suffix": {
        LanguageCode.DE: "J",
        LanguageCode.EN: "y"
    },
    "all_time": {
        LanguageCode.DE: "Max",
        LanguageCode.EN: "max"
    },
    "rating": {
        LanguageCode.DE: "Bewertung",
        LanguageCode.EN: "Rating",
    },
    "metrics_overview": {
        LanguageCode.DE: "Metriken Übersicht",
        LanguageCode.EN: "Metrics Overview",
    },
    "responses": {
        LanguageCode.DE: "Antworten",
        LanguageCode.EN: "responses",
    },
    "timeline": {
        LanguageCode.DE: "Zeitachse",
        LanguageCode.EN: "Timeline",
    },
    "data_download": {
        LanguageCode.DE: "Daten herunterladen",
        LanguageCode.EN: "Download Data",
    },
    "finished_download": {
        LanguageCode.DE: "Dein Feedback-Daten-Download ist fertig!",
        LanguageCode.EN: "Your feedback data download is ready!",
    },
}



def format_duration(seconds: int|None, language_code: LanguageCode = LanguageCode.EN) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return FEEDBACK_REVIEW["all_time"][language_code]
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours}{FEEDBACK_REVIEW['houre_suffix'][language_code]}"
    if seconds < 604800:
        days = seconds // 86400
        return f"{days}{FEEDBACK_REVIEW['day_suffix'][language_code]}"
    if seconds < 2629743:
        weeks = seconds // 604800
        return f"{weeks}{FEEDBACK_REVIEW['week_suffix'][language_code]}"
    if seconds < 31556926:
        months = seconds // 2629743
        return f"{months}{FEEDBACK_REVIEW['month_suffix'][language_code]}"
    years = seconds // 31556926
    return f"{years}{FEEDBACK_REVIEW['year_suffix'][language_code]}"



FEEDBACK_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "welcome_text":{
        LanguageCode.DE: """Vielen Dank, dass du dich dazu entschlossen hast uns Feedback zu geben.
Im Folgenden findest du einige Fragen, bitte wähle das zutreffendste aus.
In den Textfeldern kanst du uns mitteilen, was dir noch auf dem Herze liegt.
Damit hilfst du uns sehr weiter :)""",
        LanguageCode.EN: """Thanks, that you have decided to give us feedback.
In the following you'll find some questions, please select the most fitting one.
You can tell us what your further toughts are in the textfiels below.
This will help is immense :)"""
    },
    "choose_1":{
        LanguageCode.DE:"trifft voll zu",
        LanguageCode.EN:"totally applies"
    },
    "choose_2":{
        LanguageCode.DE:"trifft eher zu",
        LanguageCode.EN:"more likely to apply"
    },
    "choose_3":{
        LanguageCode.DE:"trifft eher nicht zu",
        LanguageCode.EN:"doesn't really apply"
    },
    "choose_4":{
        LanguageCode.DE:"trifft nicht zu",
        LanguageCode.EN:"doesn't apply"
    },
    "improve":{
        LanguageCode.DE: "Was kann verbessert werden?",
        LanguageCode.EN: "What could be improved?"
    },
    "wish":{
        LanguageCode.DE: "Was wünschst du dir noch?",
        LanguageCode.EN: "What is something you wish for?"
    },
    "bug":{
        LanguageCode.DE: "Hast du einen Bug gefunden?",
        LanguageCode.EN: "Did you find a bug?"
    }

}

# The wording `/standard_plan` uses to mark the plan against the saved modules.
#
# OSCAR stores no grades, so none of these sentences may claim that a module was
# passed. They all speak about the plan, and the note says so once more in full.
PLAN_PROGRESS_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "legend": {
        LanguageCode.DE: "✅ steht in deinem Plan · ⬜ fehlt noch",
        LanguageCode.EN: "✅ is in your plan · ⬜ is still missing",
    },
    "no_grades": {
        LanguageCode.DE: (
            "OSCAR kennt deine Noten nicht. "
            "Ein Haken heißt: Du hast das Modul eingeplant, nicht bestanden."
        ),
        LanguageCode.EN: (
            "OSCAR does not know your grades. "
            "A tick means you planned the module, not that you passed it."
        ),
    },
    "summary": {
        LanguageCode.DE: "Eingeplant: {planned} von {total} CP",
        LanguageCode.EN: "Planned: {planned} of {total} CP",
    },
    "semester_marked": {
        LanguageCode.DE: "{number}. Semester ({planned}/{total} CP eingeplant)",
        LanguageCode.EN: "Semester {number} ({planned}/{total} CP planned)",
    },
    "semester_plain": {
        LanguageCode.DE: "{number}. Semester ({total} CP)",
        LanguageCode.EN: "Semester {number} ({total} CP)",
    },
    "nothing_saved": {
        LanguageCode.DE: (
            "Du hast noch keine Module gespeichert. "
            "Speichere sie mit `/module`, dann markiert dir `/standard_plan`, "
            "was du schon eingeplant hast."
        ),
        LanguageCode.EN: (
            "You saved no modules yet. "
            "Save them with `/module`, then `/standard_plan` marks what you "
            "have planned already."
        ),
    },
}


MODULE_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "added_to_plan": {
        LanguageCode.DE: "{title} wurde zu deiner Semesterübersicht hinzugefügt.",
        LanguageCode.EN: "{title} was added to your semester overview.",
    },
    "not_found": {
        LanguageCode.DE: (
            "Ich habe kein Modul mit dem Namen **{name}** gefunden. "
            "Wähle bitte einen Vorschlag aus der Liste."
        ),
        LanguageCode.EN: (
            "I found no module called **{name}**. "
            "Please pick a suggestion from the list."
        ),
    },
    "kuerzel":{
        LanguageCode.DE: "Kürzel: ",
        LanguageCode.EN: "Abbreviation: "
    },
    "sprache":{
        LanguageCode.DE: "Sprache: ",
        LanguageCode.EN: "Language: "
    },
    "dozent":{
        LanguageCode.DE: "Dozent: ",
        LanguageCode.EN: "Lecturer: "
    }
}

MODULE_FILTER_CATEGORIES_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "AI": {
        LanguageCode.DE:"KI",
        LanguageCode.EN:"AI"
    },
    "ComputerGame": {
        LanguageCode.DE:"Computer Spiele",
        LanguageCode.EN:"Computer Game"
    },
    "SystemsEngineering": {
        LanguageCode.DE:"Systems Entwicklung",
        LanguageCode.EN:"Systems Engineering"
    },
    "ScientificComputing": {
        LanguageCode.DE:"Wissenschaftliches Rechnen",
        LanguageCode.EN:"Scientific Computing"
    },
}


PO_REGULATIONS = {
    PO.PO_2023: {
        LanguageCode.EN: "Examination Regulations 2023",
        LanguageCode.DE: "Prüfungsordnung 2023"
    },
    PO.PO_2024: {
        LanguageCode.EN: "Examination Regulations 2024",
        LanguageCode.DE: "Prüfungsordnung 2024"
    },
    PO.PO_2020: {
        LanguageCode.EN: "Examination Regulations 2020",
        LanguageCode.DE: "Prüfungsordnung 2020"
    },
    PO.PO_2021: {
        LanguageCode.EN: "Examination Regulations 2021",
        LanguageCode.DE: "Prüfungsordnung 2021"
    },
    PO.PO_2015: {
        LanguageCode.EN: "Examination Regulations 2015",
        LanguageCode.DE: "Prüfungsordnung 2015"
    },
    PO.PO_2016: {
        LanguageCode.EN: "Examination Regulations 2016",
        LanguageCode.DE: "Prüfungsordnung 2016"
    },
    PO.PO_2017: {
        LanguageCode.EN: "Examination Regulations 2017",
        LanguageCode.DE: "Prüfungsordnung 2017"
    }
}

RATING_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "rate_title": {
        LanguageCode.DE: "Modul bewerten",
        LanguageCode.EN: "Rate Module",
    },
    "score_label": {
        LanguageCode.DE: "Bewertung (1-5 Sterne)",
        LanguageCode.EN: "Rating (1-5 stars)",
    },
    "difficulty_label": {
        LanguageCode.DE: "Schwierigkeit (1-5: 1=leicht, 5=schwer)",
        LanguageCode.EN: "Difficulty (1-5: 1=easy, 5=hard)",
    },
    "comment_label": {
        LanguageCode.DE: "Erfahrungsbericht / Tipps (optional)",
        LanguageCode.EN: "Review / Tips (optional)",
    },
    "invalid_input": {
        LanguageCode.DE: (
            "Bitte gib für Bewertung und Schwierigkeit eine ganze Zahl von 1 bis 5 ein."
        ),
        LanguageCode.EN: (
            "Please enter a whole number from 1 to 5 for rating and difficulty."
        ),
    },
    "rate_success": {
        LanguageCode.DE: (
            "Vielen Dank für deine Bewertung von **{title}**!\n"
            "⭐ Bewertung: {rating}/5 | 🏋️ Schwierigkeit: {difficulty}/5"
        ),
        LanguageCode.EN: (
            "Thank you for rating **{title}**!\n"
            "⭐ Rating: {rating}/5 | 🏋️ Difficulty: {difficulty}/5"
        ),
    },
    "ratings_count_one": {
        LanguageCode.DE: "Bewertung",
        LanguageCode.EN: "rating",
    },
    "ratings_count": {
        LanguageCode.DE: "Bewertungen",
        LanguageCode.EN: "ratings",
    },
    "no_ratings": {
        LanguageCode.DE: "Noch keine Bewertungen",
        LanguageCode.EN: "No ratings yet",
    },
    "difficulty": {
        LanguageCode.DE: "Schwierigkeit",
        LanguageCode.EN: "Difficulty",
    },
    # Reading the reviews, not writing one. The comments were stored from the start
    # and shown nowhere, so a student wrote a tip that nobody could ever read.
    "reviews_button": {
        LanguageCode.DE: "💬 Erfahrungen",
        LanguageCode.EN: "💬 Reviews",
    },
    "reviews_title": {
        LanguageCode.DE: "# Erfahrungen zu {title}",
        LanguageCode.EN: "# Reviews of {title}",
    },
    "reviews_summary": {
        LanguageCode.DE: "⭐ {rating}/5 · 🏋️ Schwierigkeit {difficulty}/5 · {count} {label}",
        LanguageCode.EN: "⭐ {rating}/5 · 🏋️ difficulty {difficulty}/5 · {count} {label}",
    },
    "no_reviews": {
        LanguageCode.DE: (
            "Noch hat niemand einen Erfahrungsbericht geschrieben.\n"
            "Schreib den ersten mit **⭐ Bewerten**. Das Kommentarfeld ist optional, "
            "aber es ist das, was anderen wirklich hilft."
        ),
        LanguageCode.EN: (
            "Nobody has written a review yet.\n"
            "Write the first with **⭐ Rate**. The comment field is optional, but it "
            "is the part that actually helps the next student."
        ),
    },
    "reviews_anonymous": {
        LanguageCode.DE: "Anonym",
        LanguageCode.EN: "Anonymous",
    },
    "reviews_privacy": {
        LanguageCode.DE: (
            "Erfahrungsberichte werden ohne Namen gezeigt. Deinen eigenen löschst du "
            "mit `/my_data`."
        ),
        LanguageCode.EN: (
            "Reviews are shown without a name. Delete your own with `/my_data`."
        ),
    },
    "latest_review": {
        LanguageCode.DE: "💬 „{comment}“",
        LanguageCode.EN: "💬 “{comment}”",
    },
    "more_reviews": {
        LanguageCode.DE: "… und {count} weitere",
        LanguageCode.EN: "… and {count} more",
    },
}

EXAM_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "exam_title": {
        LanguageCode.DE: "Altklausuren an der OVGU",
        LanguageCode.EN: "Past exams at the OVGU",
    },
    "exam_desc": {
        LanguageCode.DE: (
            "Die Fachschaftsräte sammeln alte Klausuren und Gedächtnisprotokolle. "
            "Jede Fakultät führt ihr eigenes Archiv, darum steht hier mehr als "
            "eines.\n\n"
            "OSCAR speichert keine Klausur selbst. Das Urheberrecht liegt beim "
            "Lehrstuhl, nicht bei dir."
        ),
        LanguageCode.EN: (
            "The student councils collect past exams and written recollections of "
            "oral exams. Each faculty runs its own archive, so there is more than "
            "one here.\n\n"
            "OSCAR stores no exam itself. The copyright sits with the chair, "
            "not with you."
        ),
    },
    "exam_hint": {
        LanguageCode.DE: (
            "💡 Du hast gerade eine Klausur geschrieben? Schick dem Fachschaftsrat "
            "ein Gedächtnisprotokoll. Davon lebt das Archiv."
        ),
        LanguageCode.EN: (
            "💡 Just sat an exam? Send your student council a written recollection. "
            "The archive lives on them."
        ),
    },
    "exam_button": {
        LanguageCode.DE: "📚 Altklausuren",
        LanguageCode.EN: "📚 Past exams",
    },
}

# `/here` names the module a channel is about, without anybody typing a title.
HERE_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "here_no_channel": {
        LanguageCode.DE: (
            "`/here` liest den Kanalnamen. Eine Direktnachricht hat keinen, "
            "nutze dort `/module <name>`."
        ),
        LanguageCode.EN: (
            "`/here` reads the channel name. A direct message has none, "
            "so use `/module <name>` there."
        ),
    },
    "here_not_found": {
        LanguageCode.DE: (
            "Zu **#{channel}** finde ich kein Modul im Handbuch.\n"
            "Nutze `/module <name>`, wenn du weißt, wie das Modul heißt."
        ),
        LanguageCode.EN: (
            "I find no module for **#{channel}** in the handbook.\n"
            "Use `/module <name>` if you know what the module is called."
        ),
    },
    "here_pick_title": {
        LanguageCode.DE: "# Welches Modul meinst du?",
        LanguageCode.EN: "# Which module do you mean?",
    },
    "here_pick_desc": {
        LanguageCode.DE: "**#{channel}** passt auf mehrere Module. Wähle eines aus.",
        LanguageCode.EN: "**#{channel}** fits more than one module. Pick one.",
    },
    "here_placeholder": {
        LanguageCode.DE: "Modul wählen",
        LanguageCode.EN: "Choose a module",
    },
}

COHORT_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "cohort_title": {
        LanguageCode.DE: "# 👥 Anonymisierte Kohorten-Statistik",
        LanguageCode.EN: "# 👥 Anonymous Cohort Statistics",
    },
    "cohort_desc": {
        LanguageCode.DE: (
            "Vergleich deines Studienverlaufs mit aggregierten Daten deiner Kohorte "
            "(Studierende im selben Studiengang & Fachsemester)."
        ),
        LanguageCode.EN: (
            "Compare your study progress against aggregated data from your cohort "
            "(students in the same major & academic semester)."
        ),
    },
    "insufficient_data": {
        LanguageCode.DE: (
            "🔒 **Datenschutzhinweis (k-Anonymität):**\n"
            "In dieser Kohorte ({major}, {semester}. Semester) sind aktuell nur "
            "**{count} von mindestens {min_size}** Studierenden registriert.\n\n"
            "Zum Schutz deiner Privatsphäre werden Detailstatistiken und Modullisten "
            "erst ab einer Gruppengröße von mindestens {min_size} Studierenden aggregiert, "
            "um Rückschlüsse auf Einzelpersonen zuverlässig auszuschließen."
        ),
        LanguageCode.EN: (
            "🔒 **Privacy Notice (k-anonymity):**\n"
            "This cohort ({major}, Semester {semester}) currently only has "
            "**{count} of minimum {min_size}** registered students.\n\n"
            "To safeguard individual privacy, detailed metrics and module breakdowns "
            "are only displayed once a cohort reaches at least {min_size} students, "
            "preventing individual student fingerprinting."
        ),
    },
    "metrics_header": {
        LanguageCode.DE: "📊 **Kohorten-Kennzahlen ({count} Studierende):**",
        LanguageCode.EN: "📊 **Cohort Metrics ({count} students):**",
    },
    "avg_modules": {
        LanguageCode.DE: "Ø Geplante Module pro Person",
        LanguageCode.EN: "Avg. planned modules per student",
    },
    "avg_cp": {
        LanguageCode.DE: "Ø Geplante Leistung",
        LanguageCode.EN: "Avg. planned workload",
    },
    "top_modules_header": {
        LanguageCode.DE: "🔥 **Häufigst geplante Module in deiner Kohorte:**",
        LanguageCode.EN: "🔥 **Most frequently planned modules in your cohort:**",
    },
    "no_modules_planned": {
        LanguageCode.DE: "*In dieser Kohorte hat noch niemand Module im Semesterplan gespeichert.*",
        LanguageCode.EN: "*No modules have been added to semester plans in this cohort yet.*",
    },
    "faculty_header": {
        LanguageCode.DE: "🏛️ **Fakultätsweite Verteilung ({total} Studierende):**",
        LanguageCode.EN: "🏛️ **Faculty-wide Distribution ({total} students):**",
    },
    "btn_cohort": {
        LanguageCode.DE: "👥 Kohortenvergleich",
        LanguageCode.EN: "👥 Cohort Stats",
    },
    "btn_progress": {
        LanguageCode.DE: "🏆 Mein Fortschritt",
        LanguageCode.EN: "🏆 My Progress",
    },
}


CODE_GOLF_TEXTS: dict[str, dict[LanguageCode, str]] = {
    "golf_title": {
        LanguageCode.DE: "⛳ Wöchentliche Code-Golf-Challenge",
        LanguageCode.EN: "⛳ Weekly Code Golf Challenge",
    },
    "active_week": {
        LanguageCode.DE: "Aktive Woche (KW {week}): **#{number} — {title}**",
        LanguageCode.EN: "Active Week (Week {week}): **#{number} — {title}**",
    },
    "archive_header": {
        LanguageCode.DE: "📚 Challenge-Auswahl:",
        LanguageCode.EN: "📚 Challenge Selector:",
    },
    "btn_submit": {
        LanguageCode.DE: "⛳ Lösung einreichen",
        LanguageCode.EN: "⛳ Submit Solution",
    },
    "btn_leaderboard": {
        LanguageCode.DE: "🏆 Rangliste",
        LanguageCode.EN: "🏆 Leaderboard",
    },
    "btn_details": {
        LanguageCode.DE: "📖 Aufgabenstellung",
        LanguageCode.EN: "📖 Problem Details",
    },
    "btn_my_submission": {
        LanguageCode.DE: "📜 Meine Lösung",
        LanguageCode.EN: "📜 My Submission",
    },
    "leaderboard_title": {
        LanguageCode.DE: "🏆 **Rangliste für #{number}: {title}**",
        LanguageCode.EN: "🏆 **Leaderboard for #{number}: {title}**",
    },
    "leaderboard_empty": {
        LanguageCode.DE: "*Noch keine Einreichungen für diese Challenge. Sei die/der Erste!*",
        LanguageCode.EN: "*No submissions for this challenge yet. Be the first!*",
    },
    "leaderboard_entry": {
        LanguageCode.DE: "{rank}. **{name}** — `{length} Bytes` ({language})",
        LanguageCode.EN: "{rank}. **{name}** — `{length} Bytes` ({language})",
    },
    "modal_title": {
        LanguageCode.DE: "Code-Golf #{number}",
        LanguageCode.EN: "Code Golf #{number}",
    },
    "modal_lang_label": {
        LanguageCode.DE: "Programmiersprache",
        LanguageCode.EN: "Programming Language",
    },
    "modal_lang_placeholder": {
        LanguageCode.DE: "z.B. Python, C, Rust, JS, Haskell...",
        LanguageCode.EN: "e.g. Python, C, Rust, JS, Haskell...",
    },
    "modal_code_label": {
        LanguageCode.DE: "Quellcode (Code Golf)",
        LanguageCode.EN: "Source Code (Code Golf)",
    },
    "modal_code_placeholder": {
        LanguageCode.DE: "Füge hier deinen kürzesten Code ein...",
        LanguageCode.EN: "Paste your shortest code here...",
    },
    "submit_new_best": {
        LanguageCode.DE: "🎉 **Lösung erfasst!**\nLänge: **{length} Bytes** ({language}).",
        LanguageCode.EN: "🎉 **Solution recorded!**\nLength: **{length} Bytes** ({language}).",
    },
    "submit_improved": {
        LanguageCode.DE: (
            "🎉 **Neue Bestleistung!**\n"
            "Verbesserte Länge: **{new_len} Bytes** (vorher {prev_len} Bytes in {language})."
        ),
        LanguageCode.EN: (
            "🎉 **New personal best!**\n"
            "Improved length: **{new_len} Bytes** (previously {prev_len} Bytes in {language})."
        ),
    },
    "submit_worse": {
        LanguageCode.DE: (
            "ℹ️ Deine Lösung ({new_len} Bytes) ist nicht kürzer als dein bisheriger "
            "Rekord (**{prev_len} Bytes**). Dein bester Stand bleibt gespeichert."
        ),
        LanguageCode.EN: (
            "ℹ️ Your solution ({new_len} Bytes) is not shorter than your current best "
            "(**{prev_len} Bytes**). Your best score is kept."
        ),
    },
    "no_submission_yet": {
        LanguageCode.DE: "Du hast für Challenge #{number} noch keine Lösung eingereicht.",
        LanguageCode.EN: "You haven't submitted a solution for Challenge #{number} yet.",
    },
    "my_submission_info": {
        LanguageCode.DE: (
            "📜 **Deine Einreichung für #{number} ({title}):**\n"
            "• Sprache: `{language}`\n"
            "• Länge: `{length} Bytes`\n\n"
            "```\n{code}\n```"
        ),
        LanguageCode.EN: (
            "📜 **Your submission for #{number} ({title}):**\n"
            "• Language: `{language}`\n"
            "• Length: `{length} Bytes`\n\n"
            "```\n{code}\n```"
        ),
    },
    "input_label": {
        LanguageCode.DE: "**Eingabe:**",
        LanguageCode.EN: "**Input:**",
    },
    "output_label": {
        LanguageCode.DE: "**Ausgabe:**",
        LanguageCode.EN: "**Output:**",
    },
    "example_input_label": {
        LanguageCode.DE: "**Beispiel-Eingabe:**",
        LanguageCode.EN: "**Example Input:**",
    },
    "example_output_label": {
        LanguageCode.DE: "**Beispiel-Ausgabe:**",
        LanguageCode.EN: "**Example Output:**",
    },
    "rules_note": {
        LanguageCode.DE: (
            "📏 *Gemessen wird die UTF-8 Byte-Länge (ohne umschließende Markdown-Backticks). "
            "Arbitrary Code Execution ist deaktiviert — Bewertung basiert auf Byte-Länge.*"
        ),
        LanguageCode.EN: (
            "📏 *Measured in UTF-8 byte length (excluding outer markdown code blocks). "
            "Arbitrary code execution is disabled — ranking is based on byte length.*"
        ),
    },
}

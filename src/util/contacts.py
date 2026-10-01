""" This module holds structured contact information for students at FIN OVGU.

    Covers official university and faculty contact points such as the Dean of Studies,
    Examination Office, Student Council (FaRaFIN), Programme Directors, Germany Scholarship
    (Deutschlandstipendium), Internship Office, Erasmus, and Counseling Services.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContactPerson:
    """Represents a single contact person or office."""
    title_de: str
    title_en: str
    office: str
    email: str
    url: str
    details_de: str
    details_en: str


@dataclass(frozen=True)
class ContactCategory:
    """Represents a category of contacts with an emoji, title, and persons."""
    key: str
    emoji: str
    title_de: str
    title_en: str
    description_de: str
    description_en: str
    contacts: tuple[ContactPerson, ...]


CONTACT_CATEGORIES: tuple[ContactCategory, ...] = (
    ContactCategory(
        key="dekanat_pa",
        emoji="🏛️",
        title_de="Studiendekanat & Prüfungsamt",
        title_en="Dean of Studies & Examination Office",
        description_de=(
            "Zuständig für Studienorganisation, Prüfungsordnungen, Notenverbuchung und Atteste."
        ),
        description_en=(
            "Responsible for study organization, exam regulations, grades, and certificates."
        ),
        contacts=(
            ContactPerson(
                title_de="Prüfungsamt FIN (PA)",
                title_en="Examination Office FIN",
                office="Gebäude 40, Raum 209 (oder G29)",
                email="pa-fin@ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Pr%C3%BCfungsamt.html",
                details_de=(
                    "Anlaufstelle für Notenverbuchung, Prüfungsanmeldungen, Krankmeldungen "
                    "(Atteste), Anerkennungen und Abschlussarbeiten. Wichtig: "
                    "Prüfungsabmeldung ist bis 3 Tage vor der Klausur ohne Grund möglich."
                ),
                details_en=(
                    "Contact for grade records, exam registrations, sick notes, credit "
                    "transfers, and theses. Note: Exam deregistration is possible up to 3 days "
                    "prior to the exam without giving reasons."
                ),
            ),
            ContactPerson(
                title_de="Studiendekanat FIN",
                title_en="Dean of Studies Office FIN",
                office="Gebäude 29 (FIN), Raum 102/103",
                email="studiendekanat@cs.ovgu.de",
                url="https://www.inf.ovgu.de/Fakult%C3%A4t/Studiendekanat.html",
                details_de=(
                    "Zuständig für Studien- und Prüfungsordnungen (SPO), Lehrangebot, "
                    "Modulhandbücher (BookStack) und Qualität der Lehre."
                ),
                details_en=(
                    "Responsible for examination regulations (SPO), course planning, "
                    "module handbooks (BookStack), and teaching quality."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="farafin",
        emoji="🦊",
        title_de="Fachschaftsrat (FaRaFIN)",
        title_en="Student Council (FaRaFIN)",
        description_de="Studentische Selbstverwaltung – von Studierenden für Studierende.",
        description_en="Student self-government of the faculty – by students for students.",
        contacts=(
            ContactPerson(
                title_de="Fachschaftsrat Informatik (FaRaFIN)",
                title_en="Computer Science Student Council (FaRaFIN)",
                office="Gebäude 29 (FIN), Raum 019 (Erdgeschoss)",
                email="farafin@ovgu.de",
                url="https://farafin.de",
                details_de=(
                    "Erste Anlaufstelle bei allen Fragen rund ums Studium, Probleme mit "
                    "Modulen oder Dozierenden, Altklausuren, Erstsemestertage (EET) und Events. "
                    "Sprechzeiten in der Vorlesungszeit fast täglich!"
                ),
                details_en=(
                    "Your primary contact for study questions, feedback on modules or "
                    "lecturers, past exam archives, orientation days (EET), and events. "
                    "Office hours almost daily during lecture periods!"
                ),
            ),
            ContactPerson(
                title_de="E-Wochen & Erstsemester-Portal (FaRaFIN EET)",
                title_en="Freshman Orientation Weeks (FaRaFIN EET)",
                office="Gebäude 29 (FIN), Raum 019",
                email="eet@farafin.de",
                url="https://eet.farafin.de",
                details_de=(
                    "Offizielles Webportal der Einführungswochen (EET): Stundenplanbau-Hilfe, "
                    "Campus-Rallye, Mathe-Vorkurs, Mentoring und Events für Erstis!"
                ),
                details_en=(
                    "Official portal for FIN introduction weeks: timetable scheduling workshops, "
                    "campus rally, math prep course, mentoring, and freshman events!"
                ),
            ),
        ),
    ),
    ContactCategory(
        key="studiengangsleiter",
        emoji="🎓",
        title_de="Studiengangsleiter & Fachberatung",
        title_en="Programme Directors & Academic Advisors",
        description_de="Fachliche Beratung zu Modulwahl, Vertiefungen und Anerkennungen.",
        description_en="Academic advising on module choices, tracks, and recognition.",
        contacts=(
            ContactPerson(
                title_de="B.Sc. & M.Sc. Informatik (INF)",
                title_en="B.Sc. & M.Sc. Computer Science",
                office="Gebäude 29 (FIN)",
                email="studienberatung-inf@cs.ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Fachstudienberatung.html",
                details_de="Fachberatung für Informatik (inkl. bilingualer Zweig).",
                details_en="Academic advisor for Bachelor and Master Computer Science.",
            ),
            ContactPerson(
                title_de="B.Sc. & M.Sc. Ingenieurinformatik (IngInf)",
                title_en="B.Sc. & M.Sc. Engineering Informatics",
                office="Gebäude 29 (FIN)",
                email="studienberatung-inginf@cs.ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Fachstudienberatung.html",
                details_de="Fachberatung für die ingenieurwissenschaftliche Informatik.",
                details_en="Academic advisor for Engineering Informatics.",
            ),
            ContactPerson(
                title_de="B.Sc. & M.Sc. Wirtschaftsinformatik (WIF)",
                title_en="B.Sc. & M.Sc. Business Informatics",
                office="Gebäude 29 (FIN)",
                email="studienberatung-wif@cs.ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Fachstudienberatung.html",
                details_de="Fachberatung an der Schnittstelle von IT und Wirtschaft.",
                details_en="Academic advisor for Business Informatics.",
            ),
            ContactPerson(
                title_de="B.Sc. Computervisualistik & M.Sc. Visual Computing (CV/VC)",
                title_en="B.Sc. Computer Visualistics & M.Sc. Visual Computing",
                office="Gebäude 29 (FIN)",
                email="studienberatung-cv@cs.ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Fachstudienberatung.html",
                details_de="Fachberatung für Computergraphik, Bildverarbeitung und VC.",
                details_en="Academic advisor for Visual Computing and Computer Graphics.",
            ),
            ContactPerson(
                title_de="M.Sc. Data and Knowledge Engineering (DKE)",
                title_en="M.Sc. Data and Knowledge Engineering (DKE)",
                office="Gebäude 29 (FIN)",
                email="dke-advisor@ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Fachstudienberatung.html",
                details_de="Internationale Fachberatung für Data Science, KI und Machine Learning.",
                details_en="Academic advisor for Data Science, AI, and Machine Learning.",
            ),
            ContactPerson(
                title_de="M.Sc. Digital Engineering (DE)",
                title_en="M.Sc. Digital Engineering (DE)",
                office="Gebäude 29 (FIN)",
                email="de-advisor@ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Fachstudienberatung.html",
                details_de="Interdisziplinäre Beratung für digitale Prozessentwicklung.",
                details_en="Interdisciplinary advisor for digital process and system development.",
            ),
        ),
    ),
    ContactCategory(
        key="stipendien",
        emoji="💶",
        title_de="Deutschlandstipendium & Finanzen",
        title_en="Germany Scholarship & Financial Aid",
        description_de="Informationen zu Stipendien, finanzieller Förderung und BAföG.",
        description_en="Information regarding scholarships, funding, and BAföG financial support.",
        contacts=(
            ContactPerson(
                title_de="Deutschlandstipendium an der OVGU",
                title_en="Germany Scholarship (Deutschlandstipendium)",
                office="Rektorat / Transfer- und Gründerzentrum (TGZ)",
                email="deutschlandstipendium@ovgu.de",
                url="https://www.ovgu.de/deutschlandstipendium.html",
                details_de=(
                    "300 € monatlich (150 € Bund + 150 € Förderer), einkommensunabhängig. "
                    "Bewerbung jährlich im SoSe (meist Juni bis Juli) für das nächste Studienjahr. "
                    "Berücksichtigt Studienleistungen und ehrenamtliches Engagement."
                ),
                details_en=(
                    "300 € per month (independent of income and BAföG). Application phase "
                    "annually in summer semester (June/July) for next academic year. "
                    "Evaluates academic achievements and social engagement."
                ),
            ),
            ContactPerson(
                title_de="BAföG-Amt & Sozialberatung (Studentenwerk)",
                title_en="BAföG Office & Social Counseling",
                office="Wohnheim 7 / Mensa UniCampus, untere Ebene",
                email="bafoeg@studentenwerk-magdeburg.de",
                url="https://www.studentenwerk-magdeburg.de/finanzierung/",
                details_de=(
                    "Zuständig für Ausbildungsförderung (BAföG), Studienkredite, "
                    "Härtefallfonds und allgemeine Sozialberatung bei finanziellen Engpässen."
                ),
                details_en=(
                    "Responsible for student loans/grants (BAföG), emergency funds, "
                    "and social counseling for financial matters."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="ausland_praktikum",
        emoji="🌍",
        title_de="Praktikumsamt & Auslandsstudium",
        title_en="Internship Office & Study Abroad",
        description_de="Ansprechpartner für Pflichtpraktika, Erasmus+ und Partnerschaften.",
        description_en="Contacts for mandatory internships, Erasmus+, and exchange programmes.",
        contacts=(
            ContactPerson(
                title_de="Praktikumsamt FIN",
                title_en="Internship Office FIN",
                office="Gebäude 29 (FIN)",
                email="praktikumsamt-fin@ovgu.de",
                url="https://www.inf.ovgu.de/Studium/Praktikumsamt.html",
                details_de=(
                    "Vorab-Genehmigung des Betriebspraktikums, Prüfung der Verträge "
                    "und Anerkennung des Praktikumsberichts nach Abschluss."
                ),
                details_en=(
                    "Pre-approval of industrial internships, review of contracts, "
                    "and credit recognition of internship reports."
                ),
            ),
            ContactPerson(
                title_de="Erasmus- & Auslandsbeauftragte FIN",
                title_en="Erasmus & Study Abroad FIN",
                office="Gebäude 29 (FIN)",
                email="erasmus-fin@ovgu.de",
                url="https://www.inf.ovgu.de/International.html",
                details_de=(
                    "Beratung zu Auslandssemestern, Partneruniversitäten weltweit, "
                    "Learning Agreements und Anerkennung ausländischer Studienleistungen."
                ),
                details_en=(
                    "Guidance on exchange semesters, partner universities worldwide, "
                    "Learning Agreements, and transfer of credits earned abroad."
                ),
            ),
            ContactPerson(
                title_de="Support Internationals & DAAD FIT (Akademisches Auslandsamt)",
                title_en="Support Internationals & DAAD FIT (International Office)",
                office="Gebäude 18 (Campus Service Center)",
                email="international@ovgu.de",
                url="https://www.ovgu.de/international.html",
                details_de=(
                    "Begleitung internationaler Studierender, DAAD FIT Initiative "
                    "(Förderung internationaler Talente für Studium und Beruf), "
                    "Internationales Buddy-Programm und Sprachkurse."
                ),
                details_en=(
                    "Comprehensive support for international students, DAAD FIT initiative "
                    "(career preparation and academic integration), International Buddy "
                    "Programme, and integration courses."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="support",
        emoji="🤝",
        title_de="Beratung & Psychosozialer Support",
        title_en="Counseling & Psychological Support",
        description_de="Vertrauliche Unterstützung bei Stress, Krisen und Familie.",
        description_en="Confidential support for mental health, exam anxiety, and family care.",
        contacts=(
            ContactPerson(
                title_de="Psychosoziale Studierendenberatung (PSB)",
                title_en="Psychosocial Student Counseling (PSB)",
                office="Wohnheim 7, J.-G.-Nathusius-Ring 5",
                email="psb@studentenwerk-magdeburg.de",
                url="https://www.studentenwerk-magdeburg.de/beratung/psychosoziale-beratung/",
                details_de=(
                    "Kostenlose, neutrale und vertrauliche psychologische Beratung bei "
                    "Prüfungsangst, Schreibblockaden, Überlastung und Krisen."
                ),
                details_en=(
                    "Free, confidential psychological counseling for exam anxiety, stress, "
                    "writer's block, motivational crises, and personal challenges."
                ),
            ),
            ContactPerson(
                title_de="Gleichstellungsbeauftragte der FIN",
                title_en="Equal Opportunity Officer FIN",
                office="Gebäude 29 (FIN)",
                email="gleichstellung-fin@ovgu.de",
                url="https://www.inf.ovgu.de/Fakult%C3%A4t/Gleichstellung.html",
                details_de=(
                    "Förderung von Chancengleichheit, Unterstützung von Studentinnen "
                    "in MINT-Fächern sowie Vereinbarkeit von Studium und Familie."
                ),
                details_en=(
                    "Promotion of equal opportunities, support for women in STEM, "
                    "and family/study balance."
                ),
            ),
        ),
    ),
)


def get_category_by_key(key: str) -> ContactCategory | None:
    """Finds a contact category by its unique key."""
    for cat in CONTACT_CATEGORIES:
        if cat.key == key:
            return cat
    return None

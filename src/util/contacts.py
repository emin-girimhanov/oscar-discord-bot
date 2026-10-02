""" This module holds structured contact information for students at FIN OVGU.

    **Every fact in here was read on the page its entry links to, on 2026-10-02.**

    The first version of this list looked official and was not. It named mailboxes that
    do not exist (`pa-fin@ovgu.de`, `studienberatung-inf@cs.ovgu.de`, an own address
    per study programme), put the student council into room 019 with office hours
    "almost daily", and five of its links answered 404. A student who wrote to one of
    those addresses got a bounce, or worse, nothing.

    So the rule for this file is: a room, a mail address or a phone number is only
    written down when the linked page states it. Where the page states none, the field
    stays empty and the entry sends the student to the page. An empty field is honest,
    a plausible looking one is not. `tests/test_contacts.py` holds the addresses that
    were made up, so they cannot come back.

    When a link dies, look the office up again rather than guessing the new address.
"""

from dataclasses import dataclass


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class ContactPerson:
    """ Represents a single contact person or office.

        `office`, `email` and `phone` may be empty. The view leaves an empty one out.
    """
    title_de: str
    title_en: str
    office: str
    email: str
    url: str
    details_de: str
    details_en: str
    phone: str = ""


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
        title_de="Dekanat & Prüfungsamt",
        title_en="Dean's Office & Examination Office",
        description_de="Prüfungen, Noten, Atteste und die Leitung der Fakultät.",
        description_en="Exams, grades, medical certificates and the faculty management.",
        contacts=(
            ContactPerson(
                title_de="Prüfungsamt FIN",
                title_en="Examination Office FIN",
                office="Gebäude 29, Raum 101/102",
                email="fin-pruefungsamt@ovgu.de",
                url="https://www.fin.ovgu.de/pamt.html",
                details_de=(
                    "Anlaufstelle für Noten, Prüfungsan- und -abmeldung, Rücktritt wegen "
                    "Krankheit, Anerkennungen und Abschlussarbeiten. "
                    "Sprechzeiten nur mit Termin. "
                    "Die Zeiten und alle Formulare stehen auf der Seite."
                ),
                details_en=(
                    "Contact for grades, exam registration and deregistration, withdrawal "
                    "due to illness, credit transfers and theses. "
                    "Office hours by appointment only. The page lists the hours and all forms."
                ),
            ),
            ContactPerson(
                title_de="Dekanat FIN",
                title_en="Dean's Office FIN",
                office="Gebäude 29 (FIN)",
                email="fin-dekan@ovgu.de",
                url="https://www.fin.ovgu.de/Fakult%C3%A4t/Organisationsstruktur/Dekanat.html",
                details_de=(
                    "Dekan, Studiendekan und Sekretariat der Fakultät. "
                    "Die Seite nennt jede Person mit Mailadresse und Telefon."
                ),
                details_en=(
                    "Dean, Dean of Studies and the secretariat of the faculty. "
                    "The page names every person with mail address and phone."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="farafin",
        emoji="🐘",
        title_de="Fachschaftsrat (FaRaFIN)",
        title_en="Student Council (FaRaFIN)",
        description_de="Studentische Selbstverwaltung – von Studierenden für Studierende.",
        description_en="Student self-government of the faculty – by students for students.",
        contacts=(
            ContactPerson(
                title_de="Fachschaftsrat Informatik (FaRaFIN)",
                title_en="Computer Science Student Council (FaRaFIN)",
                office="G29-103",
                email="post@farafin.de",
                phone="(+49) 391 67 51377",
                url="https://farafin.de",
                details_de=(
                    "Erste Anlaufstelle bei Fragen rund ums Studium, bei Problemen mit "
                    "Modulen oder Dozierenden, für Altklausuren und Events. "
                    "Feste Sprechzeiten gibt es gerade nicht. Schau einfach im Büro vorbei "
                    "oder schreib eine Mail."
                ),
                details_en=(
                    "Your first contact for questions about your studies, for trouble with "
                    "modules or lecturers, for past exams and events. "
                    "There are no fixed office hours at the moment. Drop by the office or "
                    "write a mail."
                ),
            ),
            ContactPerson(
                title_de="Einführungswoche (E-Woche) für Erstsemester",
                title_en="Orientation Week (E-Woche) for New Students",
                office="G29-103 (FaRaFIN), die Woche findet im Gebäude 29 statt",
                email="post@farafin.de",
                url="https://farafin.de/erstsemester/e-woche/",
                details_de=(
                    "Der FaRaFIN organisiert die E-Woche zum Semesterstart, für alle neuen "
                    "Bachelor- und Masterstudierenden der FIN, auf Deutsch und Englisch. "
                    "Mit Stundenplanbau, Campusrallye, Stadtrallye und Spieleabend. "
                    "Das Wochenprogramm, die Vorkurse und das Mentoring stehen auf der Seite."
                ),
                details_en=(
                    "FaRaFIN runs the orientation week at the start of the semester, for all "
                    "new Bachelor and Master students of the FIN, in German and English. "
                    "With timetable building, a campus rally, a city rally and a games night. "
                    "The page has the programme of the week, the prep courses and the mentoring."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="studiengangsleiter",
        emoji="🎓",
        title_de="Studiengangsleitung",
        title_en="Programme Directors",
        description_de="Fachliche Fragen zu Modulwahl, Vertiefungen und Anerkennungen.",
        description_en="Academic questions on module choices, tracks and recognition.",
        contacts=(
            ContactPerson(
                title_de="Studiengangsleiter aller Studiengänge",
                title_en="Programme Directors of All Programmes",
                office="Gebäude 29 (FIN)",
                email="",
                url="https://www.fin.ovgu.de/Studium/Vor+dem+Studium/Studiengangsleiter.html",
                details_de=(
                    "Jeder Studiengang der FIN hat eine Leitung und eine Stellvertretung. "
                    "Die Seite nennt beide für jeden Studiengang. "
                    "Eine eigene Mailadresse pro Studiengang gibt es nicht, "
                    "schreib der Person direkt."
                ),
                details_en=(
                    "Every programme of the FIN has a director and a deputy. "
                    "The page names both for each programme. "
                    "There is no mailbox per programme, write to the person directly."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="stipendien",
        emoji="💶",
        title_de="Deutschlandstipendium & Finanzen",
        title_en="Germany Scholarship & Finances",
        description_de="Deutschlandstipendium, BAföG und Beratung zur Finanzierung.",
        description_en="Germany Scholarship, BAföG and advice on financing your studies.",
        contacts=(
            ContactPerson(
                title_de="Deutschlandstipendium an der OVGU",
                title_en="Germany Scholarship (Deutschlandstipendium)",
                office="Gebäude 18, Raum 133",
                email="",
                url="https://www.ovgu.de/deutschlandstipendium.html",
                details_de=(
                    "300 € im Monat, unabhängig vom Einkommen. "
                    "Voraussetzungen, Bewerbungszeitraum und Förderdauer stehen auf der Seite."
                ),
                details_en=(
                    "300 € per month, independent of income. "
                    "The page has the requirements, the application period and the duration."
                ),
            ),
            ContactPerson(
                title_de="BAföG (Studentenwerk Magdeburg)",
                title_en="BAföG (Studentenwerk Magdeburg)",
                office="",
                email="",
                url="https://www.studentenwerk-magdeburg.de/bafoeg/",
                details_de=(
                    "Antrag, Sprechstunden und die zuständigen Ansprechpersonen für BAföG. "
                    "Daneben berät das Studentenwerk zu Krediten und zur Studienfinanzierung."
                ),
                details_en=(
                    "Application, consultation hours and the responsible contacts for BAföG. "
                    "The Studentenwerk also advises on loans and on financing your studies."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="ausland_praktikum",
        emoji="🌍",
        title_de="Ausland & Internationales",
        title_en="Study Abroad & International",
        description_de="Erasmus, Auslandssemester und Hilfe für internationale Studierende.",
        description_en="Erasmus, semesters abroad and support for international students.",
        contacts=(
            ContactPerson(
                title_de="Erasmus-Koordination FIN",
                title_en="Erasmus Coordinator FIN",
                office="G29-214",
                email="claudia.krull@ovgu.de",
                url="https://www.fin.ovgu.de/Studium/W%C3%A4hrend+des+Studiums/Outgoing.html",
                details_de=(
                    "Beratung zu Auslandssemestern, Partneruniversitäten und Learning Agreements."
                ),
                details_en=(
                    "Guidance on semesters abroad, partner universities and Learning Agreements."
                ),
            ),
            ContactPerson(
                title_de="Support Internationals at FIN",
                title_en="Support Internationals at FIN",
                office="Gebäude 29 (FIN)",
                email="",
                url=(
                    "https://www.fin.ovgu.de/inf/en/Study/Being+a+student/Incoming/"
                    "Support+Internationals+at+FIN.html"
                ),
                details_de=(
                    "Hilfe der Fakultät für internationale Studierende. "
                    "Die Seite ist auf Englisch und nennt das Team."
                ),
                details_en=(
                    "The faculty's support for international students. The page names the team."
                ),
            ),
            ContactPerson(
                title_de="International Office der OVGU",
                title_en="International Office of the OVGU",
                office="",
                email="",
                url="https://www.ovgu.de/international.html",
                details_de=(
                    "Die zentrale Anlaufstelle der Universität für internationale Studierende "
                    "und für Wege ins Ausland."
                ),
                details_en=(
                    "The university's central office for international students "
                    "and for going abroad."
                ),
            ),
        ),
    ),
    ContactCategory(
        key="support",
        emoji="🤝",
        title_de="Beratung & Gleichstellung",
        title_en="Counselling & Equal Opportunity",
        description_de="Vertrauliche Unterstützung bei Stress, Krisen und Familie.",
        description_en="Confidential support with stress, crises and family matters.",
        contacts=(
            ContactPerson(
                title_de="Psychosoziale Beratung (Studentenwerk)",
                title_en="Psychosocial Counselling (Studentenwerk)",
                office="",
                email="",
                url="https://www.studentenwerk-magdeburg.de/soziales/psb/",
                details_de=(
                    "Beratung bei Prüfungsangst, Überlastung und Krisen. "
                    "Termine und Ansprechpersonen stehen auf der Seite."
                ),
                details_en=(
                    "Counselling for exam anxiety, overload and crises. "
                    "The page has the appointments and the counsellors."
                ),
            ),
            ContactPerson(
                title_de="Gleichstellungsbeauftragte der FIN",
                title_en="Equal Opportunity Officer FIN",
                office="G29-214",
                email="claudia@isg.cs.uni-magdeburg.de",
                url="https://www.fin.ovgu.de/GuF.html",
                details_de=(
                    "Chancengleichheit an der Fakultät sowie Vereinbarkeit von Studium "
                    "und Familie. "
                    "Die Seite nennt auch die Stellvertretungen und den Familienbeauftragten."
                ),
                details_en=(
                    "Equal opportunities at the faculty, and combining studies and family. "
                    "The page also names the deputies and the family officer."
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

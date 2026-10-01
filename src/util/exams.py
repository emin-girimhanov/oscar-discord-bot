""" The past exam archives the student councils of the OVGU run.

    OSCAR links to these archives. It stores no exam paper itself, because the
    copyright on an exam usually sits with the chair and not with the student who
    wrote it. Issue #43 settled that question: link, never host.

    Every address in here was opened by hand before it was added. A dead link sends
    a student in circles, so add nothing you have not seen answer.

    `klausuren.farafin.de` used to be the one address OSCAR showed. That host no
    longer resolves, which is why the entries below carry the real pages.
"""

from dataclasses import dataclass

from util.enums import LanguageCode


# Nine fields, because an archive needs a name, a faculty and a line of text in
# both languages. Splitting that into two classes would only move the count.
# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class ExamArchive:
    """ One archive of past exams, run by one student council.

        `url_de` and `url_en` may be the same page. Only FaRaFIN keeps a separate
        English version.
    """
    key: str
    council: str
    emoji: str
    faculty_de: str
    faculty_en: str
    url_de: str
    url_en: str
    covers_de: str
    covers_en: str

    def url(self, language: LanguageCode) -> str:
        """ The address to open for a student reading in `language`.

            Parameters:
                language: The language the student set in OSCAR.

            Returns:
                An absolute `https` url.
        """
        return self.url_en if language == LanguageCode.EN else self.url_de

    def faculty(self, language: LanguageCode) -> str:
        """ The name of the faculty the archive belongs to."""
        return self.faculty_en if language == LanguageCode.EN else self.faculty_de

    def covers(self, language: LanguageCode) -> str:
        """ One line saying which exams a student finds in this archive."""
        return self.covers_en if language == LanguageCode.EN else self.covers_de


# FaRaFIN comes first. It is the archive for the programmes OSCAR is built for, and
# the others only matter for the modules a student takes outside the FIN.
EXAM_ARCHIVES: tuple[ExamArchive, ...] = (
    ExamArchive(
        key="farafin",
        council="FaRaFIN",
        emoji="💻",
        faculty_de="Fakultät für Informatik (FIN)",
        faculty_en="Faculty of Computer Science (FIN)",
        url_de="https://farafin.de/dienste/klausuren/",
        url_en="https://farafin.de/en/services/exams/",
        covers_de=(
            "Alle Informatik-Module, dazu Gedächtnisprotokolle. "
            "Sortierbar nach Modul, Prüfendem und Studiengang."
        ),
        covers_en=(
            "Every computer science module, plus written recollections of oral exams. "
            "Sortable by module, examiner and programme."
        ),
    ),
    ExamArchive(
        key="farawiwi",
        council="FaraWiwi",
        emoji="📈",
        faculty_de="Fakultät für Wirtschaftswissenschaft (FWW)",
        faculty_en="Faculty of Economics and Management (FWW)",
        url_de="https://www.farawiwi.ovgu.de/Klausuren.html",
        url_en="https://www.farawiwi.ovgu.de/Klausuren.html",
        covers_de=(
            "BWL, VWL und Statistik, getrennt nach Bachelor, Master und "
            "Nicht-FWW. Wichtig für Wirtschaftsinformatik."
        ),
        covers_en=(
            "Business studies, economics and statistics, split into Bachelor, Master "
            "and non-FWW. The one for Business Informatics."
        ),
    ),
    ExamArchive(
        key="faramath",
        council="FaraMath",
        emoji="➗",
        faculty_de="Fakultät für Mathematik (FMA)",
        faculty_en="Faculty of Mathematics (FMA)",
        url_de="https://www.faramath.ovgu.de/Ged%C3%A4chtnisprotokolle/Archiv.html",
        url_en="https://www.faramath.ovgu.de/Ged%C3%A4chtnisprotokolle/Archiv.html",
        covers_de=(
            "Gedächtnisprotokolle zu Mathematik, nach Fach und Prüfendem sortiert. "
            "Deckt die Mathe-Module der Informatik-Studiengänge ab."
        ),
        covers_en=(
            "Written recollections for the mathematics modules, sorted by subject and "
            "examiner. Covers the maths every computer science programme contains."
        ),
    ),
)


def get_archives() -> tuple[ExamArchive, ...]:
    """ Every archive OSCAR knows, in the order they should be shown."""
    return EXAM_ARCHIVES


def primary_archive() -> ExamArchive:
    """ The archive to link when there is room for only one button.

        Returns:
            The FaRaFIN archive, because OSCAR serves FIN students.
    """
    return EXAM_ARCHIVES[0]

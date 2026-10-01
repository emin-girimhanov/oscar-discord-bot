# Standard study plans

`/standard_plan` shows the Regelstudienplan of a programme. **Every number in it comes
out of the Studien- und Prüfungsordnung as a PDF.** Nothing is worked out from module
titles, from credit point sums or from what would look plausible.

A student plans a year of their life from this picture. A wrong plan is worse than no
plan, because it reads like an official answer.

---

## What a student sees

| | |
| :--- | :--- |
| Bachelor, nothing saved yet | **the table as a picture**, cut out of the SPO |
| Bachelor, modules saved | the table redrawn from JSON, with ticks |
| Master | the areas and their credit point ranges, from JSON |

The picture wins while there is nothing to tick, because it carries what a list of
module titles cannot: the exam rules, the weightings, the *mind. 10 CP benotet* bars
and the legend. A PNG cannot be ticked off, so `SPlanView` renders the JSON as soon as
the student has saved something.

---

## The sources

| Programmes | Document | Plan |
| :--- | :--- | :--- |
| B.Sc. INF, CV, IngInf, WIF | [SPO Bachelor, Lesefassung 02.04.2024](https://www.fin.ovgu.de/inf_media/Studiendokumente/Studien_+und+Pr%C3%BCfungsordnung/Bachelorstudieng%C3%A4nge/SPO_Bachelor_2024_04_02_Lesefassung.pdf) | pages 29–37, one table per programme and start |
| M.Sc. INF, IngInf, WIF | [SPO Master 23.05.2016](https://www.fin.ovgu.de/inf_media/Studiendokumente/Studien_+und+Pr%C3%BCfungsordnung/Konsekutive+Masterstudieng%C3%A4nge/SPO_Master_2016_05_23_3Semester_2.pdf), amended [29.06.2020](https://www.fin.ovgu.de/inf_media/Studiendokumente/Studien_+und+Pr%C3%BCfungsordnung/Konsekutive+Masterstudieng%C3%A4nge/SPO_Master_2020_06_29_Satzungs%C3%A4nderung.pdf) | pages 26–27, Anlage 1 |
| M.Sc. DKE, DE | [SPO Master (englischsprachig) 08.04.2021](https://www.fin.ovgu.de/inf_media/Studiendokumente/Studien_+und+Pr%C3%BCfungsordnung/Englischsprachige+Masterstudieng%C3%A4nge/SPO_Master_2021_04_08.pdf) | pages 27–28, Anlage A and B |
| M.Sc. VC | [SPO Master Visual Computing 08.04.2021](https://www.fin.ovgu.de/inf_media/Studiendokumente/Studien_+und+Pr%C3%BCfungsordnung/Englischsprachige+Masterstudieng%C3%A4nge/Visual+Computing+Master/SPO_Master_2021_04_08.pdf) | page 29, Anlage C |

Every file in `assets/json/semesterplans/` carries a `source` block naming the
document, the URL, the page and the date it was read. A test refuses a plan without
one.

---

## How long a master runs

This is where the shipped data was wrong, and where it is easy to be wrong again.

| Programme | Semesters | Credit points |
| :--- | ---: | ---: |
| M.Sc. Informatik, Ingenieurinformatik, Wirtschaftsinformatik | **3** | **90** |
| M.Sc. DKE, Digital Engineering, Visual Computing | 4 | 120 |

> SPO Master 2016, § 5 (2): *"Die Regelstudienzeit beträgt einschließlich der
> Masterarbeit drei Semester."* § 6 (1): *"Er beträgt insgesamt 90 CP"*

The three German masters shipped as four semesters and 120 CP, with eight invented
modules called *WPF Vertiefung Informatik I* to *VIII* and a *Masterkolloquium* the
regulation does not have. The tests asserted four semesters and 120 CP for every
master, which held the error in place. `SEMESTERS` in
`tests/test_semesterplan_assets.py` now writes the length down per programme, with the
paragraph it comes from.

---

## Why a master has no module list

Its regulation does not print one. It prints a table of areas with a credit point
range each, and this sentence:

> *"Der Regelstudienplan ist eine Empfehlung zur Anordnung der Bereiche. Es steht den
> Studierenden frei, von dieser Empfehlung abzuweichen."*

So the plan shows the areas and their ranges. Anything more would be invented. The
three English programmes shipped with names like *Advanced Computer Graphics*,
*Visual Computing Elective I* and *Smart Industry & IoT Architectures*, none of which
appear in the document, at 5 CP where the official modules carry 6.

---

## Rebuilding

The pictures:

```bash
pip install pymupdf
python tools/extract_semesterplan_images.py
```

It downloads the SPO, renders the page each table sits on, trims the margin and writes
`assets/images/<id>_SPO_<year>_<season>.png`. The id is the one
`STUDYCOURSE_TO_IMAGE_ID` in `src/oscar/ui/splan_view.py` maps a programme to.

The JSON is written by hand from the same PDF, because a table of merged and coloured
cells does not extract cleanly. Check every semester against the *CP gesamt* row the
document prints at the bottom: it has to be 30, and that is the checksum which says
whether the transcription came out right.

**After a new edition:** the page numbers move. Read them off the document again
before running anything.

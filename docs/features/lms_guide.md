# Learning platforms and portals at the OVGU

New students meet several digital portals and nobody tells them which one holds the
slides, where homework goes, and where an exam registration actually counts.

This page answers **[Issue #51](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/51)**.

---

## 1. The four portals

!!! warning "This list was wrong until 2026-09-17"
    The first version of this guide named `moodle2.cs.ovgu.de`, `webwork.cs.ovgu.de`,
    `gitlab.cs.ovgu.de` and `handbook.cs.ovgu.de`. **All four answer NXDOMAIN**, from
    the university's own resolver as well as from outside. A student following the
    guide landed in a browser error with no way to tell that the bot was wrong rather
    than their network. Every address below was resolved and opened by hand.

| Portal | Address | Login | What it is for |
| :--- | :--- | :--- | :--- |
| **eLearning (Moodle)** | [elearning.ovgu.de](https://elearning.ovgu.de) | OvGU account, the *Login mit OvGU-Account* button | Slides, exercise sheets, submissions, forums, tutorial group enrolment |
| **LSF (HISinOne)** | [lsf.ovgu.de](https://lsf.ovgu.de) | Central university account | Exam registration and withdrawal, transcript, room and lecture schedule |
| **Module handbook (BookStack)** | [bookstack.cs.ovgu.de](https://bookstack.cs.ovgu.de) | none, it is public | Official module descriptions, examination regulations, credit points |
| **FIN GitLab** | [isggit3.cs.ovgu.de](https://isggit3.cs.ovgu.de) | FIN account (LDAP or SSH key) | Programming labs, software projects, code reviews, CI/CD |

`cloud.ovgu.de` carries the Nextcloud Tables database OSCAR reads its module data from.
Students never open it themselves.

There is **one** Moodle. The computing centre (URZ) runs it at `elearning.ovgu.de` and
documents it as the e-learning platform of the whole university. Earlier versions of
this guide claimed the faculty ran a second one. It does not.

---

## 2. Common questions

### "I enrolled in a course on Moodle. Am I registered for the exam?"

**No.** Enrolling on Moodle gives you the material and nothing else. A legally binding
exam registration happens in **LSF**, inside the registration period. The deadlines are
in `/help` under *Öffnen → Fristen & Termine*.

### "A course wants an enrolment key."

It is announced in the first lecture. Ask in the course channel if you missed it.

### "Where do I submit programming assignments?"

Most practical courses and team projects use the faculty GitLab at
`isggit3.cs.ovgu.de`. Upload your public SSH key to your profile for git access. OSCAR
itself is developed there.

---

## 3. Inside Discord

Type `/lms` (or `/elearning`). It opens a dropdown with one entry per portal, each
with its address, what to log in with, and what it is for.

The same guide is in the help menu, for anybody who does not know the command yet:

```text
/help → Öffnen → Lernplattformen
```

The same answer is in the FAQ menu under *"Welche Plattformen nutzt die FIN?"*, written
once in `src/util/translations.py` and shown in both places.

---

## 4. Where the list lives

`src/util/lms.py`. Adding a portal means opening it first, then adding its host to
`LIVE_HOSTS` in `tests/test_lms.py`. A test refuses any entry whose host nobody has
checked, and a second test refuses the four dead ones by name.

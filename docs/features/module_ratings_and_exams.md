# Module Ratings & Past Exams

Peer feedback from students who already completed a course is one of the most valuable sources of guidance when planning upcoming semesters. At the same time, preparation with past exams (*Altklausuren*) requires clear handling of copyright and faculty policies.

This document details OSCAR's module rating system and the architecture decision regarding the past exam archive ([Issue #43](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/43)).

---

## 1. Module Ratings & Difficulty Feedback

### Features
Every student can evaluate modules they have attended directly within Discord:

* **Overall Rating (1–5 Stars):** From 1 (poor) to 5 (excellent).
* **Subjective Difficulty (1–5):** From 1 (very easy) to 5 (very hard / demanding).
* **Review & Tips (Optional):** Helpful advice for subsequent cohorts (e.g. recommended prerequisites, exercise workload, or exam format tips).

### Access Points
1. **Interactive Button on Module Card:** When viewing any module via `/module` or `/filter`, click the green **`⭐ Bewerten` / `⭐ Rate`** button to open the submission modal dialog.
2. **Slash Command `/rate`:** Directly rate any module with autocompleted choices:
   ```text
   /rate modul:Algorithmen und Datenstrukturen bewertung:5 schwierigkeit:4 kommentar:Sehr gutes Modul, wöchentliche Übungszettel frühzeitig anfangen!
   ```
   If `bewertung` or `schwierigkeit` are omitted, OSCAR automatically displays the interactive modal popup.

### Display on Module Overview
The aggregate statistics are automatically shown directly on the module card:
```text
⭐ 4.3/5 (7 ratings) | 🏋️ Difficulty: 3.6/5
```

### Data Privacy & Integrity
* **One Vote per Student:** Each student (`user_id`) has exactly one vote per module. Submitting a new rating updates the existing entry (`ON CONFLICT DO UPDATE`).
* **Anonymous Aggregation:** Discord IDs and user names are never displayed alongside ratings or aggregated statistics.
* **GDPR Compliance:** Under `/my_data`, any ratings submitted by the student are included in their personal data export and completely wiped upon account deletion (`Database.delete_user_data`).

---

## 2. Past Exams & FaRaFIN Klausurenarchiv

### The Question from Issue #43
Issue #43 asked:
> *Who holds the copyright on an exam paper? Whether the faculty allows redistribution at all? Where the files would live? How a wrong or harmful upload gets removed?*

### The Decision
Hosting uncurated exam PDFs directly in Discord attachments or on a bot-managed server introduces severe legal liabilities:
1. **Copyright:** Exam papers are intellectual property of the examining chairs and professors, not the students. Redistribution without explicit written license from the examiner is legally prohibited.
2. **Storage & Expiration:** Discord CDN attachments expire, while local server storage requires moderation, malware scanning, and takedown procedures.
3. **Established Infrastructure:** The student councils already run the archives. **FaRaFIN** keeps the computer science one at [farafin.de](https://farafin.de/dienste/klausuren/), **FaraWiwi** the FWW one at [farawiwi.ovgu.de](https://www.farawiwi.ovgu.de/Klausuren.html), and **FaraMath** the maths recollections at [faramath.ovgu.de](https://www.faramath.ovgu.de/Ged%C3%A4chtnisprotokolle/Archiv.html).

### Implementation
* **Direct Integration:** Every module card contains a **`📚 Altklausuren` / `📚 Past Exams`** link button navigating directly to the official portal.
* **Slash Command `/klausuren`:** Explains how to log in with your CS student credentials (FIN account) and how to submit exam recollection protocols (*Gedächtnisprotokolle*) to FaRaFIN after taking an exam.

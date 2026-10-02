# Cohort Statistics & Comparative Analytics

!!! note "Switched off for now"
    This feature is not in the slash menu at the moment. OSCAR had grown to twenty nine
    commands, and the ones around the semester plan come first. The code is kept, and
    `HIDDEN` in `src/util/command_surface.py` switches it back on.

Tracking personal study progress is motivating, but students frequently want to know how their semester workload compares to their peers in the same degree programme and semester (*"Am I planning too many or too few modules?", "Which electives are my classmates taking this term?"*).

This document details OSCAR's privacy-preserving cohort analytics system ([Issue #48](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/48)).

---

## 1. Core Principles & Privacy (k-Anonymity)

Student course selections and academic paces are sensitive personal data. To prevent deanonymization and profile fingerprinting, OSCAR strictly enforces **k-anonymity** with $k \ge 3$:

* **Cohort Threshold ($k=3$):** Detailed statistics (average planned CP, average module counts, and top module breakdowns) are **only displayed if at least 3 students** are registered in the specific cohort (same study course and semester).
* **Privacy Fallback:** If fewer than 3 students are in a cohort, OSCAR presents a transparent privacy notice and displays only high-level, faculty-wide distributions where no individual student's curriculum can be deduced.
* **Aggregated Only:** Individual module selections, names, and Discord IDs are never displayed or queryable.

---

## 2. Available Metrics

When a cohort satisfies the privacy threshold, OSCAR calculates and visualizes:

1. **Cohort Headcount:** Total number of students participating in this cohort.
2. **Average Workload (Ø Modules & CP):** Mean number of planned courses and credit points for the current semester.
3. **Most Planned Modules:** Ranked list of the top 5 modules in the cohort, complete with visual percentage bars (`[████████░░] 80%`).
4. **Faculty-wide Distribution:** Overview of registered students across all FIN programmes (e.g. B.Sc. INF, B.Sc. CV, M.Sc. DKE).

---

## 3. How to Access

### Slash Commands
* **`/cohort [studiengang] [semester]`**: Opens the cohort statistics view. By default, it automatically selects your configured study course and semester from `/start`. You can optionally specify a different programme or semester.
* **`/statistik`**: Convenience alias for `/cohort`.

### Interactive Button in `/progress` & `/badges`
Inside the personal progress view (`/progress` or `/badges`), students can click the **`👥 Kohortenvergleich` / `👥 Cohort Stats`** button to seamlessly toggle between their personal achievements and cohort analytics without needing to type a new command.
Clicking **`🏆 Mein Fortschritt` / `🏆 My Progress`** toggles back to the personal badges view.

---

## 4. Technical Architecture

* **Database Method:** `Database.get_cohort_statistics(major, semester, min_cohort_size=3)` performs aggregated queries against `preferences` and `semester_plans`.
* **Type Safety:** Typed return structure via `CohortStatsDict`, `TopModuleDict`, and `MajorDistDict` in `src/util/typed_dicts.py`.
* **Internationalization:** Full bilingual German/English support via `COHORT_TEXTS` in `src/util/translations.py`.

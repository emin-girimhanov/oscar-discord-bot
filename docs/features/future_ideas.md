# Community Feature Ideas

Every idea on this page is tracked as an issue. The issue holds the current thinking, the
open questions and any decision that was already made, so **the issue is the source of
truth** and this page is only the way in.

Want to contribute? Pick an idea, read its issue, and say what you would build. A comment
costs nothing and saves the wrong work.

---

## Academic content

| Idea | Issue | Where it stands |
| --- | --- | --- |
| Tick off what you already have in the standard study plan | [#40](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/40) | :material-check: Implemented: Interactive standard study plan checklist with passed/planned toggle and progress bar (`/splan`) |
| Bring the FAQ into the bot | [#41](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/41) | :material-check: Implemented: Single-source FAQ integration with interactive dropdown in Discord (`/help`) |
| Suggest modules that fit a student | [#42](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/42) | :material-check: Implemented: Curricular recommendation engine based on degree, open credits, and topic clusters (`/suggest`, `/recommend`) |
| Compare several modules side by side | [#45](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/45) | :material-check: Implemented: Side-by-side module comparator (`/compare`) |
| Assignment deadlines and reminders | [#50](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/50) | :material-check: Implemented: Exam registration windows, re-registration deadlines, and countdowns (`/fristen`) |
| Module ratings and an archive of past exams | [#43](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/43) | :material-check: Implemented: Peer ratings & difficulty feedback (`/rate`) and FaRaFIN Klausurenarchiv integration (`/klausuren`) |
| Add the Master study plans | [#22](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/22) | :material-check: Implemented: Standard study plans for all 6 Master programmes (SPO 2021) |


## Integrations

| Idea | Issue | Where it stands |
| --- | --- | --- |
| LSF, UniNow or Studo account linking | [#12](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/12) | :material-check: Feasibility Spike Concluded: Direct scraping rejected (GDPR & security risks); resolved via decoupled deep-links, RFC 5545 `.ics` export, and `/fristen` |
| Export a semester plan to a calendar file | [#44](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/44) | :material-check: Implemented: RFC 5545 `.ics` export with handbook links and FIN examination deadlines |
| Which learning management system does the faculty use | [#51](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/51) | :material-check: Implemented: Interactive LMS navigation & platform guide (`/lms`, `/elearning`) with single-source FAQ integration |

## Search and interface

| Idea | Issue | Where it stands |
| --- | --- | --- |
| Several filter values, sorting and saved filters | [#46](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/46) | :material-check: Implemented: Multi-select filtering and sorting across all module categories (`/filter`) |
| Support a third interface language | [#52](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/52) | Mostly translation work. Check the demand first |

## Your own data

| Idea | Issue | Where it stands |
| --- | --- | --- |
| Export and delete your own data | [#47](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/47) | :material-check: Implemented: Full personal data export and self-service GDPR account wipe (`/mydata`) |
| Personal progress, and cohort statistics | [#48](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/48) | :material-check: Implemented: Personal progress tracking (`/progress`), badges (`/badges`), and privacy-preserving cohort analytics (`/cohort`, `/statistik`) |

## Community

| Idea | Issue | Where it stands |
| --- | --- | --- |
| Find other students who plan the same module | [#49](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/49) | :material-check: Implemented: Opt-in study buddy matching with private threads |
| Achievement badges | [#11](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/11) | :material-check: Implemented: Achievement badges with `/badges` |
| Weekly code golf challenge | [#53](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/53) | :material-check: Implemented: Weekly code golf challenges, byte-counting & live leaderboards (`/codegolf`, `/challenge`) |

## Running the bot

| Idea | Issue | Where it stands |
| --- | --- | --- |
| Describe the Docker way to run OSCAR on a home server | [#54](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/54) | :material-check: Implemented: Docker Compose setup guide in self-hosting documentation |

---

## Adding a new idea

Open an issue. Do not add it to this page alone, or it will drift away from what is
actually planned, which is exactly what this page used to do.

A good idea issue says who wants it and why, not how to build it. One honest sentence
about what is unclear is worth more than a feature list.

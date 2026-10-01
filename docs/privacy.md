# Privacy Policy

## 1. Controller (Responsible Party)

This policy describes **one running instance** of OSCAR: the Discord bot `OSCAR#0846` and this copy of the documentation.

The "Controller" pursuant to Art. 4(7) of the General Data Protection Regulation (GDPR), the one who decides on the purposes and means of processing personal data, is the person who operates this instance:

<div class="author-grid">
  <ul>
    <li>
      <strong>Emin Girimhanov</strong><br>
      <em>Operator of this OSCAR instance</em><br>
      Student at the Faculty of Computer Science (FIN), Otto-von-Guericke University Magdeburg<br>
      Germany<br>
      <a data-email="ZW1pbi5naXJpbWhhbm92QHN0Lm92Z3UuZGU=" href="#">emin.girimhanov [at] st.ovgu.de</a>
    </li>
  </ul>
</div>

### What the university has to do with it
OSCAR was developed by a team of students as a supervised software project at the Chair of Simulation (FIN, OVGU). The team and the supervisors are named on the [About OSCAR](about_oscar.md) page.

**The university, the chair, the supervisors and the other members of the team do not operate this instance.** They have no access to its database, its log or its backups, and they are not responsible for it.

The module catalogue the bot shows is read from the Nextcloud of the faculty, and the handbook links from the faculty BookStack. Those requests contain nothing about you.

An OSCAR instance somebody else runs has its own operator and its own privacy policy. The documentation of the faculty is at <http://studium-lehre.gitlabpages.cs.ovgu.de/discord-bot>.

---

## 2. Data Protection Officer

No data protection officer is appointed for this instance. It is run by a single private person. For every question about your data, write to the operator named in Section 1.

The Data Protection Officer of OVGU is responsible for the systems of the university. This bot is not one of them.

---

## 3. Scope of this Policy

This Privacy Policy applies to:

1. The **OSCAR documentation website** (static site).
2. The **OSCAR Discord bot** (software service operated on Discord).

---

## 4. Documentation Website (MkDocs)

### 4.1 Purpose & Hosting
This website provides project documentation. It is hosted on **GitHub Pages**, a service of GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA.

By design, this site does **not** use analytics tools (e.g., Google Analytics, Matomo) and does **not** set tracking cookies.

### 4.2 Server Log Files
When you visit this website, GitHub processes technical access data, as every web host does. According to GitHub this includes:

* **IP address**
* **Date and time** of access
* **Requested resource** (URL/path)
* **Browser and operating system** information

The operator of this site cannot see these logs and receives no statistics about visitors.

**Legal basis:** Art. 6(1)(f) GDPR, the legitimate interest in publishing the documentation of an open source project on a reliable host.

### 4.3 Retention
GitHub decides how long it keeps these logs, see the [GitHub Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

---

## 5. External Resources & Fonts

To protect your privacy, this documentation website loads **nothing from other hosts**: no Content Delivery Network, no badge service, no analytics. Every image, icon, script and style sheet comes from the host that serves the page itself.

### One request to GitHub
The header shows how many stars the source code repository has. To show that number, the page asks `api.github.com` once per visit. GitHub is also the company that hosts this website, see Section 4, so no additional party learns of your visit.

### Local Fonts
Fonts used on this website are standard system fonts. **No connection to Google Fonts servers is established** when you visit this page.

### Links
A link you click leaves this website, for example to Discord, to the source code or to a university portal. From then on the privacy policy of that site applies.

---

## 6. OSCAR Discord Bot

### 6.1 Purpose
OSCAR supports semester planning and provides module-related information within the Discord platform.

### 6.2 Processed Data

To provide its functionality, OSCAR processes the following data:

**A. Transient Data (Processed but not stored permanently)**
* **Message Content:** The bot reads messages only to identify the two operator commands `!ping` and `!resync`. Content not addressed to the bot is ignored, and no message is stored or logged.
* **Discord Display Names:** Used for temporary interaction but not logged.

**B. Persistently Stored Data (Database)**
* **Discord User ID:** A numerical identifier (e.g., `123456789...`) used to link your saved preferences to you.
* **Preferences:** Settings you explicitly save (e.g., study program, language, semester).
* **Semester Plan:** List of Module IDs you have added to your plan.
* **Feedback:** Text entries and ratings you explicitly submit via the feedback command.
* **Module Ratings & Reviews:** The stars, the difficulty and the optional text you submit with `/rate`. Other students see the rating and the text, without your name and without your ID.
* **Study Buddies:** The modules you opted in for with `/studybuddy`. Students who opted in for the same module can see your Discord account. Nobody else can, and leaving removes the entry.
* **Code Golf:** Your shortest solution per challenge and the language you named. The leaderboard shows the length and the language, not your name and not your ID.

**C. Log**
The bot writes a technical log: that it started, which commands it registered and which errors occurred. It does not record who used which command, and it does not contain your Discord User ID.

**We do not intentionally store:** Real names, email addresses, IP addresses of Discord users, or general chat logs.

### 6.3 Legal Basis
* **Art. 6(1)(b) GDPR:** Processing is necessary to provide the specific bot features you request via commands, for example saving your semester plan.
* **Art. 6(1)(a) GDPR (Consent):** What other students can see is only there because you put it there yourself: a review you write with `/rate`, a code golf entry, and your opt-in to `/studybuddy`. You withdraw it at any time by leaving the study group or by deleting your data with `/my_data`.
* **Art. 6(1)(f) GDPR (Legitimate Interest):** The technical log and the backups, which are needed to run the bot reliably and to repair it after a failure.

### 6.4 Recipients / Third Parties
* **Discord Inc.:** The bot runs on the Discord platform. Discord processes data according to their own policies.
* **Hosting:** The database, the log and the backups are stored on a server that the operator owns and runs himself, in Germany. No hosting company is involved, and only the operator has access.
* **Nobody else:** Your data is not sold, not shared and not used for anything but the features of the bot. The university does not receive it.

### 6.5 Data Retention
* **User Preferences, Semester Plan, Ratings, Study Buddies, Code Golf:** Stored until you delete your data with `/my_data`, or until this instance is shut down. The database and its backups are deleted when that happens.
* **Feedback:** Stored for up to **6 months** for quality evaluation, then anonymized or deleted. `/my_data` removes yours immediately, without waiting for that.
* **Backups:** A copy of the database is made every night and kept for **14 days**, readable by the operator only. Data you delete with `/my_data` is gone from the live database at once and from the last copy after 14 days.
* **Log:** At most 50 MB, older lines are overwritten.

---

## 7. Transfers to Third Countries
The OSCAR Bot operates on **Discord**. Discord Inc. is based in the USA. By using the Bot on Discord, you acknowledge that data (metadata, interaction logs) is processed on Discord's servers in the USA. This is governed by the [Discord Privacy Policy](https://discord.com/privacy).

This **documentation website** is hosted by GitHub, Inc. in the USA, see Section 4. The **database of the bot** stays in Germany.

---

## 8. Your Rights Under GDPR
You have the right to **Access, Rectify, Delete, Restrict processing, and Object** to the processing of your data.

* **Access and Delete, without asking anyone:** Run `/my_data` in Discord. It shows you
  everything the bot stores about you, hands it over as a file you can keep, and deletes
  all of it on request. The answer is only visible to you.
* **Rectify:** `/start` overwrites your programme, examination regulations, semester and
  language at any time.
* **For anything else:** Write to the **operator** (see Section 1). That includes data in a backup, which `/my_data` cannot reach and which is deleted after 14 days at the latest.

### Right to lodge a complaint
You have the right to lodge a complaint with a supervisory authority, in particular:

**State Commissioner for Data Protection Saxony-Anhalt** Otto-von-Guericke-Straße 34a, 39104 Magdeburg, Germany
Website: [https://datenschutz.sachsen-anhalt.de/](https://datenschutz.sachsen-anhalt.de/)

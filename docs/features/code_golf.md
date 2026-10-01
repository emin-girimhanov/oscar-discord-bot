# Weekly Code Golf Challenge

The **Weekly Code Golf Challenge** ([#53](https://isggit3.cs.ovgu.de/studium-lehre/discord-bot/-/issues/53)) brings competitive programming and code-minification fun directly into the FIN Discord community.

Every calendar week, OSCAR presents an algorithmic puzzle. The objective is classic code golf: **solve the problem using the fewest bytes of source code possible**.

---

## **Commands**

```bash
/codegolf [nummer] [rangliste]
/challenge [nummer] [rangliste]
```

### Parameters

* `nummer` *(optional, 1–10)*: Directly open a specific challenge from the archive.
* `rangliste` *(optional, True/False)*: Open directly in leaderboard view.

---

## **Key Features**

### 1. **Weekly Rotation & Archive**
* Challenges rotate automatically every calendar week using the standard ISO week number (`(iso_week - 1) % len(challenges)`).
* An interactive dropdown menu allows students to browse past and upcoming challenges from the archive at any time.

### 2. **Language Agnostic**
* Participants can submit solutions in any programming language: Python, C, C++, Rust, JavaScript, Haskell, Bash, APL, Brainfuck, etc.
* The modal form lets you specify your language alongside the code snippet.

### 3. **Byte-Count Measurement**
* Code size is calculated precisely as the number of **UTF-8 bytes**.
* Outer whitespace and surrounding markdown code blocks (e.g. ````python ... ````) are automatically stripped before counting.
* Every student has their personal best recorded. If you submit a shorter solution later, your record is updated automatically!

### 4. **Live Leaderboards**
* Each challenge features a real-time Top 10 leaderboard ranked by byte length in ascending order.
* Ties are broken by earlier submission timestamp.
* Top entries are honored with medals: 🥇 Gold, 🥈 Silver, 🥉 Bronze.

### 5. **Host Safety & Sandbox Decision**
* Running arbitrary user-submitted code inside the bot's host container would pose security and isolation risks.
* In accordance with the decision for Issue #53, OSCAR measures code size statically and provides peer-review and discussion channels. Students can share, review, and benchmark each other's solutions in community threads.

### 6. **Gamification & Badges**
* Submitting at least one solution to any challenge unlocks the **⛳ Code-Golfer** achievement badge, viewable in `/badges` and `/progress`.

### 7. **Privacy & GDPR Compliance**
* All code golf submissions are linked to your Discord user ID and fully exportable via `/my_data`.
* Deleting your account via `/my_data` wipes all your challenge submissions immediately from the database.

---

## **Challenge Catalog**

| # | Challenge ID | Title (DE) | Title (EN) | Goal |
|---|---|---|---|---|
| 1 | `fizzbuzz` | FizzBuzz Klassiker | Classic FizzBuzz | Print 1–100, replace multiples of 3 with 'Fizz', 5 with 'Buzz', both with 'FizzBuzz' |
| 2 | `palindrome` | Palindrom-Prüfung | Palindrome Checker | Check if a string reads the same forwards and backwards (ignoring case & spaces) |
| 3 | `fibonacci` | N-te Fibonacci-Zahl | N-th Fibonacci Number | Compute the $N$-th Fibonacci number for given $N$ via stdin |
| 4 | `primes` | Primzahlen bis N | Primes up to N | Output all prime numbers up to $N$ separated by spaces |
| 5 | `caesar` | Cäsar-Chiffre (ROT13) | Caesar Cipher (ROT13) | Shift alphabetic characters by 13 positions |
| 6 | `vowels` | Vokale zählen | Count Vowels | Count total vowels (a, e, i, o, u) in the input text |
| 7 | `collatz` | Collatz-Folge | Collatz Sequence Steps | Calculate steps to reach 1 in the $3n+1$ sequence |
| 8 | `anagram` | Anagramm-Prüfer | Anagram Checker | Check if two comma-separated words are anagrams |
| 9 | `rpn` | Reverse Polish Notation | Reverse Polish Notation | Evaluate arithmetic expression in postfix notation (+, -, *, /) |
| 10 | `roman` | Römische Zahlen | Roman Numerals | Convert an integer (1–3999) into Roman numeral string |

---

## **How to Submit a Solution**

1. Run `/codegolf` or `/challenge`.
2. Inspect the active weekly challenge, input/output format, and example test cases.
3. Click **⛳ Lösung einreichen / Submit Solution**.
4. In the pop-up modal, specify your programming language and paste your code.
5. Click **Submit**. OSCAR calculates the byte count and informs you immediately of your score and rank!

# Testing Guide: OSCAR-Bot

This document explains how we test OSCAR. As a beginner, we focus on the "Why" and "How" without diving too deep into the theory.

## What do we test? (Unit Tests)

We use **Unit Tests**. This means we break the bot down into its smallest parts (functions, classes) and check if these parts work correctly in isolation.

### Why do we do this?

1. **Safety**: If you change something in the code later, you'll immediately notice if you accidentally broke something old.
2. **Documentation**: Tests are like a manual. You can immediately see: "Ah, if I call this function with X, I expect Y".
3. **Debugging**: It's much easier to find a bug in a small function than to start the whole bot on Discord and hope the error occurs.

---

## What do we NOT test?

We do **not** test if Discord is online or if the internet is working. This is called "Integration Testing" and it's much more complex and slower.
To bypass this, we use **Mocks**.

---

## Core Concepts

### 1. Fixtures (Preparation)

A fixture is something that is prepared before a test. For example, a temporary database so we don't clutter our real database with test data.

**Example from `test_database.py`:**

```python
@pytest.fixture
def db(tmp_path):
    # Creates a fresh, empty database for each test
    db_path = str(tmp_path / "test.db")
    return Database(db_path=db_path)
```

### 2. Mocking (Dummies)

Since we don't want to establish a real connection to Discord (which would require a bot token and internet), we use "Mocks". These are small objects that pretend to be real Discord objects.

**Example from `test_ui_components.py`:**

```python
async def test_callback_calls_on_changed(self):
    callback = AsyncMock() # A "fake" function that remembers if it was called
    btn = ToggleButton(state=False, on_changed=callback)

    interaction = MagicMock(spec=discord.Interaction) # Pretends to be a Discord interaction

    await btn.callback(interaction) # We manually "press" the button in the test

    # We check if our dummy was called
    callback.assert_called_once()
```

---

## A Test in Detail

Let's look at a test in `test_database.py`:

```python
def test_creates_new_user(self, db):
    # 1. Action: We call the function we want to test
    db._check_user(99999)

    # 2. Verification: We check directly in the (test) database
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (99999,))

        # assert means: "We ensure that..."
        assert cursor.fetchone() is not None
```

## How do I run the tests?

We use `pytest`. Open your terminal and type:

```bash
uv run pytest
```

This runs all tests. If everything is green, everything is great! If something turns red, pytest shows you exactly which line the error is in.


---

## The check `pytest` cannot do

Every test above builds its modules by hand, and a module written by hand is always
well formed. The real table is not, and two crashes got past the whole suite:

| What broke | Why the tests missed it |
| :--- | :--- |
| `/suggest` raised `TypeError: '>' not supported between instances of 'NoneType' and 'int'` | 15 of the 410 rows send `Fachsemester` as null. No test module had a null field. |
| The result list of `/filter` crashed at `per_page=7` | It stood at 37 of the 40 components a view holds. No test counted it. |

So there is a second check that builds **every view against the live catalogue**:

```bash
python tools/smoke_views.py
```

It builds a card for five real modules, every standalone view, the result list over
the whole table, and it scores all 292 modules for a student with a semester set,
which is the path that crashed. Nothing asserts. It prints one line per view with its
component count, and the exit code is the number that failed.

```text
   ModuleView(100372)                       20 / 40
   SelectView                               30 / 40
   PaginatedModuleView (every module)       31 / 40
   SPlanView                                expected: ValueError when the student has not run /start yet
!! /suggest scoring all 292 modules         TypeError: '>' not supported ...
```

It needs the Nextcloud Tables API, so it is **not in the pipeline**. Run it:

* after changing a view,
* after changing how a module is read,
* when the module table changes, at the start of a semester.

## The other thing pytest cannot do: say how long it takes

```bash
python tools/benchmark.py
```

A discord interaction has **three seconds** before the student is told the application
did not respond. This prints how much of that each step spends, and marks anything over
50 ms. It found the one that mattered:

```text
  warm_cache()  the whole cold path               1615.1 ms  <-- slow
  ModuleView       the module card                   5.3 ms
  SuggestView                                       10.2 ms
  apply_selection  /filter end to end                6.5 ms
```

Reading the module table is a blocking request made from inside a command handler, so
a cold cache stopped the whole bot, not only that one command. `util.tables.warm_cache`
fills it before anybody asks, and `Oscar.keep_tables_warm` keeps it filled.

Numbers move with the network. Read the shape, not the figure: the cold line is a
request, every warm line is a dict lookup, and nothing in between should be slow.

A view that raises on purpose belongs in `EXPECTED` at the top of the script, with the
reason and the name of the caller that handles it.

### Why not make it a test?

Because a red pipeline that depends on somebody else's server is a pipeline people
learn to ignore. The unit tests stay offline and fast. This one is a thing you run.

# UI Migration: Tkinter → PySide6 (Qt 6)

> **For Claude Code.** This file tells you how to replace Instabot's whole Tkinter / ttkbootstrap GUI with a modern PySide6 desktop UI. Read it fully before you start, then work phase by phase (§8). Read `PROJECT_OVERVIEW.md` too: it documents every tab, bot method and DB table you will wire up.

---

## 1. Goal

Replace everything in `view/` and the window setup in `main.py` with a new PySide6 UI that:

1. Keeps **every existing feature and form field** (the parity list is in §6).
2. Looks modern: dark theme, sidebar navigation, cards, clear spacing, consistent widgets.
3. **Never freezes.** Every bot call runs off the GUI thread.
4. Adds what the old UI lacked: a **Jobs panel** (scheduled / running / finished jobs with status), a **live log panel** (the bots' `print` output), and a way to **cancel scheduled jobs**.

### Why PySide6
- Native desktop app, like today. No browser or server needed, and it runs next to the Selenium Chrome windows without conflict.
- Real threading support (`QThreadPool`, signals/slots), which this app needs because every job is long-running.
- Proper table views for Statistics, good dark styling through QSS, and an official LGPL license from the Qt Company.

---

## 2. Hard rules

- **Do not change bot logic** in `bot_folder/` or the SQL in `database/`, except for the small fixes this file lists explicitly. This task is the UI only.
- DB rows are read **by tuple index** (see the schema table in `PROJECT_OVERVIEW.md` §6.1). Keep using the same indexes, or wrap them in small helper functions in the UI layer. Do not change the schema.
- **Never call a bot method on the GUI thread.** Creating a bot opens Chrome, so the bot must also be **constructed** inside the worker, not in the GUI.
- Never touch Qt widgets from a worker thread. Workers talk to the GUI only through signals.
- Keep the old `view/` folder until the new UI reaches parity (Phase 5). Then delete it and remove `ttkbootstrap`.
- Don't commit `instabot.db`, `.env`, screenshots or drivers (already in `.gitignore`).
- Work on a branch (e.g. `ui/pyside6`), commit after each phase, and don't push or open a PR unless asked.

---

## 3. Dependencies

Update `requirements.txt`:

```
PySide6>=6.7
qtawesome>=1.3        # icons (Font Awesome / Material) for sidebar and buttons
webdriver-manager      # was missing
# keep: selenium==3.141.0, beautifulsoup4, requests, python-dotenv
```

Remove `ttkbootstrap` only in Phase 5. Also fix the README install line to `pip install -r requirements.txt`.

---

## 4. Target structure

```
main.py                     → loads .env (load_dotenv()), creates QApplication, applies theme, shows MainWindow
ui/
  app.py                    → create_app(): QApplication, Fusion style, font, theme
  main_window.py            → MainWindow: header, sidebar, QStackedWidget pages, jobs + log docks, status bar
  theme/
    dark.qss                → the whole stylesheet (colors as named constants at the top)
    palette.py              → color tokens used from Python (status colors, etc.)
  core/
    jobs.py                 → Job dataclass, JobManager (QObject), JobWorker (QRunnable)
    log_bridge.py           → redirects stdout/stderr into a Qt signal (still echoes to console)
    validators.py           → shared form checks (credentials, positive ints, proxy pairs, schedule)
    db_helpers.py           → small read helpers that name tuple indexes (e.g. account_username(row))
  widgets/
    account_picker.py       → AccountPicker: account combo + refresh button, emits account_changed(row)
    credentials_box.py      → username + masked password (auto-filled from the picked account)
    distribution_picker.py  → "Save users to distribution list" checkbox + list combo
    schedule_box.py         → ScheduleBox: "Schedule action" toggle, unit (Minutes/Hours/Days), value; .delay_seconds()
    proxy_box.py            → host + port (validated as both-or-neither)
    comment_input.py        → comma-separated comments with chips preview; .comments() -> list[str]
    user_list.py            → searchable list with a count label (used by Followers + DM pages)
    card.py                 → Card: titled QFrame used to group form sections
    toast.py                → small non-blocking success/error notification
  pages/
    hashtag_page.py
    location_page.py
    follow_followers_page.py
    followers_page.py       → unfollow center
    dm_page.py
    combination_page.py
    statistics_page.py
  dialogs/
    accounts_dialog.py
    settings_dialog.py
    inspect_settings_dialog.py
tests/
  test_ui_smoke.py          → pytest-qt smoke tests (§9)
```

Pages must only hold UI and call into `core/` and the existing `bot_folder/` / `database/` classes. Put repeated form logic in `widgets/`, not copied into each page (today every tab duplicates the same account/schedule/proxy code).

---

## 5. Look and layout

### Main window
```
┌──────────────────────────────────────────────────────────────────────────┐
│  Instabot                         [Account: ▾ my_account ] [⟳]  [⚙] [👤] │  header
├────────────┬─────────────────────────────────────────────────────────────┤
│ # Hashtag  │                                                             │
│ ⌖ Location │            current page (cards with forms)                  │
│ ⇄ Follow   │                                                             │
│   Followers│                                                             │
│ ✕ Unfollow │                                                             │
│ ✉ DM       │                                                             │
│ ★ Combine  │                                                             │
│ ▤ Stats    │                                                             │
├────────────┴─────────────────────────────────────────────────────────────┤
│ Jobs (2 running, 1 scheduled)  │  Log                                    │  bottom dock (collapsible, tabbed)
└──────────────────────────────────────────────────────────────────────────┘
 status bar: last event text · running job count
```

- **Sidebar** (`QListWidget` with qtawesome icons) switches a `QStackedWidget`. It replaces the old `ttk.Notebook`. Keep the same order as today: Hash Tag, Followers (label it "Unfollow"), Location, Follow Followers, DM, Combination, Statistics. Reorder only if it reads better, and keep all seven.
- **Global account picker in the header.** Today every tab has its own "Choose user" dropdown. Replace them with one header `AccountPicker`. When it changes, emit `account_changed(row)` and let every page refresh its account-dependent data (distribution lists, unfollow list, past-run boxes). Pages still show the username and a masked password, read-only, so the user sees which account will run.
- The menu bar's **Accounts / Settings / Inspect Settings / Exit** become header buttons (plus a normal `QMenuBar` with the same items and shortcuts: Ctrl+, for Settings, Ctrl+Q for Exit). Each opens a modal `QDialog`.
- Start maximized (`showMaximized()`), not full screen. Remember window size and the dock state with `QSettings`.
- The old static "status bar" placeholder becomes a real `QStatusBar` with the last event and the running job count.

### Theme
- `QApplication.setStyle("Fusion")`, then load `ui/theme/dark.qss`.
- Tokens (top of the QSS and in `palette.py`): background `#111318`, surface/card `#1A1D24`, raised `#232733`, border `#2E3340`, text `#E6E8EE`, muted text `#9AA1B2`, accent `#7C5CFF`, success `#2EBD85`, warning `#F5A524`, danger `#F04438`.
- Font: system UI font at 10–11pt. Page titles 18pt semibold, card titles 12pt semibold.
- Rounded corners (8px on cards and inputs), 12–16px padding inside cards, 16px gap between cards.
- One **primary button** per page (accent fill, e.g. "Run job"). Secondary buttons are outlined. Destructive buttons (Delete, Unfollow everyone, Clear list) are red and always ask for confirmation.
- Disabled widgets must look disabled (lower contrast), because many fields are conditionally enabled.
- Optional: a light theme (`light.qss`) and a toggle in Settings. Not required.

### Form behavior (applies to every page)
- Validate inline: a red border plus a one-line message under the field, instead of popup error boxes. Disable the primary button until the form is valid.
- Use `QSpinBox` for every count (posts, follows, skips, limits, likes) with sensible ranges, instead of free-text entries that need int checks.
- Conditional enabling, kept from today: the comment input only when COMMENT is checked; the distribution picker only when FOLLOW is checked; schedule inputs only when "Schedule action" is on.
- After a job is queued, show a toast ("HashTag job started for @user" or "Scheduled in 2h 30m") and keep the form filled.

---

## 6. Feature parity: page by page

Use this as a checklist. Bot calls and argument orders are in `PROJECT_OVERVIEW.md` §4–5. Check each call's signature in the code before wiring it.

### Accounts dialog (was `view/accounts.py`)
- Table of accounts (`QTableView`): Name, Phone, Username, Created, Last login. **Do not show passwords in the table.**
- Side form: Name, Phone, Username*, Password* (masked, with a show/hide eye button).
- Actions: Add (`Database.save_account`), Edit (select a row → loads the form → Save calls `update_account`), Delete (`delete_account`, confirm first).
- After any change, refresh the header `AccountPicker`.

### Settings dialog (was `view/settings.py`)
Use a `QTabWidget` or a left list inside the dialog, with sections:
1. **General:** Likes threshold, Posts threshold, Followers threshold (spin boxes), Headless (switch). Save through `Database.save_settings`. Keep the current rule: a field left at 0 keeps its old value. Show a note next to Likes threshold that it is not enforced by the bots yet.
2. **Distribution lists:** choose an account, a list of its groups, Add (`create_distribution_group`), Remove (`remove_group_from_distribution_list`, with confirmation).
3. **Proxies:** table + form (Host, Username, Password, Port), Save / Remove. Fix bug #5's inverted condition so Save works when the fields **are** filled. Show a note that proxies are not applied by the bots yet.
4. **Warm-up websites:** list + add/remove (`save_website` / `remove_website`).
- Handle the case where the settings row does not exist yet (bug #7): show defaults instead of crashing.

### Inspect Settings dialog (was `view/inspect_settings.py`)
Rebuild the same fields (block URLs, scroll box XPath, like-button XPaths, "page not available" / "user not found" texts) as a clean form. It stays a stub: label it "Coming soon", with the Save button disabled. Don't implement saving.

### Hashtag page
- Fields: hashtag, number of posts, action toggles LIKE / FOLLOW / COMMENT (at least one required), comments (when COMMENT is on), distribution list (when FOLLOW is on), schedule, proxy.
- Run → `HashTagBot(username, password, False, proxy_dict).search_hash_tag(...)` as a job.

### Location page
- Same as Hashtag, but the input is a **location URL** (validate that it contains `instagram.com/explore/locations/`). Show the "location name" field disabled with a "Not available yet" hint.
- Run → `LocationBot.search_location_by_url(...)`. Don't wire `search_location_by_name` (it is broken, bug #19).

### Follow Followers page
- Two cards side by side, or a segmented toggle: **"Follow their followers"** (`follow_after_followers`) and **"Follow who they follow"** (`follow_after_following`).
- Shared: target profile URL, number to follow (>0), number to skip, distribution list, schedule, proxy.
- **Past runs** card: a table from `FollowFollowersDB.get_account_data(account)` with Date, Follow, Failed, Skip, URL.

### Unfollow page (was the "Followers" tab, `view/tab_followers.py`)
Split it into three clear cards:
1. **Who doesn't follow me back:** Run → `FollowersBot.get_unfollowers()` **as a job** (fixes bug #18, the GUI freeze). Show the results in a searchable `user_list` with a count, plus "Open profile" (the old SEARCH) and a "Unfollow all N" button → `unfollow_users(...)`. Fix the bad `len()` on an int in the error message.
2. **Users the bot followed** (the `unfollow` table for the current account): searchable list with a count. Actions: Remove from list (DB only), Unfollow selected (`unfollow_user`), Unfollow whole list (`unfollow_users`), Unfollow only non-followers-back (`unfollow_users_who_not_return_follow` then `unfollow_users`; pass the missing `remove_not_found_users` argument, bug #17). Options: Limit (spin box), Remove not-found users (checkbox), Reverse order (checkbox), schedule.
3. **Unfollow everyone** (danger zone, red border): limit spin box + button → `unfollow_all_users(limit)`, with a confirmation that names the account.

### DM page
- Distribution list picker for the current account; members shown in `user_list` with a count.
- Message: multi-line `QPlainTextEdit` with a character count. Message limit spin box (`limit_msg`). Schedule.
- Send → `DM(..., True, proxy_dict).send_message_to_distribution_group(...)` as a job.
- Clear list / Remove selected user: fix bug #15 (create a `DMDB()` instance instead of calling the method on the class).
- **Message my followers** card: fix the missing `proxy_dict` in the UI call (bug #14, UI side). The bot side of #14 (wrong arguments in `send_message_to_following_list`) is a bot bug. Leave the button disabled with a "Not working yet" hint unless you are asked to fix the bot.

### Combination page
- Source: a segmented toggle **Hashtag | Post URL** (enforces exactly one, instead of today's check).
- Fields: likes per followed user (≥0), users to follow (>0), skip posts, skip users, distribution list, schedule. Drop the hard-coded dummy proxy. Pass the same values the old tab passed, so behavior doesn't change.
- Show an info line: "Follows about 100 users over 12 hours, then unfollows them all, and repeats."
- Past runs card from `CombinationDM.get_account_data(account)`.

### Statistics page
- A sub-navigation (tabs or a segmented control): HashTag, Location, Follow Followers, DM, Follow back, **Combination** (new; data from `CombinationDM.get_combination_data()`).
- Each one is a `QTableView` backed by a small `QAbstractTableModel` with **named column headers** taken from the schema table (no more raw tuples). Sortable, with a filter box and an "only current account" toggle.
- Refresh button, plus an automatic refresh when a job finishes.

---

## 7. Jobs, threading and logs (`ui/core/`)

### JobManager
```python
@dataclass
class Job:
    id: int
    kind: str            # "HashTag", "Location", "Unfollow", ...
    account: str
    description: str     # e.g. "#sunset · 50 posts · like+follow"
    status: str          # "scheduled" | "running" | "done" | "failed" | "cancelled"
    run_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
```
- `JobManager(QObject)` has signals `job_added`, `job_updated`, `job_finished`.
- `submit(kind, account, description, fn, delay_seconds=0, on_result=None)`. `fn` is a callable that **builds the bot and runs the method** (a lambda or closure). With a delay, use a `QTimer.singleShot`, or a 1-second ticker that updates a countdown. At run time, hand it to `QThreadPool.globalInstance()` as a `JobWorker(QRunnable)`.
- `ScheduleBox.delay_seconds()` must return the same value as `ScheduleCalc().calc_schedule_time(unit, minutes, hours, days)`, so schedules behave as before.
- `cancel(job_id)`: works for **scheduled** jobs. For running jobs, offer "Stop": call `bot.driver.quit()` on the bot instance the worker stored. The bot's own `try/except` then ends the run. Mark the job "cancelled" and warn in the confirm dialog that the run is stopped abruptly.
- Results (for example, the unfollowers list) go back through `on_result`, connected by a signal, so the GUI updates on the main thread.
- Set the pool's max thread count high enough (e.g. 8), so several accounts can run in parallel as today.

### Jobs panel
A table in the bottom dock: status chip (colored), kind, account, description, run at / countdown, duration, and an actions column (Cancel / Stop). Double-click a row to filter the log to that job.

### Log bridge
- Replace `sys.stdout` / `sys.stderr` with a small writer that emits `text_written(str, thread_name)` and also writes to the original stream.
- Name each worker thread `job-<id>` (`threading.current_thread().name = ...` at the start of `run`), so log lines can be tagged by job.
- Log panel: read-only `QPlainTextEdit`, monospace font, a timestamp on each line, a job filter dropdown, Clear, Copy, auto-scroll, and a cap of about 5,000 lines.
- Lines that contain "block" go to the danger color, and also show a toast ("@user may be blocked, job stopped").

### main.py
```python
from dotenv import load_dotenv
load_dotenv()               # .env was never loaded before (Mailgun vars)
from ui.app import run
if __name__ == "__main__":
    run()
```
Before the window opens, make sure the `screen_shots/` folder exists (`os.makedirs(..., exist_ok=True)`, bug #22). This small fix is allowed.

---

## 8. Phases

Commit at the end of each phase. Run the smoke tests (§9) before each commit.

1. **Shell.** Dependencies, `ui/app.py`, `MainWindow` with sidebar, empty pages, header account picker, theme, docks, `main.py` switched to the new UI (the old UI stays available through `python -m view.legacy` or by keeping the old `main.py` as `main_tk.py` until Phase 5).
2. **Core.** `JobManager`, `JobWorker`, log bridge, Jobs panel, Log panel. Test it with a fake job (`time.sleep` + prints) before using real bots.
3. **Shared widgets and dialogs.** All `widgets/`, Accounts, Settings, Inspect Settings.
4. **Feature pages.** Hashtag → Location → Follow Followers → Combination → DM → Unfollow → Statistics. Tick off §6 for each one.
5. **Cleanup.** Delete `view/` and `main_tk.py`, remove `ttkbootstrap` from imports and requirements, update the README (screenshot + run steps), and update `PROJECT_OVERVIEW.md` §3–4 to describe the new UI.

---

## 9. Testing and done criteria

- Add `pytest` and `pytest-qt` as dev dependencies. Run tests with `QT_QPA_PLATFORM=offscreen`.
- `tests/test_ui_smoke.py` should:
  - start `MainWindow` against a temporary SQLite file (chdir to a tmp dir, since the DB path is `instabot.db` in the working directory),
  - open every page and every dialog without errors,
  - check form validation (e.g. the Run button is disabled without a hashtag; COMMENT without comments is invalid),
  - submit a **fake** job through `JobManager` (monkeypatch the bot class, so Chrome never opens) and check that it goes scheduled/running → done and its prints reach the log panel,
  - check that `ScheduleBox.delay_seconds()` equals `ScheduleCalc().calc_schedule_time(...)` for each unit.
- Never open real Chrome or log into Instagram in tests.

**Done when:**
- [x] Every item in §6 works and the old `view/` folder is gone.
- [x] No action freezes the window (try resizing while a job runs).
- [x] Jobs panel shows every job's live status; scheduled jobs can be cancelled.
- [x] Bot output appears in the Log panel.
- [x] Passwords are masked everywhere in the UI.
- [x] Smoke tests pass, and `python main.py` starts on a fresh clone with an empty DB.
- [x] README and `PROJECT_OVERVIEW.md` are updated.

---

## 10. Out of scope

Don't do these unless asked; list them in the final summary as follow-ups:
- Migrating Selenium 3 → 4, or updating Instagram selectors.
- Applying proxies in the bots, or fixing bot-side logic bugs (#9–#13, #16, #19, #20).
- Encrypting stored passwords or parameterizing SQL (#23, #24). Recommended next steps, but separate work.
- Implementing the Inspect Settings editor.

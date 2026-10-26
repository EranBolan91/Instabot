# Instabot — Full Project Reference

> **Purpose of this document:** a complete, self-contained description of the Instabot codebase so an AI assistant (or a new developer) can understand every feature, module, class and function without reading the source first. Its sections are: what the app does → architecture → each layer in detail → database schema (with tuple indexes, since the code reads rows by position) → cross-cutting behavior → known bugs and limitations.
>
> Last updated 2026-10-25, after the move from Tkinter to PySide6 (see `UI_MIGRATION.md`) and the move of every Instagram selector into `utils/instagram_selectors.json`.

---

## 1. What the project is

Instabot is a **desktop GUI application written in Python** that automates actions on Instagram through a real Chrome browser driven by **Selenium**. The user stores one or more Instagram accounts locally, picks one in the window's header, and starts automation **jobs** from the pages in the sidebar:

- Like / comment on / follow posts found through a **hashtag**
- Like / comment on / follow posts found through a **location URL**
- Follow the **followers** or **following** list of another user
- Follow users who **liked a post** (the "Combination" feature, with automatic unfollow cycles)
- Find who **doesn't follow you back**, then unfollow them
- **Unfollow** users the bot followed earlier (tracked in the DB), or unfollow everyone
- Send **direct messages (DMs)** to "distribution lists" of users the bot collected
- **Schedule** any of these jobs to start after X minutes, hours or days
- See **statistics** of past runs

Every job runs in the background with its own Chrome window. The **Jobs** panel shows each job's status and can stop it, and the **Log** panel shows what the bots print.

Everything is stored in a local **SQLite** database file, `instabot.db`, created automatically in the working directory.

### Tech stack
| Concern | Library |
|---|---|
| GUI | `PySide6` (Qt 6) with a dark QSS theme, `qtawesome` icons |
| Browser automation | `selenium==4.51.0` (Selenium 4 API: `find_element(By.XPATH, ...)`, etc.) |
| Chrome driver install | Selenium Manager (built into Selenium 4) downloads the driver that matches the installed Chrome |
| Finding things on Instagram | `utils/instagram_selectors.json`, read through `utils/instagram_selectors.py` (see §8) |
| HTML parsing | `beautifulsoup4` (imported, no longer needed by the bots) |
| Storage | `sqlite3` (standard library) |
| Error e-mails | `requests` → Mailgun HTTP API |
| Config | `python-dotenv` (`.env` is loaded by `main.py`) |
| Concurrency | `QThreadPool` + `QRunnable` jobs (`ui/core/jobs.py`) |
| Tests | `pytest` + `pytest-qt` (`requirements-dev.txt`) |

It runs on Python 3.12+ (developed on 3.14).

### How to run
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```
Tests: `.venv/bin/pip install -r requirements-dev.txt`, then `.venv/bin/python -m pytest`. They run offscreen against a temporary database and never open Chrome, except `tests/test_instagram_selectors.py`, which uses headless Chrome on local HTML copies of Instagram's pages, never the real site.

---

## 2. Architecture overview

The project follows a loose **MVC-like layered structure**:

```
main.py                      → entry point: loads .env, creates screen_shots/, starts the Qt app
ui/                          → PySide6 GUI
    app.py                   → QApplication setup, theme, log bridge, run()
    main_window.py           → MainWindow: header, sidebar, pages, Jobs + Log docks, dialogs
    core/                    → jobs, log bridge, validators, DB tuple helpers (no widgets)
    widgets/                 → reusable widgets (forms, pickers, tables, panels)
    pages/                   → one page per feature (sidebar entries)
    dialogs/                 → Accounts, Settings, Inspect Settings
    theme/                   → dark.qss + palette.py (color tokens), icons/ (app.png + stylesheet icons)
bot_folder/                  → Selenium bots (business logic, one per feature)
    main_bot.py              → InstagramBot base class (shared browser helpers)
database/                    → SQLite access layer
    db.py                    → Database base class (creates all tables, shared queries)
    <feature>/<feature>.py   → per-feature DB subclasses (save / read stats)
models/                      → plain data classes (DTOs) passed to the database layer
utils/                       → Instagram selectors (JSON + lookup code), selector check, helpers
tests/                       → pytest-qt tests
```

### Typical data flow of a job
1. The user picks an account in the header's **Account** dropdown. Every page fills its username/password from the `accounts` table and reloads that account's lists and past runs.
2. The user fills a page's form. Each field is checked as the user types, and the Run button stays disabled until the form is valid.
3. On Run, the page reads every value **now** (so later edits can't change a queued job) and calls `JobManager.submit(kind, account, description, make_bot, run, delay_seconds, on_result)`.
4. The job waits as **scheduled** if it has a delay, then **queued**, then **running** on a worker thread. There, `make_bot()` creates the bot (e.g. `HashTagBot(username, password, False, proxy_dict)`), which opens Chrome. Then `run(bot)` calls the bot method.
5. The bot logs in (`_login`), navigates Instagram, finds elements through the selectors (`S.click(driver, "post.like_button")`), performs actions with randomized and progressive sleeps, and saves every followed user to the `unfollow` table (and optionally to a distribution list).
6. Everything the bot `print`s appears in the **Log** panel, tagged with its job. Lines that mention a block also show a red toast.
7. When the job finishes, the bot builds a **model** object (e.g. `Hashtag`) and saves it through the matching **DB class** (e.g. `HashtagDB().save_in_db`). The Statistics page and the pages' "Past runs" tables refresh by themselves.
8. If Instagram blocks the account, the bot takes a screenshot (`screen_shots/<username>.png`), e-mails it through Mailgun, and stops.

### Constructor convention
Every bot inherits `InstagramBot(username, password, is_mobile, proxy_dict)`.
- `is_mobile=True` → Chrome with mobile emulation ("Nexus 5") and the options below (used by the DM bot).
- `is_mobile=False` → desktop Chrome. The options are **not passed** here (known issue #4).
- Both start with `webdriver.Chrome(options=options)`; Selenium Manager finds the matching ChromeDriver.
- `proxy_dict = {"proxy": ..., "port": ...}` is accepted everywhere but **never used** (known issue #5).

---

## 3. Entry point and main window

### `main.py`
Calls `load_dotenv()`, creates `screen_shots/` (the bots fail without it), and calls `ui.app.run()`.

### `ui/app.py`
- `create_app()`: creates the `QApplication` (or reuses the existing one) and calls `configure_app`.
- `configure_app(app)`: sets the app name, the Fusion style, the font, the dark palette and the app icon (`ui/theme/icons/app.png`, the camera shown on the window and dialogs). It then loads `ui/theme/dark.qss`, replaces its color tokens and `@icons` path, and applies it. It is idempotent: it marks the app with the `instabot_configured` property.
- `run()`: installs the `LogBridge`, shows `MainWindow`, runs the event loop. If bot threads are still alive after the window closes (a Chrome that wouldn't quit), it ends the process with `os._exit` so it doesn't hang.

### `ui/main_window.py` — `class MainWindow`
- **Menu bar:** *Main* → Accounts… · Settings… (Ctrl+,) · Inspect Settings… · Exit (Ctrl+Q). *View* → show/hide the Jobs and Log docks.
- **Header:** the app name, the **AccountPicker** (account dropdown + refresh), and buttons for Accounts and Settings. Changing the account calls `set_account(row)` on every page.
- **Sidebar** (same order as the old tabs): Hashtag, Unfollow, Location, Follow Followers, DM, Combination, Statistics. Each opens its page in a `QStackedWidget`.
- **Docks** (bottom, tabbed): **Jobs** (`JobsPanel`) and **Log** (`LogPanel`). Double-clicking a job shows only its log lines.
- **Status bar:** the last job event ("#3 HashTag @user finished") and "N running".
- **Toasts:** short pop-up messages for job start, success and errors, and for "@user may be blocked".
- Dialogs open with `_open_dialog` (non-blocking `open()`, deleted on close). Inspect Settings gets the job manager and the current account, so it can run the selector check.
- Window size, dock layout, the last page and the last account are saved with `QSettings` and restored on start (maximized on first start).
- Closing while jobs are active asks "Quit anyway?" and then stops them (closes their Chrome windows).

---

## 4. GUI layer (`ui/`) — every page, dialog and widget

### 4.1 Core (`ui/core/`)
- **`jobs.py`**
  - `Job` dataclass: id, kind, account, description, status, run_at, started_at, finished_at, error.
  - Statuses: `scheduled` → `queued` → `running` → `done` / `failed` / `cancelled`.
  - `JobManager(QObject)`: `submit(...)`, `cancel(id)` (a scheduled job), `stop(id)` (a running job: calls `bot.driver.quit()`), `shutdown()`, `clear_finished()`, `get(id)`, and running/scheduled/active counts. Signals: `job_added`, `job_updated`, `job_finished`, `job_removed`.
  - At most 8 jobs run at the same time (`MAX_PARALLEL_JOBS`). A 1-second timer starts scheduled jobs when they're due.
  - `JobWorker(QRunnable)`: runs `make_bot()` and `run(bot)` in a thread named `job-<id>`, and always quits the driver at the end.
- **`log_bridge.py`** — `LogBridge`: replaces `sys.stdout` / `sys.stderr` with writers that still echo to the console and also emit `(text, thread name, is_error)`. The Log panel uses the thread name to know which job printed a line.
- **`validators.py`**: shared form checks that return an error text or `None`, `required`, `no_spaces`, `no_apostrophe` (an apostrophe breaks some SQL queries, known issue #23), `http_url`, `positive`, `unique`, `proxy_pair`, `instagram_url`, `instagram_location_url`, `hashtag`, and `first_error` to combine them.
- **`db_helpers.py`**: names for the tuple indexes of DB rows (`account_id(row)`, `account_username(row)`, `account_password(row)`, `account_created(row)`, `group_id(row)`, `group_name(row)`, …) and `as_int`.

### 4.2 Widgets (`ui/widgets/`)
| Widget | What it is |
|---|---|
| `AccountPicker` | Header account dropdown + refresh button. Emits `account_changed(row)`. |
| `Card` | A titled box that groups form sections (`DangerCard` gives it a red border). |
| `FormField` / `FormValidator` (`form.py`) | A label + input + help/error line. The validator shows errors only after a field was touched, and enables the bound Run button only when every check passes (`add`, `add_check`, `watch`, `bind`, `touch_all`, `reset`, `revalidate`). |
| `CredentialsBox` | Read-only username + masked password of the current account. |
| `DistributionPicker` | "Save users to a distribution list" checkbox + the account's lists. `selected_group()` → `(group_id, group_name)`. |
| `ScheduleBox` | "Schedule this job" toggle, unit (Minutes / Hours / Days) and value. `delay_seconds()` uses `ScheduleCalc`. |
| `ProxyBox` | Host + port, both or neither. `proxy_dict()`. Notes that the bots don't use it yet. |
| `CommentInput` | Comma-separated comments with a chip preview. `comments()` → list. |
| `PostActions` | Like / Follow the author / Comment checkboxes, the comment input, and the distribution picker (enabled only with Follow). |
| `Segmented` | A two-or-more-option toggle (e.g. "Hashtag \| Post URL"). |
| `UserList` | A searchable list of usernames with a count. Double-click opens the profile in the user's browser. |
| `RecordsTable` | A sortable, searchable table of DB rows with named columns (dates, numbers, yes/no) and an "only this account" filter. |
| `JobsPanel` | Table of jobs: #, kind, account, description, status, start time, duration, and a Cancel / Stop button. "Clear finished". |
| `LogPanel` | Colored log lines (errors red, blocks highlighted) for all jobs or one job, with Clear and Copy. Keeps the last 5000 lines. Emits `block_detected`. |
| `Toast` | A small, non-blocking message that hides itself after a few seconds. |
| `confirm.ask(...)` | A yes/no confirmation for destructive actions. |
| `FlowLayout` | A wrapping layout (used for comment chips). |

### 4.3 Pages (`ui/pages/`)
`BasePage` gives every page a title, a subtitle and a scrollable body. `JobPage(BasePage)` adds the shared parts of the pages that run a bot: the Account card, the Run card (schedule, proxy and the Run button), the validator, `login()` → `(username, password, proxy_dict)`, `submit(...)`, `is_schedule()`, and a refresh hook when one of the account's jobs finishes. In spin boxes, 0 means "No limit" and is passed to the bots as `-1` (`limit_arg`).

#### Hashtag (`hashtag_page.py`)
Fields: hashtag (with or without `#`), number of posts, actions (at least one of Like / Follow / Comment; comments required when Comment is on; distribution list when Follow is on), schedule, proxy.
Run → `HashTagBot(...).search_hash_tag(hashtag, amount, like, comment, follow, split_comment, to_distribution, group_name, group_id, is_schedule)`.

#### Unfollow (`followers_page.py`, the old "Followers" tab)
Three cards:
1. **Who doesn't follow me back:** "Find who doesn't follow me back" → `FollowersBot.get_unfollowers()` as a job. The result list has "Open profile" and "Unfollow all N" (`unfollow_users(users, 0, …)`).
2. **Users the bot followed** (the `unfollow` table for this account): Remove from list (DB only), Unfollow selected (`unfollow_user`), Unfollow whole list (`unfollow_users(users, 1, …)`), Unfollow only those not following back (`unfollow_users_who_not_return_follow`, then `unfollow_users` on its result). Options: Unfollow at most N, Remove users that no longer exist, Newest first.
3. **Unfollow everyone** (red card): `unfollow_all_users(limit)`, after a confirmation that names the account.
The schedule applies to the unfollow buttons. The "find" check always starts right away.

#### Location (`location_page.py`)
Same as Hashtag, but the input is a **location URL** that must contain `instagram.com/explore/locations/`. The "search by name" field is disabled ("Not available yet", known issue #19).
Run → `LocationBot.search_location_by_url(url, amount, like, follow, comment, …)`. Note the argument order: like, **follow, comment**.

#### Follow Followers (`follow_followers_page.py`)
A toggle: **Their followers** (`follow_after_followers`) or **Who they follow** (`follow_after_following`). Fields: profile address, number to follow, skip the first N (only used by "Who they follow"), distribution list, schedule, proxy. A **Past runs** table comes from `FollowFollowersDB.get_account_data(account)`.

#### DM (`dm_page.py`)
- **Recipients:** the account's distribution lists and the chosen list's members (`get_users_from_dm_users`), with Remove user and Clear list.
- **Message:** a multi-line text with a character count, and "Send at most N".
- Run → `DM(username, password, True, proxy).send_message_to_distribution_group(message, dm_users, list_name, is_schedule, True, account_id, group_id, limit)`. The members are read when the job starts, so a scheduled job uses the current list.
- **Message my followers** is shown disabled ("Not working yet", known issue #14).

#### Combination (`combination_page.py`)
"Follows about 100 users over 12 hours, then unfollows them all, and repeats."
Source toggle **Hashtag | Post URL**. Fields: users to follow, posts to like per followed user, skip posts, skip users (not used by the bot), distribution list (not used by the bot, #12). No proxy.
Run → `CombinationBot.combination(hashtag, url, likes, follow, distribution, 0, group_name, group_id, skip_posts, skip_users)`. A Past runs table comes from `CombinationDM.get_account_data`; each finished run adds a row.

#### Statistics (`statistics_page.py`)
Tabs: HashTag, Location, Follow Followers, DM, Follow back, Combination. Each is a `RecordsTable` with named columns from the schema in §6.1, searchable, sortable, with an "only the current account" filter. Refresh button, plus an automatic refresh whenever a job finishes.

### 4.4 Dialogs (`ui/dialogs/`)
- **Accounts** (`accounts_dialog.py`): a table of accounts (Name, Phone, Username, Created, Last login; **passwords are not shown**) and a form (Name, Phone, Username*, Password* with a show/hide button). Add (`save_account`), Edit → Save (`update_account`), Delete (`delete_account`, after a confirmation). The header's account list refreshes after any change.
- **Settings** (`settings_dialog.py`), four tabs:
  1. *General:* likes / posts / followers thresholds and Headless. Saved with `save_settings`; a field left at 0 keeps its old value. If the settings row doesn't exist yet (no account added), it shows defaults. It notes that the likes threshold isn't enforced and that desktop Chrome ignores Headless.
  2. *Distribution lists:* pick an account, add a list (`create_distribution_group`) or remove one (`remove_group_from_distribution_list`, after a confirmation).
  3. *Proxies:* a table and a form (Host*, Port*, Username, Password) → `Proxy.save_in_db` / `remove_from_db`. It notes that the bots don't apply proxies.
  4. *Warm-up websites:* a list of URLs (`save_website` / `remove_website`).
- **Inspect Settings** (`inspect_settings_dialog.py`): the editor for `utils/instagram_selectors.json`.
  - *Selectors* tab: a tree of every selector grouped by page, with its status ("Last seen working on <date>", "educated guess" when it was never checked, or "needs fixing" after a failed check). It also has a table of its ways (type + value) with Add, Remove, Up and Down.
  - *Addresses and texts* tab: the URLs (`home`, `login`, `profile`, `hashtag`) and the texts (`row_button_texts`, `default_avatar_file`, `restriction_urls`).
  - Save / Revert. Bots see saved changes right away. It asks before closing with unsaved changes.
  - **Check selectors:** with the current account, runs a job that logs in with a real `InstagramBot` and calls `utils.selector_check.check_selectors` (read-only: it never follows, unfollows, likes, comments or sends). It then stores today's date on every selector it found (`mark_checked`) and lists the missing ones.

---

## 5. Bot layer (`bot_folder/`) — every class and function

No bot contains a raw XPath, CSS or class name any more. They find everything through `S` (`utils/instagram_selectors.py`) by key, e.g. `S.click(self.driver, "profile.following_button")`. The keys are listed in §8.

### 5.1 `bot_folder/main_bot.py` — `class InstagramBot` (base class)
Holds a `db.Database()`, the credentials, `base_url = 'https://www.instagram.com'` and the Selenium `driver`.

**`__init__(username, password, is_mobile, proxy_dict)`** builds Chrome options: no-sandbox, disable GPU and notifications, `--headless` if `settings.headless`, and either the "Nexus 5" mobile emulation (mobile) or a fixed desktop user-agent (desktop). Page load strategy is `eager` (`options.page_load_strategy`). It then starts Chrome with `webdriver.Chrome(options=options)`; Selenium Manager supplies the matching driver.
It also sets `self.wait = WebDriverWait(driver, 7)`.

| Method | What it does |
|---|---|
| `get_username()` / `get_password()` | Getters. |
| `_login()` | Visits a random site from the `website` table (if any), opens `S.url("login")`, types into `login.username_input` and `login.password_input` + Enter, then returns `is_login_successful()`. On success it calls `_dismiss_popups()`. |
| `is_login_successful()` | For up to 15 s: `True` when `login.logged_in_marker` (the Home icon) shows up. `False` on `login.error_message` (wrong password), or on a restriction/challenge URL (Instagram wants a security check). |
| `_dismiss_popups()` | Clicks "Not now" (`login.not_now_button`) up to twice ("Save your login info?", notifications). |
| `_nav_user(user)` | Opens `S.url("profile", username=user)`. |
| `_nav_user_new_tab(username)` | Opens the profile in a new tab via JS `window.open`. |
| `_like_post()` | Clicks `post.like_button`, which only matches the post's own heart while it isn't liked, so it never unlikes. Screenshots on failure. |
| `_get_like_amount_text()` | Reads the post's like count from `post.likes_link`. Unused, because the likes threshold is disabled. |
| `_comment_post(split_comment)` | Picks a random comment, clicks `post.comment_input`, types it + Enter. |
| `_follow_user(to_distribution, group_id)` | On an open post: finds `post.author_follow_button` (only there while you don't follow the author) and the author (`post.author_link`). If the author has a profile picture and at least `settings.amount_followers` followers, it clicks Follow, saves the user to `unfollow` and optionally to a distribution group. |
| `_unfollow_user(username, user_id)` | Logs in, opens the profile, clicks `profile.following_button` → `profile.unfollow_confirm` (or `profile.requested_button` → the confirm popup), and removes the user from the `unfollow` table. |
| `_popup_unfollow()` | Clicks `profile.unfollow_confirm` if it shows up within 3 s. |
| `_user_not_found_broken_link()` | `True` if the page shows `profile.not_found_title` ("Sorry, this page isn't available."). |
| `_check_if_blocked()` | `True` if the URL contains one of `restriction_urls`, or the `block.popup` is shown. |
| `_get_followers_number(username)` | Opens the user in a 2nd tab, checks `_has_profile_image()`, reads the post and follower counts, closes the tab. **Always returns `(followers, has_image, posts)`**; `-1` means unknown (the counts are only read when the user has a picture). |
| `_has_profile_image()` | Compares the `profile.picture` `src` with `texts.default_avatar_file`. Returns **`-1` when the user HAS a real picture** (the result of `str.find`), a number ≥ 0 for the default avatar, and `None` if no picture element was found. |
| `_check_if_follow_back()` | If `profile.follow_back_button` appears, clicks it and returns `True`. |
| `_get_usersname()` | Scrolls the open list (`dialog.scroll_area`) to the end and returns `[(username,), ...]` (`S.dialog_rows`). |
| `_screen_shot(username)` | Saves `screen_shots/<username>.png`. |
| `_send_email(username, success_posts, time, section)` | Sends an error e-mail with the screenshot attached through the Mailgun API, using env vars `MAILGUN_DOMAIN`, `MAILGUN_API` and `ALERT_EMAIL` (sender and recipient). Sends nothing if any is missing. |
| `_blocked_action_popup()` | Waits up to 4 s for `block.popup`. If it appears: screenshot, click `block.popup_ok`, return `True`. |
| `global_block_message(username, section)` | Prints "User … has been blocked" (the Log panel highlights it and shows a toast). |
| `global_complate_task(username, section, results)` | Prints a task-complete message. Unused. |
| `is_post_liked()` | If the post is liked (`post.unlike_button`), clicks it to unlike. Unused. |
| `skip_posts(n)` | Clicks `post.next_button` `n` times. |
| `save_account_action(account_action)` | Saves to `account_actions`. |
| `get_post_amount()` | The open profile's posts counter, as text. |
| `check_current_url()` | Returns `driver.current_url`. |

### 5.2 `bot_folder/hash_tag/hash_tag_bot.py` — `class HashTagBot(InstagramBot)`
- **`search_hash_tag(hash_tag, amount, like, comment, follow, split_comment, to_distribution, group_name, group_id, time_schedule)`**
  1. Logs in, opens `S.url("hashtag", tag=...)` (Instagram now redirects this to a search grid) and clicks `grid.first_post`.
  2. Repeats `amount` times: optionally like / comment / follow (`_follow_user`), then clicks `post.next_button`.
  3. **Throttling:** every `TIME_SLEEP` (5) posts it sleeps `loops * 5` seconds, so the pauses grow (0s, 25s, 50s…). The counter resets when `i*5 == 500`.
  4. After each post it checks `_check_if_blocked()`. If blocked: screenshot, e-mail, close the browser, stop.
  5. `finally`: saves stats (`_prepare_data_for_db`), deletes cookies, closes the browser.
  - The likes threshold check is replaced by a placeholder `if int(20) > int(0):` (always true, #11).
- **`_prepare_data_for_db(...)`**: saves a `Hashtag` row and an `AccountActions` row ("HashTag", amount, successes).

### 5.3 `bot_folder/location/location_bot.py` — `class LocationBot(InstagramBot)`
- **`search_location_by_url(url, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id, time_schedule)`**: the same loop as the hashtag bot, on the location URL. It has no block check. Saves a `Location` stats row.
- **`search_location_by_name(...)`**: types the name into `search.input` and loops. Incomplete: no login, and it calls `_follow_user()` without arguments (#19). Not wired in the UI.
- **`_search_entry(name)`**: types into the search input.
- **`_prepare_data_for_db(...)`**: saves a `Location` row.

### 5.4 `bot_folder/follow_followers/follow_followers_bot.py` — `class FollowFollowersBot(InstagramBot)`
- **`follow_after_followers(user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule, num_skip)`**: logs in, opens the target profile, clicks `profile.followers_counter`, then scrolls the list and reads it row by row (`S.dialog_rows`), keeping a set of usernames already looked at. For each row whose button says "Follow", where the user has a profile picture and at least `settings.amount_followers` followers, it clicks Follow, saves the user to `unfollow` (and the distribution list), checks the blocked popup, and uses the progressive sleep. It skips the bot's own username, stops after `num_of_following` follows, and stops after 3 scrolls with no new rows (end of the list). It ignores `num_skip`.
- **`follow_after_following(...)`**: the same for `profile.following_counter`, but it scrolls the full list first, then starts at row `num_skip`.
- **`_prepare_data_for_db(...)`**: saves a `FollowFollowers` stats row.

### 5.5 `bot_folder/followers/followers_bot.py` — `class FollowersBot(InstagramBot)`
- **`get_unfollowers()`**: logs in, reads the account's own *following* and *followers* lists (`_get_names`) and returns `following − followers`. As a sanity check, the number of followers it read must be close to the profile's follower count (within +10). Otherwise it returns `False`.
- **`_get_names()`**: scrolls the open list to the end, collects the usernames (`S.dialog_rows`), and closes it (`dialog.close_button`).
- **`unfollow_all_users(limit_unfollowers)`**: opens its own following list and, row by row, clicks every button that starts with "Following" and confirms the "Unfollow @user?" popup, up to the limit. It uses the progressive sleep and block detection, and stops after 3 scrolls with no new rows.
- **`unfollow_users(user_list, to_remove_from_db, account_id, to_login, to_reverse, limit_unfollow_list, remove_not_found_users)`**: for each username it opens the profile. With `profile.following_button` it clicks it, then `profile.unfollow_confirm`. With `profile.requested_button` it clicks it and confirms the popup.
  - It counts users who show "Follow Back" (they follow us).
  - If `to_remove_from_db`, it deletes the user from `unfollow` only after `profile.follow_button` shows, which confirms the unfollow worked.
  - It can also delete not-found users.
  - It sleeps every `ROUNDS` users, stops at the limit, and saves a `Followers` row (the follow-back count) to `follow_back`.
- **`unfollow_user(username, account_id)`**: wrapper around `_unfollow_user` that closes the browser afterwards.
- **`unfollow_users_who_not_return_follow(unfollowers_list, account_id, to_reverse)`**: logs in, reads its own followers, and returns the DB users who are **not** followers. Closes the browser.

### 5.6 `bot_folder/dm/dm_bot.py` — `class DM(InstagramBot)`
- **`send_message_to_distribution_group(message, dm_users, group_name, is_schedule, to_login, account_id, group_id, limit_msg)`**: for each user (list reversed):
  - It opens the profile, clicks `profile.message_button`, types into `dm.message_input` (`_type_message`), and sends with `dm.send_button` or Enter.
  - It removes the user from `dm_users` and stops at `limit_msg` sent messages.
  - If the profile shows "Requested", it cancels the request and removes the user from `dm_users` and `unfollow`. If it shows "Follow" (we no longer follow them), it removes the user from both tables.
  - Includes block detection and the progressive sleep. Saves a `DM` stats row when the run ends.
- **`_type_message(text_input, message)`**: types the message line by line, with Shift+Enter between lines (Enter alone sends).
- **`send_message_to_following_list(message, is_schedule)`**: logs in, opens its own followers list, collects usernames and calls the method above with too few arguments. Broken (#14).
- **`_prepare_data_for_db(...)`**: saves the `DM` row.

### 5.7 `bot_folder/combination/combination_bot.py` — `class CombinationBot(InstagramBot)`
Module constants: `PROCESS_TIME = 12h`, `MAX_FOLLOWERS_EACH_PROCESS = 100`, `WAIT_FOR_EACH_FOLLOW = PROCESS_TIME / 100 = 432s`, `MAX_EMPTY_LISTS = 5`.
This is the most "human-like" feature: **follow ~100 users over 12 hours, then unfollow everyone the bot followed, and repeat.**
- **`combination(hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id, skip_posts, skip_users)`**: entry point. It only forwards `followers, hashtag, url, skip_posts, likes` to `automation`. When the run ends it saves a `combination` stats row (likes and follows asked for vs. failed) and an `account_actions` row. Distribution and skip_users are not implemented (#12).
- **`automation(max_followers, hashtag, url, skip_posts, likes)`**:
  1. Logs in and opens the starting post (`_get_wanted_post`): a hashtag's first post, a post URL itself, or the first post of any other URL. Then it skips `skip_posts` posts.
  2. Opens the post's **likes list** (`_open_likes`) and gets its scroll area.
  3. Outer loop while `max_followers > 0`, middle loop up to 100 follows. In each burst it follows a random **1–4 users** (`_follow`), then sleeps `432s × burst size`.
  4. After each 100-follow cycle it unfollows **all** users in this account's `unfollow` table (`_unfollow_users`).
  5. Stops on block (with a screenshot), or after `MAX_EMPTY_LISTS` likes lists in a row with nobody new.
- **`_new_rows()`**: rows of the open likes list not looked at yet (`self._seen`).
- **`_get_buttons(scroll_box, last_height, wait)`**: scrolls and returns the new rows. At the end of a post's likes it closes the list (`_close_list`, Escape), moves to the next post and opens its likes. Returns `(rows, height, scroll_box)`.
- **`_follow(button, username, settings, follow_count, wait, likes)`**: checks that the URL isn't a restriction URL, and that the user has a profile picture, at least `amount_followers` followers and at least `amount_posts` posts. Then it clicks Follow, saves the user to `unfollow`, checks the blocked popup (e-mail on block), and optionally likes `likes` of that user's posts (`_like_posts`). Returns `(followed, is_blocked)`.
- **`_like_posts(wait, username, likes)`**: opens the user in a new tab, opens `profile.first_post`, likes it and the next `likes-1` posts, closes the tab.
- **`_like_post(wait)`**: clicks `post.like_button` if present (it's only found while not liked, so it never unlikes).
- **`_open_likes(wait)`**: clicks `post.likes_link`. If there is none, it goes to the next post.
- **`_get_scroll_box(wait)`**: `dialog.scroll_area`.
- **`_go_to_next_post(wait)`**: clicks `post.next_button`.
- **`_unfollow_users(user_list, account_id, wait)`**: in a new tab, unfollows users in bursts of 1–4 with the same sleeps, counts follow-backs, stops on block, and saves a `Followers` row.
- **`_unfollow(user, account_id, wait)`**: opens the profile, clicks Following/Requested and confirms, detects a block, detects "Follow Back", and removes the user from `unfollow` only when `profile.follow_button` shows. Returns `(follow_back, is_blocked)`.
- **`_print_username_and_time(loops)`**: helper for the progressive sleep. Unused.
- **`_prepare_data_for_db(...)`**: saves `Combination` and `AccountActions` rows. **Never called.**
- The `wait` parameter is still in the helper signatures but unused (the selectors wait by themselves).

### 5.8 `bot_folder/proxy.py`
Builds a Chrome extension zip (`proxy_auth_plugin.zip`) with `manifest.json` and `background.js` that sets a fixed HTTP proxy with username/password auth (`get_proxy_plugin()`). **Not used anywhere.** The proxy host and credentials are read from `PROXY_HOST`, `PROXY_PORT`, `PROXY_USER` and `PROXY_PASS` in `.env` when it is called. `closeproxy.xpi` in the repo root is a Firefox proxy extension, also unused.

---

## 6. Database layer (`database/`)

### 6.1 `database/db.py` — `class Database`
`__init__` connects to `instabot.db`, runs `CREATE TABLE IF NOT EXISTS` for every table, commits and closes. **Every method opens and closes its own connection.** Many queries are built with `str.format` instead of parameters, so they are open to SQL injection and break on usernames containing `'`. Every feature DB class inherits from `Database`, so creating any of them re-runs the table creation.

#### Tables and column order (rows are read **by index** in the code)
| Table | Columns (index: name) | Purpose |
|---|---|---|
| `accounts` | 0 id, 1 name, 2 phone, 3 username, 4 password, 5 creation_date, 6 last_login | Stored Instagram accounts. The password is encrypted (`enc:v1:` + Fernet token, see `utils/crypto.py`); `Database()` encrypts any old plain-text ones on start. |
| `settings` | 0 id, 1 amount_likes, 2 amount_followers, 3 is_schedule, 4 schedule_hour, 5 modify, 6 headless, 7 amount_posts | Single global row (id=1). `[2]` = min followers, `[6]` = headless, `[7]` = min posts. |
| `unfollow` | 0 id, 1 user_id → accounts.id, 2 username | Every user the bot followed, per account. It is the source for the unfollow features. |
| `groups` | 0 id, 1 group_name, 2 user_id → accounts.id | Distribution lists (per account). |
| `dm_users` | 0 id, 1 username, 2 group_id → groups.id | Members of distribution lists. `get_users_from_dm_users` returns `(username,)` tuples. |
| `hashtag` | 0 id, 1 account, 2 hashtag, 3 num_posts, 4 num_failed_posts, 5 action_like, 6 action_follow, 7 action_comment, 8 distribution, 9 group_name, 10 comment, 11 schedule, 12 date | Hashtag run stats. |
| `location` | same as `hashtag` but column 2 is `url` | Location run stats. |
| `follow_followers` | 0 id, 1 account, 2 url, 3 num_follow, 4 num_failed_follow, 5 distribution, 6 group_name, 7 schedule, 8 date, 9 skip | Follow-followers run stats. |
| `dm` | 0 id, 1 account, 2 message, 3 group_name, 4 num_members, 5 num_failed_members, 6 schedule, 7 date | DM run stats. |
| `combination` | 0 id, 1 account, 2 url, 3 hashtag, 4 num_likes, 5 num_failed_likes, 6 num_followers, 7 num_failed_followers, 8 schedule, 9 distribution, 10 group_name, 11 date, 12 skip_users | Combination run stats. |
| `follow_back` | 0 id, 1 user_id, 2 account, 3 follow_back, 4 date | How many unfollowed users turned out to be following us. |
| `account_actions` | 0 id, 1 user_id, 2 account, 3 action, 4 amount, 5 amount_success, 6 date | Generic per-run action log ("HashTag", "Combination"). |
| `proxy` | 0 id, 1 host, 2 username, 3 password, 4 port | Saved proxies (Settings → Proxies shows host, username and port). |
| `website` | 0 id, 1 website, 2 modify | Random "warm-up" websites visited before login. |
| `inspect_settings` | id, page_not_found, user_not_found, block_restriction, block_change_pass, scroll_box_xml, scroll_box_close_btn, like_btn_xml, second_like_btn_xml, unsuccessful_login_txt, date_modify | An old plan for editable selectors. Created with defaults, never used: `utils/instagram_selectors.json` replaced it. |

#### `Database` methods
| Method | Description |
|---|---|
| `save_account(name, phone, username, password)` | Inserts an account (password encrypted), then calls `_init_settings()`. |
| `_init_settings()` | Inserts the default settings row if the table is empty. |
| `get_accounts()` | All account rows, passwords decrypted. A password that can't be decrypted (lost key) comes back empty, with an error in the log. |
| `delete_account(username)` / `update_account(id, name, phone, username, password)` | Return a bool. |
| `save_settings(likes, followers, schedule_hours, is_active, headless, posts)` | Updates row id=1. |
| `get_data_from_settings()` | Returns the settings row (tuple) or `None`. |
| `save_unfollow_users(user, account_username)` | Adds a followed user to `unfollow`. |
| `get_unfollow_users(username)` | `unfollow` rows for that account. |
| `get_user_id(username)` | `accounts.id` for a username (crashes if not found). |
| `create_distribution_group(group_name, username)` | Creates a group. |
| `get_distribution_lists_by_username(username)` | Groups of an account. |
| `remove_group_from_distribution_list(group_name, owner_username)` | Deletes a group (its `dm_users` rows stay). |
| `add_username_to_distribution_group(user, group_id)` | Adds a member. |
| `remove_username_from_unfollow_list(username, user_id)` | Deletes from `unfollow`. |
| `get_group_id_by_group_name_and_id(group_name, owner_username)` | Group id lookup. |
| `get_users_from_dm_users(group_name, owner_username)` | Usernames in a group. |
| `save_data_account_action(action)` | Inserts an `AccountActions` row. |
| `get_proxy_data()` / `get_websites_data()` | All proxies / websites. |

### 6.2 Feature DB subclasses (all inherit `Database`)
| File | Class | Methods |
|---|---|---|
| `database/hashtag/hashtag.py` | `HashtagDB` | `save_in_db(Hashtag)`, `get_hashtag_data()` |
| `database/location/location.py` | `LocationDB` | `save_in_db(Location)`, `get_location_data()` |
| `database/follow_followers/follow_followers.py` | `FollowFollowersDB` | `save_in_db(FollowFollowers)`, `get_follow_followers_data()`, `get_account_data(account)` |
| `database/dm/dm.py` | `DMDB` | `save_in_db(DM)`, `get_dm_data()`, `remove_dm_user_from_list(username, group_id)` |
| `database/combination/combination.py` | `CombinationDM` | `save_in_db(Combination)`, `get_combination_data()`, `get_account_data(account)` |
| `database/followers/followers.py` | `FollowersDB` | `save_in_db(Followers)` → inserts into `follow_back` |
| `database/follow_back/follow_back.py` | `FollowBackDB` | `save_in_db(FollowBack)`, `get_follow_back_data()`, `get_account_data()` (queries the wrong table) |
| `database/proxy/proxy.py` | `Proxy` | `save_in_db(Proxy)`, `remove_from_db(id)` |
| `database/website/website.py` | `Website` | `save_in_db(Website)`, `remove_from_db(id)` |

---

## 7. Models (`models/`)
Plain data holders. Most set `self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")` automatically.

| Class (file) | Constructor fields |
|---|---|
| `AccountActions` (`account_actions.py`) | user_id, username, action, amount, amount_success (+date) |
| `Hashtag` (`hashtag.py`) | account, hashtag, num_posts, action_like, action_follow, action_comment, distribution, group_name, comment, num_failed_posts, schedule (+date) |
| `Location` (`location.py`) | account, url, num_posts, action_like, action_follow, action_comment, distribution, group_name, comment, num_failed_posts, schedule (+date) |
| `FollowFollowers` (`follow_followers.py`) | account, url, num_follow, num_failed_follow, distribution, group_name, schedule, skip (+date) |
| `DM` (`dm.py`) | account, message, group, num_members, num_failed_members, schedule (+date) |
| `Combination` (`combination.py`) | account, url, hashtag, num_likes, num_failed_likes, num_followers, num_failed_followers, schedule, distribution, group_name, skip_users (+date) |
| `Followers` (`followers.py`) | user_id, account, follow_back (+date) |
| `FollowBack` (`follow_back.py`) | used_id → stored as `user_id`, account, follow_back, date (date argument ignored) |
| `Proxy` (`proxy.py`) | host, username, password, port |
| `Website` (`website.py`) | website_link → `website` (+`modify` date) |

---

## 8. Utilities (`utils/`)

### 8.1 `utils/instagram_selectors.json` — the one source of truth for Instagram's pages
Instagram's DOM changes often, so this file is where most maintenance happens. Fix it here (or in **Inspect Settings**), never in the bots. Top-level keys:
- `about`: a description of the format.
- `urls`: `home`, `login`, `profile` (`{username}`), `hashtag` (`{tag}`).
- `texts`:
  - `row_button_texts` (`Follow`, `Following`, `Requested`, `Follow Back`): the buttons a list row can have.
  - `default_avatar_file`: the file name of Instagram's default profile picture.
  - `restriction_urls` (`/restriction/`, `/challenge/`, `/accounts/suspended/`).
- `selectors`: groups → keys. Each entry has `what` (a description), `find` (a list of **ways**, tried in order), and `checked` (the date it was last seen working, or `null` = an educated guess that couldn't be checked safely).

Ways: `{"css": ...}`, `{"xpath": ...}`, `{"name": ...}` (a form field name), `{"text": regex}` (the smallest visible element whose whole text matches), `{"scrollable": css}` (the scrolling part inside the last element matching css).

| Group | Keys |
|---|---|
| `login` | `username_input`, `password_input`, `error_message`, `logged_in_marker`, `not_now_button` |
| `profile` | `follow_button`, `follow_back_button`, `following_button`, `requested_button`, `unfollow_confirm`, `message_button`, `posts_counter`, `followers_counter`, `following_counter`, `picture`, `first_post`, `not_found_title` |
| `grid` | `first_post` |
| `post` | `like_button`, `unlike_button`, `next_button`, `close_button`, `comment_input`, `author_link`, `author_follow_button`, `likes_link` |
| `dialog` | `box`, `scroll_area`, `user_link`, `row_button`, `close_button` |
| `dm` | `message_input`, `send_button` |
| `block` | `popup`, `popup_ok` |
| `search` | `input` |

Notes on today's Instagram (checked 2026-10-25):
- The login fields are `name="email"` / `name="pass"`.
- The profile counters are links (`a[role=link]`) whose text is "N followers".
- Followers, following and likes lists open in a dialog with a scrolling div.
- The profile's Follow/Following buttons are scoped to the profile header, so suggested accounts don't match. Their text includes a hidden "Down chevron icon", so they match with `starts-with`.
- The post's Like is the heart in the action bar that also holds the Comment icon (not a comment's heart).
- The DM box is a `contenteditable` textbox.

### 8.2 `utils/instagram_selectors.py` — `class Selectors`, and the shared instance `S`
| Method | What it does |
|---|---|
| `reload()` / `save(data)` | Read / write the JSON. `save` reloads, so bots see edits right away. |
| `entry(key)` / `ways(key)` / `keys()` | An entry, its ways, all keys (`"group.name"`). |
| `text(name)` / `url(name, **values)` | A value from `texts` / a formatted URL from `urls`. |
| `find_all(root, key)` | All visible elements from the first way that finds any. |
| `find(root, key, timeout=0)` | The first match or `None`, retrying until the timeout. |
| `get(root, key, timeout=7)` | Like `find`, but raises `NoSuchElementException` with the key's description. |
| `exists(root, key, timeout=0)` | `find(...) is not None`. |
| `clickable(element)` | The nearest clickable ancestor (`a`, `button`, `[role=button]`, `[role=link]`) of an svg or text span. |
| `click(root, key, timeout=7)` | `get` + `clickable` + click. |
| `count(root, key, timeout=7)` | A counter's number as text, using its `title` attribute when Instagram shortens it ("686M"). |
| `dialog_rows(driver, timeout=7)` | The open (last) list dialog as `[(username, button or None), ...]`, one row per username link. The button is the row's Follow / Following / Requested / Follow Back button. |
| `scroll_to_bottom(driver, element)` | Scrolls an element to its end and returns its new height. |

### 8.3 `utils/selector_check.py`
- `check_selectors(driver, username, log=print)`: needs a logged-in driver. It visits Home, your profile (opens the followers and following lists), a profile you follow (opens and closes the Following menu, opens Message without typing), `@instagram`, a `#sunset` post (and its likes list), and a profile that doesn't exist. It returns `{key: (status, note)}` with the statuses `ok`, `missing` and `not checked`. **Read-only:** it never clicks Follow, Unfollow, Like, Comment or Send.
- `CANNOT_CHECK`: the keys that only appear in situations it can't create safely (a block, a wrong password, a pending request, a typed message, …), with the reason.
- `mark_checked(results)`: stores today's date as `checked` on every key that was found.

### 8.4 `utils/utils.py` — `class Utils`
- Timing constants: `TIME_SLEEP = 5` (sleep step in seconds, and every how many actions to sleep), `ROUNDS = 5` (the unfollow sleep interval).
- `_check_username_password(username, password)` (static): `False` if either is empty.
- `arithmetic_progression(time_wait, total, rows)`: prints an estimated run time in minutes for the progressive sleep scheme.
- `clean_number(text)`: converts Instagram counters to int: `"1,454"` → 1454, `"20.8K"` → 20800, `"10M"` → 10000000, `"1.2B"` → 1200000000.
- `clean_post_number(text)`: the same as `clean_number`.

### 8.5 `utils/schedule.py` — `class ScheduleCalc`
`calc_schedule_time(action, minutes, hours, days)` returns the delay in **seconds**. `action` is 0 = minutes, 1 = hours, 2 = days (`ScheduleBox` passes the chosen unit).

---

## 9. Cross-cutting behavior

- **Anti-detection measures:**
  - A random "warm-up" website before login, and a fixed desktop user-agent (desktop Chrome).
  - Progressive sleeps (`loops × 5s` every 5 actions), and random 1–4 follow bursts with long waits in Combination.
  - Only following users with a real profile picture and above the follower/post thresholds.
  - Block detection (restriction/challenge URLs, the "action blocked" popup) that stops the job.
- **Follow tracking loop:** every follow from any feature goes into `unfollow` → shown on the Unfollow page → unfollowed later. The DM feature also cleans up `unfollow` / `dm_users` when users are no longer followed.
- **Distribution lists:** created in Settings → filled automatically while following (Hashtag / Location / Follow Followers) → used as DM recipients on the DM page.
- **Jobs:** each job gets its own worker thread and its own Chrome window, so several accounts can run in parallel (up to 8). Jobs can be scheduled, cancelled before they start, or stopped while running (this closes their Chrome). Bots still report progress only through `print`, which the Log panel shows per job.
- **Logins:** each job logs in again in a fresh Chrome profile. If Instagram asks for a security check, the bot stops and says so. Log in to the account by hand once, then run again.
- **Error reporting:** the Log panel, toasts, screenshots in `screen_shots/`, and Mailgun e-mails (they need the `MAILGUN_DOMAIN` / `MAILGUN_API` variables in `.env`).
- **Ignored by git (`.gitignore`):** `instabot.db`, `screen_shots`, `images`, `.env`, `chromedriver.exe`, `geckodriver*`, `proxy_auth_plugin.zip`, `venv`, `.venv`, `*.pyc`.

### Developer TODO list (from the old `main.py`)
- ~~Change the Follow Followers logic to "scroll then follow", like Combination.~~ Done: it reads the list row by row.
- Finish and test "unfollow only users who don't follow back" against today's Instagram.
- ~~Show Combination stats in the Statistics tab.~~ Done.
- Per-account action summary boxes on the Statistics page.
- ~~Display the follow-back counts.~~ Done: Statistics → Follow back.
- ~~Make Instagram selectors editable from the UI.~~ Done: Inspect Settings.

---

## 10. Known bugs and limitations
The issues below were found by reading the code. The numbers are kept stable because the UI's hints refer to them ("known issue #12"). Fixed ones are marked **Fixed**.

**Selectors and Instagram changes**
1. **Fixed.** Selectors used to be scattered, absolute or obfuscated. They now all live in `utils/instagram_selectors.json`. When Instagram changes, run **Inspect Settings → Check selectors**, then fix what's missing there.
2. **Fixed.** Migrated to Selenium 4: `find_element(By.X, ...)` everywhere, no `desired_capabilities`, and Selenium Manager instead of webdriver-manager.
3. **Fixed.** The ChromeDriver is no longer pinned: Selenium Manager downloads the one matching the installed Chrome.

**Driver and config**
4. **Fixed.** Chrome now gets its options in both desktop and mobile mode (before, desktop ignored them and mobile's `chrome_options` replaced them), and `Options` is imported from `selenium.webdriver.chrome.options`.
5. `proxy_dict` is never applied. The proxy fields and the `proxy` table have no effect. (**Fixed** in the UI: the old Settings window's inverted Save check.)
6. **Fixed.** The proxy credentials and the alert e-mail now come from `.env` (see `.env.example`). The old values are still in the git history, so they must be rotated.
7. If the `settings` row does not exist (no account added yet), `get_data_from_settings()` returns `None` and `InstagramBot.__init__` crashes on `[6]`. (**Fixed** in the UI: Settings shows defaults. In practice bots always have an account, and adding one creates the row.)
8. **Fixed.** `requirements.txt` lists every dependency and installs on Python 3.14. The README uses `pip install -r`.

**Logic bugs**
9. **Fixed.** `_get_followers_number` always returns 3 values.
10. **Fixed.** `_follow_user` reads the 3 values and only follows users with a picture and enough followers.
11. Hashtag likes threshold: it is replaced by `if int(20) > int(0):`, so the "Settings → likes" value is ignored.
12. `CombinationBot.combination` doesn't save followed users to the distribution list (`group_id`) and ignores `skip_users`. (**Fixed:** it now saves its stats when a run ends.)
13. **Fixed.** `DMDB.save_in_db` inserted into column `group_distribution`, but the table column is `group_name`, so DM stats were never saved.
14. `send_message_to_following_list` calls `send_message_to_distribution_group` with too few arguments. (The UI side is handled: "Message my followers" is disabled.)
15. **Fixed** (the old DM tab called `DMDB.remove_dm_user_from_list` on the class).
16. `FollowBackDB.save_in_db` uses the column `used_id` (it should be `user_id`). `FollowBackDB.get_account_data` queries `follow_followers` (copy-paste error). The app doesn't call either one: follow-back rows are saved by `FollowersDB`, and Statistics reads them with `FollowBackDB.get_follow_back_data()`.
17. **Fixed** (the old tab passed 6 of the 7 arguments to `unfollow_users`).
18. **Fixed.** "Who doesn't follow me back" runs as a background job.
19. `search_location_by_name` does not log in and calls `_follow_user()` without the required arguments. Not wired in the UI.
20. **Fixed.** `Utils.clean_number("10M")` returns 10,000,000.
21. `Database.get_user_id` / `get_group_id_by_group_name_and_id` crash with `TypeError` when nothing is found (`None[0]`).
22. `screen_shots/` is now created by `main.py` (**Fixed**), but `_send_email` still fails if the screenshot is missing.

**Security and quality**
23. **Fixed.** All SQL uses `?` parameters. The UI still refuses apostrophes in usernames and list names; that check can now be dropped.
24. Instagram passwords are stored in plain text in SQLite. (The Accounts table no longer shows them.)
25. Wide `try/except Exception: pass` blocks in the bots hide most failures, and there is no logging framework. (**Partly fixed:** there are now tests, and running jobs can be stopped.)
26. Automating Instagram actions violates Instagram's Terms of Use and can get accounts restricted or banned. The block-detection code exists for this reason.

---

## 11. Quick file index
| Path | Contains |
|---|---|
| `main.py` | App entry point |
| `ui/app.py` | QApplication setup, theme, `run()` |
| `ui/main_window.py` | Main window: header, sidebar, pages, docks, dialogs |
| `ui/core/jobs.py` | `Job`, `JobManager`, `JobWorker` |
| `ui/core/log_bridge.py` | stdout/stderr → Log panel |
| `ui/core/validators.py` | Form checks |
| `ui/core/db_helpers.py` | Names for DB tuple indexes |
| `ui/widgets/*.py` | Reusable widgets (§4.2) |
| `ui/pages/job_page.py` | Base class of the bot pages |
| `ui/pages/hashtag_page.py` | Hashtag page |
| `ui/pages/followers_page.py` | Unfollow page |
| `ui/pages/location_page.py` | Location page |
| `ui/pages/follow_followers_page.py` | Follow Followers page |
| `ui/pages/dm_page.py` | DM page |
| `ui/pages/combination_page.py` | Combination page |
| `ui/pages/statistics_page.py` | Statistics page |
| `ui/dialogs/accounts_dialog.py` | Accounts |
| `ui/dialogs/settings_dialog.py` | Settings (thresholds, headless, distribution lists, proxies, websites) |
| `ui/dialogs/inspect_settings_dialog.py` | Selector editor and checker |
| `ui/theme/dark.qss`, `ui/theme/palette.py` | Stylesheet and color tokens |
| `ui/theme/icons/` | The app icon (`app.png`) and the stylesheet's arrow/check icons |
| `bot_folder/main_bot.py` | `InstagramBot` base class |
| `bot_folder/hash_tag/hash_tag_bot.py` | `HashTagBot` |
| `bot_folder/location/location_bot.py` | `LocationBot` |
| `bot_folder/follow_followers/follow_followers_bot.py` | `FollowFollowersBot` |
| `bot_folder/followers/followers_bot.py` | `FollowersBot` |
| `bot_folder/dm/dm_bot.py` | `DM` bot |
| `bot_folder/combination/combination_bot.py` | `CombinationBot` |
| `bot_folder/proxy.py` | Chrome proxy-auth extension builder (unused) |
| `database/db.py` | `Database` base, schema and shared queries |
| `database/*/*.py` | Per-feature DB classes |
| `models/*.py` | Data classes |
| `utils/instagram_selectors.json` | Every Instagram selector, URL and text |
| `utils/instagram_selectors.py` | `Selectors` / `S`: finding things by key |
| `utils/selector_check.py` | Read-only check of the selectors on real Instagram |
| `utils/utils.py` | Timing constants, number parsing |
| `utils/schedule.py` | Schedule delay calculator |
| `tests/` | pytest-qt tests (`conftest.py` has the temp-DB fixtures) |
| `UI_MIGRATION.md` | The Tkinter → PySide6 plan (done) |

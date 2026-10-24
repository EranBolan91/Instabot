# Instabot — Full Project Reference

> **Purpose of this document:** a complete, self-contained description of the Instabot codebase so an AI assistant (or a new developer) can understand every feature, module, class and function without reading the source first. Its sections are: what the app does → architecture → each layer in detail → database schema (with tuple indexes, since the code reads rows by position) → cross-cutting behavior → known bugs and limitations.

---

## 1. What the project is

Instabot is a **desktop GUI application written in Python** that automates actions on Instagram through a real Chrome browser driven by **Selenium**. The user stores one or more Instagram accounts locally, then uses tabs in the GUI to start automation jobs such as:

- Like / comment on / follow posts found through a **hashtag**
- Like / comment on / follow posts found through a **location URL**
- Follow the **followers** or **following** list of another user
- Follow users who **liked a post** (the "Combination" feature, with automatic unfollow cycles)
- Find who **doesn't follow you back**, then unfollow them
- **Unfollow** users the bot followed earlier (tracked in the DB), or unfollow everyone
- Send **direct messages (DMs)** to "distribution lists" of users the bot collected
- **Schedule** any of these jobs to start after X minutes, hours or days
- See **statistics** of past runs

Everything is stored in a local **SQLite** database file, `instabot.db`, created automatically in the working directory.

### Tech stack
| Concern | Library |
|---|---|
| GUI | `tkinter` + `ttkbootstrap` (theme `"darkly"`), some `tkinter.ttk` |
| Browser automation | `selenium==3.141.0` (uses the old Selenium 3 API: `find_element_by_xpath`, etc.) |
| Chrome driver install | `webdriver_manager` (`ChromeDriverManager(version='114.0.5735.90')`) |
| HTML parsing | `beautifulsoup4` (only used in the Combination bot's like check) |
| Storage | `sqlite3` (standard library) |
| Error e-mails | `requests` → Mailgun HTTP API |
| Concurrency | `threading.Thread`, `threading.Timer`, `concurrent.futures.ThreadPoolExecutor` |

`ttkbootstrap` and `webdriver_manager` are imported but **missing from `requirements.txt`**.

### How to run
```bash
pip install -r requirements.txt
pip install ttkbootstrap webdriver-manager   # not listed in requirements.txt
python main.py
```
`main.py` opens a full-screen `ttkbootstrap.Window(themename="darkly")` and builds the `Layout`.

---

## 2. Architecture overview

The project follows a loose **MVC-like layered structure**:

```
main.py                      → entry point, creates window + Layout
view/                        → Tkinter GUI (one class per tab / window)
bot_folder/                  → Selenium bots (business logic, one per feature)
    main_bot.py              → InstagramBot base class (shared browser helpers)
database/                    → SQLite access layer
    db.py                    → Database base class (creates all tables, shared queries)
    <feature>/<feature>.py   → per-feature DB subclasses (save / read stats)
models/                      → plain data classes (DTOs) passed to the database layer
utils/                       → constants (XPaths, class names, texts) + helpers
```

### Typical data flow of a job
1. The user picks an account in a tab's **"Choose user"** dropdown. The tab fills the username/password fields from the `accounts` table.
2. The user fills the form and clicks **RUN / SEARCH / START FOLLOW / SEND**.
3. The tab validates the form (`_check_form`), then creates a bot instance, e.g. `HashTagBot(username, password, False, proxy_dict)`. **Creating the bot immediately opens a Chrome window.**
4. The bot method runs in a **background thread** (`threading.Thread`), or in a `threading.Timer` if "Schedule action" is checked.
5. The bot logs in (`_login`), navigates Instagram, performs actions with randomized and progressive sleeps, and saves every followed user to the `unfollow` table (and optionally to a distribution list).
6. When the job finishes, the bot builds a **model** object (e.g. `Hashtag`) and saves it through the matching **DB class** (e.g. `HashtagDB().save_in_db`) so it appears in the **Statistics** tab.
7. If Instagram blocks the account, the bot takes a screenshot (`screen_shots/<username>.png`) and e-mails it through Mailgun.

### Constructor convention
Every bot inherits `InstagramBot(username, password, is_mobile, proxy_dict)`.
- `is_mobile=True` → Chrome with mobile emulation ("Nexus 5") using a local `chromedriver.exe` (used by the DM bot).
- `is_mobile=False` → desktop Chrome via `ChromeDriverManager`.
- `proxy_dict = {"proxy": ..., "port": ...}` is accepted everywhere but **never used** (see Known Issues).

---

## 3. Entry point and layout

### `main.py`
Creates the root window (`ttk.Window(themename="darkly")`), makes it full-screen and instantiates `Layout(window)`. Also has a block of TODO comments describing planned work (see §9).

### `view/layout.py` — `class Layout`
Builds the main window:
- **Menu bar "Main"** → `Accounts`, `Settings`, `Inspect Settings`, `Exit`. Each opens a `Toplevel` window (`_accounts`, `_settings`, `_inspect_settings`); `_exit` destroys the window.
- **Notebook tabs**, in order: `Hash Tag` (`TabHashTag`), `Followers` (`TabFollowers`), `Location` (`TabLocation`), `Follow Followers` (`TabFollowFollowers`), `DM` (`TabDM`), `Combination` (`TabCombination`), `Statistics` (`StatisticsTab`).
- A static **status bar** label ("status bar"), which is just a placeholder.

---

## 4. GUI layer (`view/`) — every window and tab

### Shared UI patterns (present in almost every tab)
- **Choose user dropdown** (`ttk.OptionMenu`) listing `accounts.username`. Its callback `_set_username_password(value)` fills the username/password entries (masked with `*`) and loads that account's **distribution lists** into a second dropdown.
- **Schedule Action frame**: radio buttons Minutes / Hours / Days plus three entries. `_enable_entry()` enables only the entry of the selected unit. If the "Schedule action" checkbox is on, the delay is computed with `ScheduleCalc().calc_schedule_time(...)` and the job runs through `threading.Timer(delay, ...)`.
- **Proxy frame**: proxy host + port entries. They are validated (both or neither) and passed as `proxy_dict`, but the bots ignore them.
- **Comment entry**: comma-separated comments (`"Nice picture,Looking good"`). `_split_comment` turns them into a list, and the bot picks one at random per post.
- **"Save users in distribution list?"** checkbox: every followed user is also added to the selected distribution group (used later by the DM tab).
- **REFRESH LIST** button (`_get_accounts`): reloads the accounts dropdown.

### `view/accounts.py` — `class AccountsNew` (menu → Accounts)
CRUD for stored Instagram accounts.
- Left side: REGISTER form (Name, Phone, Username*, Password*) with an **ADD** button.
- Right side: a listbox of all accounts. Double-clicking an account shows its details in a second listbox (`_display_content`).
- Buttons: **EDIT** (`_edit_account`: loads the selected account into the form and enables UPDATE), **UPDATE** (`_save(UPDATE)`), **DELETE** (`_delete_account`, with a confirmation dialog).
- `_save(update_or_save)`: `SAVE=1` → `Database.save_account`, `UPDATE=0` → `Database.update_account`.
- `_get_accounts`, `_set_accounts`, `_reset`: helpers.
- Passwords are stored and displayed in **plain text**.

### `view/settings.py` — `class Settings` (menu → Settings)
A scrollable full-screen window with these sections:
1. **Main settings** (stored in the single `settings` row, id=1):
   - *Likes threshold* → `amount_likes`: only act on posts with more than X likes. **Currently not enforced**; the check is commented out in the bots.
   - *Posts threshold* → `amount_posts`: only follow users with at least X posts (Combination bot).
   - *Followers threshold* → `amount_followers`: only follow users with at least X followers (all follow features).
   - *Headless* checkbox → `headless` (only applied in the mobile-driver branch; see Known Issues).
   - **SAVE CHANGES** (`_save_changes`): keeps the old value of any field left at 0, then saves through `Database.save_settings`.
2. **Distribution list**: choose an account, type a list name, ADD (`_save_distribution_list` → `create_distribution_group`) or REMOVE (`_remove_group_from_distribution_list`). `_set_users_groups` reloads the listbox when the account changes.
3. **Proxy**: Host / Username / Password / Port, SAVE (`save_proxy`) and REMOVE (`remove_proxy`). Stored in the `proxy` table.
4. **Websites**: a list of URLs (`save_website` / `remove_website`). Before each login the bot visits **one random website** from this list, to look less bot-like.
- `_settings_data()` loads all of the above when the window opens.

### `view/inspect_settings.py` — `class InspectSettings` (menu → Inspect Settings)
A **UI-only stub**. It has entries for the block URLs, scroll box XPath, like-button XPaths and the "page not available" / "user not found" texts. The idea (see the TODO in `main.py`) is to let the user update Instagram selectors without changing code. `_init_data()` is empty and the SAVE button has no command. The matching DB table `inspect_settings` exists but is never read or written.

### `view/tab_hash_tag.py` — `class TabHashTag` ("Hash Tag" tab)
Form: username/password, hashtag keyword, number of posts, checkboxes LIKE / FOLLOW (+ distribution list) / COMMENT (+ comment entry) / Schedule, proxy.
- `_run_script()`: validates with `_check_form` (credentials required, hashtag required, amount a positive integer, proxy and port given together) and requires at least one action. It then runs `HashTagBot.search_hash_tag(...)` in a thread or timer.
- `_activate_check` enables the comment entry, `_activate_distribution_check_box` enables the distribution checkbox only when FOLLOW is checked.

### `view/tab_location.py` — `class TabLocation` ("Location" tab)
Same layout as the Hash Tag tab, but the input is a **location URL** (e.g. `https://www.instagram.com/explore/locations/212988663/new-york-new-york/`). The "location name" entry is disabled ("Not active now").
- `_run_script()`: if a URL is given it runs `LocationBot.search_location_by_url`, otherwise `search_location_by_name`.

### `view/tab_follow_followers.py` — `class TabFollowFollowers` ("Follow Followers" tab)
Two forms side by side:
- **Left, "Follow after users that user following them"** → `_search_following` → `FollowFollowersBot.follow_after_following` (follows the target's *following* list).
- **Right, "Follow after users that following user"** → `_search_followers` → `FollowFollowersBot.follow_after_followers` (follows the target's *followers* list).
- Shared inputs: number of people to follow, number to skip, distribution list, schedule, proxy.
- **User data box**: `_get_account_data_for_data_box` shows this account's past follow-followers runs (date, follow, failed, skip, URL).
- `_check_form`: credentials, URL and a follow count > 0.

### `view/tab_followers.py` — `class TabFollowers` ("Followers" tab)
The **unfollow** management center:
- **RUN** (`_check_form`): runs `FollowersBot.get_unfollowers()` **synchronously on the GUI thread** (the GUI freezes). Results go into the "Search results" listbox with a count and a "Do you want to UNFOLLOW them? → Click here" button that calls `_unfollow_users_list(list, 0)`.
- **SEARCH** (`_search_user`): opens the selected result's profile in the bot's browser.
- **"You are following N" listbox**: shows the `unfollow` table rows for the selected account, meaning the users *this bot followed*.
  - **REMOVE** (`_remove_from_unfollow_list`): deletes the selected user from the DB only.
  - **UNFOLLOW USER** (`_unfollow_user`): unfollows one selected user via `FollowersBot.unfollow_user`.
  - **UNFOLLOW LIST** (`_unfollow_users_list(self.unfollow_users, 1)`): unfollows every user in the DB list via `FollowersBot.unfollow_users`.
  - **REMOVE UNFOLLOWERS USERS** (`_remove_users_who_not_follow_back`): first runs `unfollow_users_who_not_return_follow`, which scrapes the account's followers and keeps only DB users who are **not** among them. It then unfollows only those users.
- Options: **Limit unfollowers** (max unfollows), **Remove not found users?** (delete deleted/broken profiles from the DB), **To reverse?** (process the list newest-first), Schedule.
- **UNFOLLOW EVERYONE** frame (`_unfollow_all_users_account_follow_them`): opens the account's own "following" dialog and clicks "Following" on everyone, up to a limit (`FollowersBot.unfollow_all_users`).
- `_get_account_id()`: looks up the account id from the loaded accounts.

### `view/tab_dm.py` — `class TabDM` ("DM" tab)
- Choose an account, then a distribution list (`_display_users_to_boxlist` shows its members and a count).
- **SEND** (`_run_script`): loads `dm_users` for the group and runs `DM.send_message_to_distribution_group(...)` with a message limit (`limit_msg`).
- **CLEAR LIST** (`_remove_all_dm_list`) / **REMOVE USER** (`_remove_user`): delete members from the group in the DB.
- **"Messages to current following account"** frame (`_send_msgs_current_account_following`): sends a message to the account's own followers list via `DM.send_message_to_following_list`.
- `_get_account_id`, `_get_group_id`: lookups.

### `view/tab_combination.py` — `class TabCombination` ("Combination" tab)
"Follow after users who liked a post."
- Inputs: account, **hashtag OR URL** (exactly one), proxy dropdown (from the `proxy` table, not actually used), distribution checkbox, **number of posts to like** per followed user, **number of users to follow**, **skip posts**, **skip users**, schedule.
- `_run_script()` runs `CombinationBot.combination(...)` in a thread or timer. The proxy is hard-coded to a dummy value (`"fdgdfgfdgf"`, `558`).
- `_check_form`: credentials; exactly one of hashtag/URL; follows ≠ 0; likes ≥ 0.
- **User data box**: past combination runs (`CombinationDM.get_account_data`).
- `_get_accounts`, `_get_proxies`: refresh the dropdowns.

### `view/tab_statistics.py` — `class StatisticsTab` ("Statistics" tab)
Five scrollable listboxes: **HashTag**, **Location**, **Follow Followers**, **DM**, **Follow back**, filled by `_init_data()` from `HashtagDB`, `LocationDB`, `FollowFollowersDB`, `DMDB` and `FollowBackDB`. Only the hashtag rows are formatted with labels, the others show raw tuples. A **REFRESH** button reloads them. Combination stats are not displayed yet (TODO).

### `view/testing.py` — `class Testing`
A scratch file for testing a scrollable canvas. Not used (and git-ignored).

---

## 5. Bot layer (`bot_folder/`) — every class and function

### 5.1 `bot_folder/main_bot.py` — `class InstagramBot` (base class)
Holds a `db.Database()`, the credentials, `base_url = 'https://www.instagram.com'` and the Selenium `driver`.

**`__init__(username, password, is_mobile, proxy_dict)`** builds Chrome options (eager page load, no-sandbox, disable GPU and notifications, a fixed desktop user-agent, and `--headless` if `settings.headless`). It then starts Chrome:
- mobile: `webdriver.Chrome('chromedriver.exe', options=..., chrome_options=<Nexus 5 emulation>)`
- desktop: `webdriver.Chrome(ChromeDriverManager(version='114.0.5735.90').install())`. **The options are not passed here.**
It also sets `self.wait = WebDriverWait(driver, 7)`.

| Method | What it does |
|---|---|
| `get_username()` / `get_password()` | Getters. |
| `_login()` | Visits a random site from the `website` table (if any), opens `/accounts/login/`, types the username and password + Enter, waits, then returns `is_login_successful()`. Prints and returns `False` on failure. |
| `is_login_successful()` | Looks for the error element (class `eiCW-`) and compares its text to `Utils.UNSUCCESSFUL_LOG_IN_TEXT`. |
| `_nav_user(user)` | Navigates to `instagram.com/<user>/`. |
| `_nav_user_new_tab(username)` | Opens the profile in a new tab via JS `window.open`. |
| `_like_post()` | Clicks the like button (class `_aamw`). Screenshots on failure. |
| `_get_like_amount_text()` | Reads a post's like count from two possible XPaths and strips commas. Currently unused, because the likes threshold is disabled. |
| `_comment_post(split_comment)` | Picks a random comment, clicks the `textarea`, types it + Enter. |
| `_follow_user(to_distribution, group_id)` | On an open post: finds the Follow button (`Utils.FOLLOW_BTN`) and reads the post author's username (`Utils.POST_USERNAME`). If the button says "Follow" and the author has at least `settings.amount_followers` followers, it clicks the button, saves the user to `unfollow` and optionally to a distribution group. |
| `_unfollow_user(username, user_id)` | Logs in, opens the profile, clicks Following → Unfollow (or "Requested" → popup), and removes the user from the `unfollow` table. |
| `_popup_unfollow()` | Confirms the "Unfollow?" popup shown for private accounts (class `mt3GC`). |
| `_user_not_found_broken_link()` | `True` if the page shows "Sorry, this page isn't available." plus the broken-link paragraph. |
| `_check_if_blocked()` | Reads the h2/p error text. Returns `True` if an error other than "page isn't available" is shown. |
| `_get_followers_number(username)` | Opens the user in a 2nd tab, checks `_has_profile_image()`, reads the post count and follower count (class `_ac2a`), closes the tab. Returns **`(followers, has_image, posts)` if the user has a profile image, otherwise `(followers, has_image)`**, an inconsistent tuple size (see bugs). `-1` means unknown. |
| `_has_profile_image()` | Checks whether the profile picture `src` is Instagram's default avatar (`44884218_...jpg`). **Returns `-1` when the user HAS a real picture** (the result of `str.find`), and a non-negative number when it's the default avatar. Users without a picture are skipped. |
| `_check_if_follow_back()` | After unfollowing, if a "Follow Back" button appears, it clicks it and returns `True`. |
| `_get_usersname()` | Scrolls a followers dialog to the bottom and returns username elements (class `_0imsa`). |
| `_screen_shot(username)` | Saves `screen_shots/<username>.png` (the folder must exist). |
| `_send_email(username, success_posts, time, section)` | Sends an error e-mail with the screenshot attached through the Mailgun API, using env vars `MAILGUN_DOMAIN` and `MAILGUN_API`. Sender and recipient addresses are hard-coded. |
| `_blocked_action_popup()` | Waits for the "action blocked" popup (class `bIiDR`). If it appears: screenshot, click it, return `True`. |
| `global_block_message(username, section)` | Prints a "user has been blocked" message. |
| `global_complate_task(username, section, results)` | Prints a task-complete message. Unused. |
| `is_post_liked()` | If the post is already liked, clicks "Unlike". Unused. |
| `skip_posts(n)` | Clicks the "next post" arrow `n` times (old class `coreSpriteRightPaginationArrow`). |
| `save_account_action(account_action)` | Saves to `account_actions`. |
| `get_post_amount()` | Reads the posts counter of the open profile. |
| `check_current_url()` | Returns `driver.current_url`. |

### 5.2 `bot_folder/hash_tag/hash_tag_bot.py` — `class HashTagBot(InstagramBot)`
- **`search_hash_tag(hash_tag, amount, like, comment, follow, split_comment, to_distribution, group_name, group_id, time_schedule)`**
  1. Logs in, opens `/explore/tags/<hash_tag>`, clicks the first post (class `_aagu`).
  2. Repeats `amount` times: optionally like / comment / follow (`_follow_user`), then clicks the **Next** arrow (`Utils.RIGHT_ARROW`).
  3. **Throttling:** every `TIME_SLEEP` (5) posts it sleeps `loops * 5` seconds, so the pauses grow (0s, 25s, 50s…). The counter resets when `i*5 == 500`.
  4. After each post it checks `_check_if_blocked()`. If blocked: screenshot, e-mail, close the browser, stop.
  5. `finally`: saves stats (`_prepare_data_for_db`), deletes cookies, closes the browser.
  - The likes threshold check is replaced by a placeholder `if int(20) > int(0):` (always true).
- **`_prepare_data_for_db(...)`**: saves a `Hashtag` row and an `AccountActions` row ("HashTag", amount, successes).

### 5.3 `bot_folder/location/location_bot.py` — `class LocationBot(InstagramBot)`
- **`search_location_by_url(url, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id, time_schedule)`**: same loop as the hashtag bot, but it opens the location URL, clicks the first post (old class `_9AhH0`) and moves with the old `coreSpriteRightPaginationArrow` class. Saves a `Location` stats row.
- **`search_location_by_name(...)`**: types the name into the search bar (`_search_entry`) and loops. It is incomplete: no login, and it calls `_follow_user()` without arguments. Disabled in the UI.
- **`_search_entry(name)`**: types into the top search input.
- **`_prepare_data_for_db(...)`**: saves a `Location` row.

### 5.4 `bot_folder/follow_followers/follow_followers_bot.py` — `class FollowFollowersBot(InstagramBot)`
- **`follow_after_followers(user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule, num_skip)`**: logs in, opens the target profile, clicks `/followers`, then repeatedly scrolls the dialog. For each "Follow" button whose user has a profile picture and at least `settings.amount_followers` followers, it clicks the button, saves the user to `unfollow` (and the distribution list), checks the blocked popup, and uses the progressive sleep. It skips the bot's own username and stops after `num_of_following` follows.
- **`follow_after_following(...)`**: same, but for the `/following` list. It scrolls the full list first, then starts at index `num_skip`.
- **`_prepare_data_for_db(...)`**: saves a `FollowFollowers` stats row.

### 5.5 `bot_folder/followers/followers_bot.py` — `class FollowersBot(InstagramBot)`
Sets `self.wait` to 4s and the scroll box XPath to `/html/body/div[5]/div/div/div[2]`.
- **`get_unfollowers()`**: logs in, scrapes the account's own *following* and *followers* lists (`_get_names`) and returns `following − followers`. As a sanity check it requires the scraped follower count to be close to the profile's follower count (within +10), otherwise it returns `False`.
- **`_get_names()`**: scrolls a followers/following dialog to the end, collects usernames (`Utils.USERNAME_IN_SCROLL_BOX`), and closes the dialog.
- **`unfollow_all_users(limit_unfollowers)`**: opens its own `/following` dialog and clicks every "Following" button (class `_8A5w5`), up to the limit, with the popup confirmation, progressive sleep and block detection.
- **`unfollow_users(user_list, to_remove_from_db, account_id, to_login, to_reverse, limit_unfollow_list, remove_not_found_users)`**: for each username it opens the profile and tries several button variants (new `FOLLOW_BTN` → `UNFOLLOW_BTN`, two legacy XPaths, "Following", "Requested") to unfollow. It counts "Follow Back" buttons (users who were following us). If `to_remove_from_db`, it deletes the user from `unfollow` only after confirming the button now says Follow / Follow Back. It can also delete not-found users. Sleeps every `ROUNDS` users. Saves a `Followers` row (the follow-back count) to the `follow_back` table.
- **`unfollow_user(username, account_id)`**: wrapper around `_unfollow_user` that closes the browser afterwards.
- **`_nav_user(user)`**: the same as the base version.
- **`unfollow_users_who_not_return_follow(unfollowers_list, account_id, to_reverse)`**: logs in, scrapes its own followers, and returns the DB users who are **not** followers. Closes the browser.

### 5.6 `bot_folder/dm/dm_bot.py` — `class DM(InstagramBot)`
- **`send_message_to_distribution_group(message, dm_users, group_name, is_schedule, to_login, account_id, group_id, limit_msg)`**: for each user (list reversed) it opens the profile, clicks **Message**, types and sends the message, removes the user from `dm_users`, and stops at `limit_msg`. If the profile shows "Requested", it cancels the request and removes the user from `dm_users` and `unfollow`. If it shows "Follow" (we no longer follow them), it removes the user from both tables. Includes block detection and the progressive sleep. Saves a `DM` stats row.
- **`send_message_to_following_list(message, is_schedule)`**: logs in, opens its own `/followers` dialog, collects usernames and calls the method above with `to_login=False`. Broken: wrong arguments (see bugs).
- **`_prepare_data_for_db(...)`**: saves the `DM` row.

### 5.7 `bot_folder/combination/combination_bot.py` — `class CombinationBot(InstagramBot)`
Module constants: `PROCESS_TIME = 12h`, `MAX_FOLLOWERS_EACH_PROCESS = 100`, `WAIT_FOR_EACH_FOLLOW = PROCESS_TIME / 100 = 432s`.
This is the most "human-like" feature: **follow ~100 users over 12 hours, then unfollow everyone the bot followed, and repeat.**
- **`combination(hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id, skip_posts, skip_users)`**: entry point. It only forwards `followers, hashtag, url, skip_posts, likes` to `automation`. Distribution, skip_users and stats saving are not implemented.
- **`automation(max_followers, hashtag, url, skip_posts, likes)`**:
  1. Logs in, opens the hashtag page or URL, clicks the first post, skips `skip_posts` posts (`_get_wanted_post`).
  2. Opens the post's **likes dialog** (`_open_likes`) and gets its scroll box (`_get_scroll_box`).
  3. Outer loop while `max_followers > 0`, middle loop up to 100 follows. In each burst it follows a random **1–4 users** (`_follow`), then sleeps `432s × burst size`.
  4. After each 100-follow cycle it unfollows **all** users in this account's `unfollow` table (`_unfollow_users`).
  5. Stops on block (with a screenshot).
- **`_scroll_down(scroll_box)`**: scrolls the dialog and returns the new height.
- **`_get_buttons(scroll_box, last_height, wait)`**: scrolls. If the height didn't change (end of the likers list), it moves to the next post and reopens the likes dialog. Returns `[(username, button), ...]` (first 11 buttons), the new height and the scroll box.
- **`_follow(button, username, settings, follow_count, wait, likes)`**: checks that the current URL is not a restriction/challenge URL, that the user has a profile picture, at least `amount_followers` followers and at least `amount_posts` posts. Then it clicks Follow, saves the user to `unfollow`, checks the blocked popup (e-mail on block), and optionally likes `likes` of that user's posts (`_like_posts`). Returns `(followed, is_blocked)`.
- **`_like_posts(wait, username, likes)`**: opens the user in a new tab, opens the first post, likes it and the next `likes-1` posts, closes the tab.
- **`_like_post(wait)`**: clicks like only if the SVG `aria-label` is "Like" (parsed with BeautifulSoup), so already-liked posts are never unliked.
- **`_open_likes(wait)`**: clicks "N likes" (`LIKES_TEXT`) or "… and others" (`OTHERS_TEXT`). If neither exists, it goes to the next post.
- **`_get_scroll_box(wait)`**: the likes dialog element (with a fallback XPath).
- **`_go_to_next_post(wait)`**: clicks the "Next" SVG.
- **`_unfollow_users(user_list, account_id, wait)`**: in a new tab, unfollows users in bursts of 1–4 with the same sleeps, counts follow-backs, stops on block, and saves a `Followers` row.
- **`_unfollow(user, account_id, wait)`**: opens the profile, tries several "Following" / "Requested" button variants plus the popup, detects a block, detects "Follow Back", and removes the user from `unfollow` only when the button changed. Returns `(follow_back, is_blocked)`.
- **`_print_username_and_time(loops)`**: helper for the progressive sleep. Unused.
- **`_prepare_data_for_db(...)`**: saves `Combination` and `AccountActions` rows. **Never called.**

### 5.8 `bot_folder/proxy.py`
Builds a Chrome extension zip (`proxy_auth_plugin.zip`) with `manifest.json` and `background.js` that sets a fixed HTTP proxy with username/password auth (`get_proxy_plugin()`). **Not used anywhere.** The proxy host and credentials are **hard-coded** in this file (and also as a `proxy` dict at the top of `main_bot.py`). `closeproxy.xpi` in the repo root is a Firefox proxy extension, also unused.

---

## 6. Database layer (`database/`)

### 6.1 `database/db.py` — `class Database`
`__init__` connects to `instabot.db`, runs `CREATE TABLE IF NOT EXISTS` for every table, commits and closes. **Every method opens and closes its own connection.** Many queries are built with `str.format` instead of parameters, so they are open to SQL injection and break on usernames containing `'`. Every feature DB class inherits from `Database`, so creating any of them re-runs the table creation.

#### Tables and column order (rows are read **by index** in the code)
| Table | Columns (index: name) | Purpose |
|---|---|---|
| `accounts` | 0 id, 1 name, 2 phone, 3 username, 4 password, 5 creation_date, 6 last_login | Stored Instagram accounts (plain-text passwords). |
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
| `proxy` | 0 id, 1 host, 2 username, 3 password, 4 port | Saved proxies. The UI lists them by username (`[2]`). |
| `website` | 0 id, 1 website, 2 modify | Random "warm-up" websites visited before login. |
| `inspect_settings` | id, page_not_found, user_not_found, block_restriction, block_change_pass, scroll_box_xml, scroll_box_close_btn, like_btn_xml, second_like_btn_xml, unsuccessful_login_txt, date_modify | Planned editable selectors. Created with defaults, never used. |

#### `Database` methods
| Method | Description |
|---|---|
| `save_account(name, phone, username, password)` | Inserts an account, then calls `_init_settings()`. |
| `_init_settings()` | Inserts the default settings row if the table is empty. |
| `get_accounts()` | All account rows. |
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

### `utils/utils.py` — `class Utils`
**Constants.** Instagram's DOM changes often, so most maintenance happens here.
- Timing: `TIME_SLEEP = 5` (sleep step in seconds, and every how many actions to sleep), `ROUNDS = 5` (the unfollow sleep interval).
- Texts and URLs: `NOT_FOUND_USER_TITLE`, `NOT_FOUND_USER_PARA`, `UNSUCCESSFUL_LOG_IN_TEXT`, `BLOCK_RESTRICTION` (`/restriction/`), `BLOCK_CHANGE_PASSWORD` (`/challenge/?next=/`), `PROFILE_IMAGE` (the default-avatar filename).
- Selectors: `RIGHT_ARROW` (Next SVG), `POST_USERNAME` (author link on an open post), `FOLLOW_BTN` (Follow/Following button div), `UNFOLLOW_BTN` ("Unfollow" span in the confirm dialog), `PROFILE_IMAGE_XPATH`, `POSTS_FOLLOWERS_FOLLOWING` (class `_ac2a` of the profile counters: [0] posts, [1] followers, [2] following), `LIKE_BUTTON` (`_aamw`), `SCROLL_BOX` (likes/followers dialog), `FIRST_POST` (`_aagw`), `CLOSE_BUTTON_SCROLL_BOX`, `USERNAME_IN_SCROLL_BOX`, `LIKES_TEXT`, `OTHERS_TEXT`, `SECOND_LIKES_BUTTON`.

**Methods**
- `_check_username_password(username, password)` (static): `False` if either is empty.
- `arithmetic_progression(time_wait, total, rows)`: prints an estimated run time in minutes for the progressive sleep scheme.
- `clean_number(text)`: converts Instagram counters to int: `"1,454"` → 1454, `"20.8K"` → 20800, `"10K"` → 10000, `"1.5M"` → 1500000. Bug: `"10M"` → 1000000 instead of 10000000.
- `clean_post_number(text)`: strips commas → int.

### `utils/schedule.py` — `class ScheduleCalc`
`calc_schedule_time(action, minutes, hours, days)` returns the delay in **seconds**. `action` is 0 = minutes, 1 = hours, 2 = days (matching the radio buttons in each tab).

---

## 9. Cross-cutting behavior

- **Anti-detection measures:** a random "warm-up" website before login; a fixed desktop user-agent; progressive sleeps (`loops × 5s` every 5 actions); random 1–4 follow bursts with long waits in Combination; only following users with a real profile picture and above follower/post thresholds; block detection (restriction/challenge URLs, the "action blocked" popup, error pages) that stops the job.
- **Follow tracking loop:** every follow from any feature goes into `unfollow` → shown in the Followers tab → unfollowed later. The DM feature also cleans up `unfollow` / `dm_users` when users are no longer followed.
- **Distribution lists:** created in Settings → filled automatically while following (Hash Tag / Location / Follow Followers tabs) → used as DM recipients in the DM tab.
- **Threads:** each job gets its own thread and its own Chrome window, so several accounts can run in parallel. There is no job manager, cancel button or progress UI. Progress is only `print`ed to the console.
- **Error reporting:** console prints, screenshots in `screen_shots/`, Mailgun e-mails (requires `MAILGUN_DOMAIN` / `MAILGUN_API` environment variables; `python-dotenv` is installed, but `load_dotenv()` is never called, so the `.env` file is not loaded automatically).
- **Ignored by git (`.gitignore`):** `instabot.db`, `screen_shots`, `images`, `.env`, `chromedriver.exe`, `geckodriver*`, `proxy_auth_plugin.zip`, `view/testing.py`, `venv`, `*.pyc`.

### Developer TODO list (from `main.py`)
- Change the Follow Followers logic to "scroll then follow", like Combination.
- Fix the case where following a user before opening their followers list returns -1 buttons.
- Finish and test "unfollow only users who don't follow back" (get the names first, close, reopen, then unfollow).
- Check how many posts a user has (partly done in Combination).
- Show Combination stats in the Statistics tab.
- Per-account action summary boxes and a dropdown in the Statistics tab.
- Display the follow-back counts (the table exists).
- Make Instagram selectors editable from the UI (the Inspect Settings window and table).

---

## 10. Known bugs and limitations
The issues below were found by reading the code. They are useful context when asked to fix or extend the project.

**Selectors and Instagram changes**
1. Many XPaths and class names are absolute or obfuscated (`_aamw`, `_ac2a`, `/html/body/div[6]/...`) and break whenever Instagram changes its UI. Some code still uses old selectors (`_9AhH0`, `coreSpriteRightPaginationArrow`, `_0imsa`, `_8A5w5`, `mt3GC`, `bIiDR`, `eiCW-`, `fr66n`, `react-root` paths). The Location bot, Follow Followers bot, DM bot and parts of Followers/Combination are likely broken against today's Instagram.
2. Selenium 3 API (`find_element_by_*`) is used; it was removed in Selenium 4.3+. The pinned `selenium==3.141.0` must be kept, or the code migrated to `find_element(By.X, ...)`.
3. The ChromeDriver version is pinned to `114.0.5735.90` and must match the installed Chrome.

**Driver and config**
4. In the desktop branch of `InstagramBot.__init__`, the `options` are **not passed** to `webdriver.Chrome`, so headless mode, the user-agent and the other flags are ignored. The `Options` import is from `selenium.webdriver.firefox.options`, even though Chrome is used.
5. `proxy_dict` is never applied. The Proxy UI fields and the `proxy` table have no effect. `Settings.save_proxy` has an inverted condition (it only saves when **all** fields are empty).
6. Hard-coded proxy credentials are committed in `bot_folder/main_bot.py` and `bot_folder/proxy.py`, and an e-mail address is hard-coded in `_send_email`. Move these to `.env` and rotate the leaked credentials.
7. If the `settings` row does not exist (no account added yet), `get_data_from_settings()` returns `None` and `InstagramBot.__init__` / `Settings._settings_data` crash on `[6]`.
8. `requirements.txt` is missing `ttkbootstrap` and `webdriver-manager`. The README says `pip install requirements.txt` (should be `-r`).

**Logic bugs**
9. `_get_followers_number` returns 3 values when the user has a profile picture and 2 otherwise. Callers unpack a fixed size: `follow_followers_bot` and `FollowersBot.get_unfollowers` expect 2, `CombinationBot._follow` and `_follow_user` expect 3. The result is a `ValueError` in many cases.
10. `_follow_user` reads `followers_num, no_use_data, no_use_d` and only follows when `followers_num != -1`.
11. Hashtag likes threshold: it is replaced by `if int(20) > int(0):`, so the "Settings → likes" value is ignored.
12. `CombinationBot.combination` ignores `to_distribution`, `group_name`, `group_id` and `skip_users`, and never saves stats (`_prepare_data_for_db` is never called, and would fail because it doesn't pass `skip_users` to `Combination`).
13. `DMDB.save_in_db` inserts into column `group_distribution`, but the table column is `group_name`, so DM stats are never saved.
14. `TabDM._send_msgs_current_account_following` creates `DM(username, password, True)` without `proxy_dict` (`TypeError`). `send_message_to_following_list` calls `send_message_to_distribution_group` with too few arguments.
15. `TabDM._remove_user` calls `dm.DMDB.remove_dm_user_from_list(...)` on the class, not an instance (missing `self`).
16. `FollowBackDB.save_in_db` uses the column `used_id` (it should be `user_id`). `FollowBackDB.get_account_data` queries `follow_followers` (copy-paste error).
17. `TabFollowers._remove_users_who_not_follow_back` passes 6 arguments to `unfollow_users`, which needs 7 (`remove_not_found_users` is missing).
18. `TabFollowers._check_form` runs `get_unfollowers()` on the GUI thread, which freezes the window. Its error message calls `len()` on an int.
19. `search_location_by_name` does not log in and calls `_follow_user()` without the required arguments.
20. `Utils.clean_number("10M")` returns 1,000,000 instead of 10,000,000.
21. `Database.get_user_id` / `get_group_id_by_group_name_and_id` crash with `TypeError` when nothing is found (`None[0]`).
22. `screen_shots/` must exist or `_screen_shot` fails. `_send_email` fails if the screenshot is missing.

**Security and quality**
23. SQL is built with `str.format` in many queries (injection, quoting bugs). Use `?` parameters.
24. Instagram passwords are stored in plain text in SQLite and shown in the Accounts list.
25. Wide `try/except Exception: pass` blocks hide most failures. There are no tests, no logging framework and no way to cancel a running job.
26. Automating Instagram actions violates Instagram's Terms of Use and can get accounts restricted or banned. The block-detection code exists for this reason.

---

## 11. Quick file index
| Path | Contains |
|---|---|
| `main.py` | App entry point |
| `view/layout.py` | Main window, menu, tabs |
| `view/accounts.py` | Accounts CRUD window |
| `view/settings.py` | Settings window (thresholds, headless, distribution lists, proxies, websites) |
| `view/inspect_settings.py` | Selector-editor window (stub) |
| `view/tab_hash_tag.py` | Hash Tag tab |
| `view/tab_location.py` | Location tab |
| `view/tab_follow_followers.py` | Follow Followers tab |
| `view/tab_followers.py` | Followers / unfollow tab |
| `view/tab_dm.py` | DM tab |
| `view/tab_combination.py` | Combination tab |
| `view/tab_statistics.py` | Statistics tab |
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
| `utils/utils.py` | Selectors, constants, number parsing |
| `utils/schedule.py` | Schedule delay calculator |

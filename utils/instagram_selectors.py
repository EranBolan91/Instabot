"""How the bots find things on Instagram's pages: the one source of truth.

Selectors live in instagram_selectors.json next to this file. Bots refer to
them by key, e.g. ``S.click(driver, "post.like_button")``, never by a raw
XPath or class name. When Instagram changes, fix the JSON (or use the
Inspect Settings window), not the bot code.

Each selector has a list of ways to find it, tried in order; the first way
that finds a visible element wins:
  {"css": ...} {"xpath": ...} {"name": ...}  plain Selenium lookups
  {"text": regex}        the smallest visible element whose whole text matches
  {"scrollable": css}    the scrolling part inside the (last) element matching css
"""
import json
import time
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

PATH = Path(__file__).with_name("instagram_selectors.json")

_TEXT_JS = r"""
const root = arguments[0] || document, re = new RegExp(arguments[1], 'i');
const visible = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
const hits = [...root.querySelectorAll('*')].filter(e =>
  re.test((e.innerText || '').trim().replace(/\s+/g, ' ')) && visible(e));
return hits.filter(e => ![...e.children].some(c => hits.includes(c)));
"""

_SCROLLABLE_JS = r"""
const boxes = [...(arguments[0] || document).querySelectorAll(arguments[1])];
const box = boxes[boxes.length - 1];
if (!box) return [];
return [...box.querySelectorAll('div')].filter(d =>
  /(auto|scroll)/.test(getComputedStyle(d).overflowY) && d.scrollHeight > d.clientHeight + 5).slice(0, 1);
"""

# for elements found inside an svg or a text span: the part that takes the click
_CLICKABLE_JS = "return arguments[0].closest('a, button, [role=button], [role=link]') || arguments[0];"

# one list row per username link: walk up from the link until the row's button is inside
_ROWS_JS = r"""
const links = arguments[0], buttonCss = arguments[1], buttonTexts = arguments[2];
return links.map(link => {
  let row = link.parentElement, button = null;
  for (let i = 0; i < 10 && row && !button; i++, row = row.parentElement) {
    const others = [...row.querySelectorAll('a[href]')].filter(a => a.getAttribute('href') !== link.getAttribute('href')
      && /^\/[^\/]+\/$/.test(a.getAttribute('href')) && (a.innerText || '').trim());
    if (others.length) break;  // reached a container of several rows
    button = [...row.querySelectorAll(buttonCss)].find(b => buttonTexts.includes((b.innerText || '').trim())) || null;
  }
  return [(link.innerText || '').trim().split('\n')[0], button];
});
"""

# exact number from a counter: Instagram puts it in a title attribute for big numbers ("686M")
_COUNT_JS = r"""
const el = arguments[0], titled = el.querySelector('[title]');
const title = titled && titled.getAttribute('title');
if (title && /^[\d.,]+$/.test(title.trim())) return title.trim();
const m = (el.innerText || '').trim().match(/^[\d.,KMB]+/i);
return m ? m[0] : null;
"""


class Selectors:
    def __init__(self, path=PATH):
        self.path = Path(path)
        self.reload()

    # ---------- The data ----------

    def reload(self):
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data):
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.reload()

    def entry(self, key):
        group, name = key.split(".")
        return self.data["selectors"][group][name]

    def ways(self, key):
        return self.entry(key)["find"]

    def keys(self):
        return ["{}.{}".format(group, name) for group, entries in self.data["selectors"].items() for name in entries]

    def text(self, name):
        return self.data["texts"][name]

    def url(self, name, **values):
        return self.data["urls"][name].format(**values)

    # ---------- Finding ----------

    def find_all(self, root, key):
        """Every visible match of the first way that matches anything; [] if none does."""
        driver = root.parent if isinstance(root, WebElement) else root
        scope = root if isinstance(root, WebElement) else None
        for way in self.ways(key):
            try:
                found = self._find_way(driver, scope, way)
                found = [element for element in found if self._displayed(element)]
            except (StaleElementReferenceException, NoSuchElementException):
                found = []
            if found:
                return found
        return []

    def find(self, root, key, timeout=0):
        """The first match, waiting up to ``timeout`` seconds; None if there is none."""
        deadline = time.time() + timeout
        while True:
            found = self.find_all(root, key)
            if found:
                return found[0]
            if time.time() >= deadline:
                return None
            time.sleep(0.5)

    def get(self, root, key, timeout=7):
        """Like find(), but raises NoSuchElementException, like Selenium's own lookups."""
        element = self.find(root, key, timeout)
        if element is None:
            raise NoSuchElementException("Instagram selector '{}' found nothing".format(key))
        return element

    def exists(self, root, key, timeout=0):
        return self.find(root, key, timeout) is not None

    def clickable(self, element):
        """For an svg icon or a text span: the link/button around it, which takes the click."""
        return element.parent.execute_script(_CLICKABLE_JS, element)

    def click(self, root, key, timeout=7):
        target = self.clickable(self.get(root, key, timeout))
        target.click()
        return target

    def count(self, root, key, timeout=7):
        """The number in a counter like "521 followers", as text ("521", "12.5K"); None if not found."""
        element = self.find(root, key, timeout)
        if element is None:
            return None
        return element.parent.execute_script(_COUNT_JS, element)

    def dialog_rows(self, driver, timeout=7):
        """The open list's rows as (username, button or None), in order.

        Reads each row on its own, so a row without a Follow button (e.g. in
        your followers list) can't shift the buttons onto the wrong users.
        """
        if not self.exists(driver, "dialog.box", timeout):
            return []
        # e.g. a likes list opened from a post: the newest dialog is on top
        box = self.find_all(driver, "dialog.box")[-1]
        links = self.find_all(box, "dialog.user_link")
        if not links:
            return []
        button_css = next(way["css"] for way in self.ways("dialog.row_button") if "css" in way)
        rows = driver.execute_script(_ROWS_JS, links, button_css, self.text("row_button_texts"))
        seen, unique = set(), []
        for username, button in rows:
            if username and username not in seen:
                seen.add(username)
                unique.append((username, button))
        return unique

    def scroll_to_bottom(self, driver, element):
        """Scroll a list down one screen-full; returns its new scroll height."""
        return driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);"
                                     "return arguments[0].scrollHeight;", element)

    # ---------- Internals ----------

    @staticmethod
    def _find_way(driver, scope, way):
        root = scope or driver
        if "css" in way:
            return root.find_elements(By.CSS_SELECTOR, way["css"])
        if "xpath" in way:
            xpath = way["xpath"]
            if scope is not None and xpath.startswith("//"):
                xpath = "." + xpath  # search inside the element, not the whole page
            if scope is not None and xpath.startswith("(//"):
                xpath = "(.//" + xpath[3:]
            return root.find_elements(By.XPATH, xpath)
        if "name" in way:
            return root.find_elements(By.NAME, way["name"])
        if "text" in way:
            return driver.execute_script(_TEXT_JS, scope, way["text"]) or []
        if "scrollable" in way:
            return driver.execute_script(_SCROLLABLE_JS, scope, way["scrollable"]) or []
        raise ValueError("Unknown way to find an element: {}".format(way))

    @staticmethod
    def _displayed(element):
        try:
            return element.is_displayed()
        except StaleElementReferenceException:
            return False


# The instance every bot uses.
S = Selectors()

"""The selectors against small copies of Instagram's page structure (as seen on 2026-10-25).

They run in headless Chrome. This checks the selectors' logic (e.g. that the
post's Like isn't confused with a comment's); whether Instagram still looks
like this is what Inspect Settings > "Check selectors" is for.
"""
import json

import pytest
from selenium.common.exceptions import NoSuchElementException

from utils.instagram_selectors import PATH, Selectors

LOGIN = """
<form id="login_form"><input name="email" type="text"><input name="pass" type="password">
<input type="submit"></form>
<div>The login information you entered is incorrect. <a href="#">Find your account and log in.</a></div>
"""

PROFILE = """
<main><header>
  <img alt="bathena's profile picture" src="https://x/123_real_n.jpg">
  <h2>bathena</h2>
  <ul><li><span><span>5</span> posts</span></li>
      <li><a href="#" role="link"><span><span title="1,521">1,521</span> followers</span></a></li>
      <li><a href="#" role="link"><span><span>594</span> following</span></a></li></ul>
  <button type="button">Following</button><div role="button">Message</div>
</header>
<div><button>Follow</button> suggested account</div>
<a href="/bathena/p/AAA/">post A</a><a href="/bathena/p/BBB/">post B</a>
</main>
"""

# a followers list: row 3 has no Follow button (you follow them already)
FOLLOWERS = """
<main><a href="/me/p/X/">post</a></main>
<div role="dialog"><h1>Followers</h1><div style="overflow-y:auto; height:100px">
  <div><a href="/anna/"><img alt="anna's profile picture"></a>
       <div><a href="/anna/"><span>anna</span></a><div>Anna A</div></div>
       <button>Follow</button><button>Remove</button></div>
  <div><a href="/bob/"><img></a><div><a href="/bob/"><span>bob</span></a></div>
       <div role="button">Following</div><button>Remove</button></div>
  <div><a href="/carol/"><img></a><div><a href="/carol/"><span>carol</span></a></div>
       <button>Remove</button></div>
  <div><a href="/dan/"><img></a><div><a href="/dan/"><span>dan</span></a></div>
       <button>Follow</button><button>Remove</button></div>
  <div style="height:400px"></div>
</div><svg aria-label="Close" role="img" width="10" height="10"><title>Close</title></svg></div>
"""

POST = """
<div role="dialog">
  <a href="/j.lulu/"><img></a><a href="/j.lulu/">j.lulu</a> <button>Follow</button>
  <div class="comments">
    <div><a href="/fan1/">fan1</a> nice <div role="button"><svg aria-label="Like" width="9" height="9"></svg></div></div>
    <div><a href="/fan2/">fan2</a> wow <div role="button"><svg aria-label="Like" width="9" height="9"></svg></div></div>
  </div>
  <section class="actions">
    <div role="button" id="post-like"><svg aria-label="Like" width="24" height="24"></svg></div>
    <div role="button"><svg aria-label="Comment" width="24" height="24"></svg></div>
    <div role="button"><svg aria-label="Save" width="24" height="24"></svg></div>
  </section>
  <div role="button"><span>368K likes</span></div>
  <textarea aria-label="Add a comment…" placeholder="Add a comment…"></textarea>
  <button id="next"><svg aria-label="Next" width="20" height="20"></svg></button>
</div>
"""

LIKED_POST = POST.replace('id="post-like"><svg aria-label="Like"', 'id="post-like"><svg aria-label="Unlike"')

DM = """<main><div role="textbox" contenteditable="true" style="height:20px">x</div></main>"""

NOT_FOUND = """<main><span>Sorry, this page isn't available.</span><span>The link you followed may be broken.</span></main>"""


@pytest.fixture(scope="module")
def driver():
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    try:
        browser = webdriver.Chrome(options=options)
    except Exception as error:  # no Chrome or no network for the driver download
        pytest.skip("headless Chrome isn't available: {}".format(error))
    yield browser
    browser.quit()


@pytest.fixture
def page(driver, tmp_path):
    def load(html):
        path = tmp_path / "page.html"
        path.write_text("<!doctype html><html><body>{}</body></html>".format(html), encoding="utf-8")
        driver.get(path.as_uri())
        return driver
    return load


S = Selectors()


# ---------- The file itself ----------

def test_every_selector_is_well_formed():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    allowed = {"css", "xpath", "name", "text", "scrollable"}
    for key in S.keys():
        entry = S.entry(key)
        assert entry["what"], key
        assert entry["find"], key
        for way in entry["find"]:
            assert len(way) == 1 and set(way) <= allowed, (key, way)
        assert "checked" in entry, key
    assert set(data) == {"about", "urls", "texts", "selectors"}


def test_urls_and_texts():
    assert S.url("profile", username="bathena") == "https://www.instagram.com/bathena/"
    assert S.url("hashtag", tag="sunset") == "https://www.instagram.com/explore/tags/sunset/"
    assert "Follow" in S.text("row_button_texts")


def test_save_round_trip(tmp_path):
    copy = tmp_path / "selectors.json"
    copy.write_text(PATH.read_text(encoding="utf-8"), encoding="utf-8")
    selectors = Selectors(copy)
    data = selectors.data
    data["selectors"]["login"]["username_input"]["find"] = [{"name": "user"}]
    selectors.save(data)
    assert Selectors(copy).ways("login.username_input") == [{"name": "user"}]


# ---------- Against the page copies ----------

def test_login_page(page):
    driver = page(LOGIN)
    assert S.get(driver, "login.username_input").get_attribute("name") == "email"
    assert S.get(driver, "login.password_input").get_attribute("type") == "password"
    assert S.exists(driver, "login.error_message")
    assert not S.exists(driver, "login.logged_in_marker")


def test_profile_counters_and_buttons(page):
    driver = page(PROFILE)
    assert S.count(driver, "profile.posts_counter") == "5"
    assert S.count(driver, "profile.followers_counter") == "1,521"  # the exact number from the title
    assert S.count(driver, "profile.following_counter") == "594"
    # clicking a counter clicks its link, not the inner span
    assert S.clickable(S.get(driver, "profile.followers_counter")).tag_name == "a"
    assert S.get(driver, "profile.following_button").text == "Following"
    assert S.get(driver, "profile.message_button").text == "Message"
    # you follow bathena: the suggested account's Follow further down must not count
    assert not S.exists(driver, "profile.follow_button")
    assert S.get(driver, "profile.picture").get_attribute("src").endswith("_real_n.jpg")
    assert S.get(driver, "profile.first_post").get_attribute("href").endswith("/bathena/p/AAA/")


def test_followers_list_is_read_row_by_row(page):
    driver = page(FOLLOWERS)
    rows = S.dialog_rows(driver)
    names = [name for name, _ in rows]
    buttons = {name: (button.text if button else None) for name, button in rows}
    assert names == ["anna", "bob", "carol", "dan"]
    # carol has no Follow button: dan's must not slide onto her
    assert buttons == {"anna": "Follow", "bob": "Following", "carol": None, "dan": "Follow"}
    scroll = S.get(driver, "dialog.scroll_area")
    assert S.scroll_to_bottom(driver, scroll) > 100


def test_post_like_is_the_posts_own_heart(page):
    driver = page(POST)
    like = S.get(driver, "post.like_button")
    assert S.clickable(like).get_attribute("id") == "post-like"  # not a comment's heart
    assert not S.exists(driver, "post.unlike_button")
    assert S.get(driver, "post.author_link").text == "j.lulu"
    assert S.get(driver, "post.author_follow_button").text == "Follow"
    assert S.count(driver, "post.likes_link") == "368K"
    assert S.get(driver, "post.comment_input").tag_name == "textarea"
    assert S.clickable(S.get(driver, "post.next_button")).get_attribute("id") == "next"


def test_liked_post_has_no_like_button(page):
    driver = page(LIKED_POST)
    assert not S.exists(driver, "post.like_button")
    assert S.exists(driver, "post.unlike_button")


def test_dm_box_and_not_found_page(page):
    driver = page(DM)
    assert S.get(driver, "dm.message_input").get_attribute("contenteditable") == "true"
    driver = page(NOT_FOUND)
    assert S.exists(driver, "profile.not_found_title")


def test_get_raises_like_selenium_and_find_returns_none(page):
    driver = page("<p>empty</p>")
    assert S.find(driver, "post.like_button") is None
    with pytest.raises(NoSuchElementException):
        S.get(driver, "post.like_button", timeout=0)

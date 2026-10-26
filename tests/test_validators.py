from ui.core import validators


def test_required():
    assert validators.required("  ", "Name") == "Name is required"
    assert validators.required("a", "Name") is None


def test_no_spaces():
    assert validators.no_spaces("my user", "Username")
    assert validators.no_spaces("my_user", "Username") is None


def test_http_url():
    assert validators.http_url("https://www.ynet.co.il") is None
    assert validators.http_url("http://example.com/page?x=1") is None
    assert validators.http_url("www.example.com")
    assert validators.http_url("")
    assert validators.http_url("https:// spaced.com")


def test_positive():
    assert validators.positive(0, "Port")
    assert validators.positive(1, "Port") is None


def test_unique_ignores_case_and_spaces():
    assert validators.unique(" Alice ", ["alice", "bob"], "Account")
    assert validators.unique("carol", ["alice", "bob"], "Account") is None
    assert validators.unique("", ["alice"], "Account") is None


def test_proxy_pair():
    assert validators.proxy_pair("", 0) is None
    assert validators.proxy_pair("1.2.3.4", 8080) is None
    assert validators.proxy_pair("1.2.3.4", 0)
    assert validators.proxy_pair("", 8080)


def test_first_error():
    assert validators.first_error(None, "a", "b") == "a"
    assert validators.first_error(None, None) is None

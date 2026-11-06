from src.data.audit_author_bridge import arxiv_author_keys, name_key


def test_name_key_accents_and_case():
    assert name_key("José  Müller") == ("muller", "jose")
    assert name_key("J. Smith") == ("smith", "j")


def test_name_key_rejects_single_token():
    assert name_key("Plato") is None


def test_arxiv_author_list_with_affiliations_and_and():
    keys = arxiv_author_keys("Ana Lopez (MIT, Cambridge), Bo Chen and C. D'Souza")
    assert keys == [("lopez", "ana"), ("chen", "bo"), ("dsouza", "c")]


def test_compatible_names():
    from src.data.audit_author_bridge import compatible
    assert compatible(("wang", "yi"), ("wang", "y"))
    assert compatible(("wang", "yi"), ("wang", "yi"))
    assert not compatible(("wang", "yi"), ("wang", "yu"))
    assert not compatible(("wang", "y"), ("li", "y"))


def test_confirm_needs_strong_coauthor_evidence():
    from src.data.audit_author_bridge import confirm
    own = {("wang", "yi")}
    co = {"li": {("li", "jun")}, "chen": {("chen", "b")}}
    assert confirm([("wang", "y"), ("li", "jun")], own, co) == (True, 1, 1)
    assert confirm([("wang", "yi"), ("chen", "bo")], own, co) == (True, 0, 1)
    assert confirm([("zhao", "q"), ("li", "jun")], own, co) == (False, 0, 0)

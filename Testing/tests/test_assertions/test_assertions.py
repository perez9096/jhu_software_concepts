from Testing.src.test_functions import assertion_examples

def test_uppercase():
    assert "I love python".upper() == "I LOVE PYTHON"

def test_reversed():
    assert list(reversed([1, 2, 3, 4])) == [4, 3, 2, 1]

def test_input(monkeypatch):
    # monkeypatch the "input" function, so that it returns "Cats"
    # This simulates the user entering "Cats" in the terminals
    monkeypatch.setattr('builtins.input', lambda _: "Cats")

    assert assertion_examples.user_input().lower() == "cats"


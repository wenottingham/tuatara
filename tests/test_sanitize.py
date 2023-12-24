from tuatara.sanitize import sanitize_artist, sanitize_album


def test_sanitize_artist():
    data = (
        ("One & Two", "one and two"),
        ("A+B", "a and b"),
        ("C + w°w", "c and w°w"),
        ("HYPER", "hyper"),
    )
    for before, after in data:
        assert sanitize_artist(before) == after


def test_sanitize_album():
    data = (
        ("Black+White", "black and white"),
        ("Wow (disc 2)", "wow"),
        ("Now (disc 1: The NeverEnding)", "now"),
        ("Disc 2: Fun", "disc 2: fun"),
    )
    for before, after in data:
        assert sanitize_album(before) == after

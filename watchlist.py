WATCHLIST = [
    "Pace",
]


def is_watchlisted(title: str) -> bool:
    title = title.lower()

    return any(model.lower() in title for model in WATCHLIST)

from backend.sources.base import BaseSource
from backend.sources.hmt_in import HMTInSource
from backend.sources.hmt_store import HMTStoreSource


def get_sources() -> list[BaseSource]:
    """
    Return every product source known to the application.
    """

    return [
        HMTInSource(),
        HMTStoreSource(),
    ]
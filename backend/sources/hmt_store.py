from backend.sources.base import BaseSource


class HMTStoreSource(BaseSource):
    @property
    def source_name(self) -> str:
        return "hmt_store"

    async def discover(self):
        return []
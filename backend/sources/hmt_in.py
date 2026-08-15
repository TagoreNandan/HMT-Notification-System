from backend.sources.base import BaseSource


class HMTInSource(BaseSource):
    @property
    def source_name(self) -> str:
        return "hmt_in"

    async def discover(self):
        return []
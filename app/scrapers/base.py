class BaseJobSource:
    name: str

    async def fetch_jobs(self) -> list[dict]:
        raise NotImplementedError

    def normalize(self, raw: dict) -> dict:
        raise NotImplementedError

    async def collect(self) -> list[dict]:
        raw_jobs = await self.fetch_jobs()
        return [self.normalize(item) for item in raw_jobs]
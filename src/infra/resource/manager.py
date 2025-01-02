import asyncio
import aioboto3
from typing import Dict
from .handler import *
from src.config.conf import (
    PROBE_CYCLE_SECS,
    SQS_QUEUE_URL,
)
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class ResourceManager:
    def __init__(self, resources: Dict[str, ResourceHandler]):
        self.resources: Dict[str, ResourceHandler] = resources

    def get(self, resource: str) -> ResourceHandler:
        if resource not in self.resources:
            raise ValueError(f'ResourceHandler "{resource}" not found.')

        return self.resources[resource]

    async def initial(self):
        for resource in self.resources.values():
            await resource.initial()

    async def probe(self):
        for resource in self.resources.values():
            try:
                if not resource.timeout():
                    log.info(f' ==> probing {resource.__class__.__name__}')
                    await resource.probe()
                else:
                    await resource.close()

            except Exception as e:
                log.error('probe error: %s', e)

    # Regular activation to maintain connections and connection pools

    async def keeping_probe(self):
        while True:
            await asyncio.sleep(PROBE_CYCLE_SECS)
            await self.probe()

    async def close(self):
        for resource in self.resources.values():
            await resource.close()


session = aioboto3.Session()
resource_manager = ResourceManager({
    'sqs_rsc': SQSResourceHandler(session=session, label='failed pub events DLQ', queue_url=SQS_QUEUE_URL),
})

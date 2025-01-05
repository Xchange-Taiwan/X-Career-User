import json
import asyncio
import aioboto3
from botocore.exceptions import ClientError
from typing import Callable, Dict
from src.infra.resource.handler import SQSResourceHandler
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class SqsMqAdapter:
    def __init__(self, sqs_rsc: SQSResourceHandler):
        self.sqs_rsc = sqs_rsc
        self.sqs_label = self.sqs_rsc.label

    async def publish_message(self, event: Dict, group_id: str):
        try:
            sqs_client = await self.sqs_rsc.access()
            message_body = json.dumps(event)
            response = await sqs_client.send_message(
                QueueUrl=self.sqs_rsc.queue_url,
                MessageBody=message_body,
                MessageGroupId=group_id,
            )

            log.info('SQS[%s]: msg is sent. msg ID: %s',
                     self.sqs_label, response['MessageId'])
            return response

        except Exception as e:
            log.error('SQS[%s]: Error sending message to SQS: %s',
                      self.sqs_label, str(e))
            raise e



    async def subscribe_messages(self, callee: Callable, **kwargs):
        pass

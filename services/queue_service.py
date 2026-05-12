from datetime import datetime, timezone
from uuid import uuid4

import aio_pika
from aio_pika import DeliveryMode, Message

from conf.settings import settings
from shcemas.queue_schema import (
    AnalysisTaskMessage,
    AnalysisTaskType,
    EnqueueTaskResponse,
)
from shcemas.task_schema import TaskStatus


class RabbitMQPublisher:
    def __init__(self, url: str, queue_name: str) -> None:
        # 你要做的事：
        # 1. 保存 RabbitMQ URL
        # 2. 保存队列名
        # 3. 不要在初始化里立刻建立网络连接
        self.url = url
        self.queue_name = queue_name



    async def publish(self, message: AnalysisTaskMessage) -> None:
        # 你要做的事：
        # 1. 建立 RabbitMQ 连接
        # 2. 声明 durable queue
        # 3. 把 message 序列化为 JSON bytes
        # 4. 使用 persistent delivery mode 投递
        # 5. 关闭连接或交给连接上下文管理
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(self.queue_name,durable=True)
            await channel.default_exchange.publish(
                Message(
                    body=self._message_body(message),
                    delivery_mode = DeliveryMode.PERSISTENT,
                    content_type='application/json',
                ),
                routing_key=self.queue_name,
            )





    def _message_body(self, message: AnalysisTaskMessage) -> bytes:
        # 你要做的事：
        # 1. 使用 Pydantic JSON 序列化
        # 2. 编码成 UTF-8 bytes
        # 3. 不要手写字符串拼接 JSON
        return message.model_dump_json().encode("utf-8")




class QueueService:
    def __init__(self, publisher: RabbitMQPublisher | None = None) -> None:
        # 你要做的事：
        # 1. 支持注入 publisher，方便本地测试
        # 2. 没有注入时根据 settings 创建 RabbitMQPublisher
        # 3. 不要在这里执行分析逻辑
        self.publisher = publisher or RabbitMQPublisher(
            url=settings.RABBITMQ_URL,
            queue_name=settings.RABBITMQ_QUEUE_NAME,
        )



    async def enqueue_analysis_task(
        self,
        task_id: str,
        dataset_id: str,
    ) -> EnqueueTaskResponse:
        # 你要做的事：
        # 1. 构造 AnalysisTaskMessage
        # 2. 调用 publisher.publish
        # 3. 返回 EnqueueTaskResponse
        # 4. 不要在这里读取 dataset 或执行分析
        message = AnalysisTaskMessage(
            task_id=task_id,
            dataset_id=dataset_id,
            task_type=AnalysisTaskType.full_analysis,
            requested_at=datetime.now(timezone.utc),
            trace_id=str(uuid4()),
        )
        await self.publisher.publish(message)
        return EnqueueTaskResponse(
            task_id=task_id,
            dataset_id=dataset_id,
            status=TaskStatus.queued,
            queue_name=settings.RABBITMQ_QUEUE_NAME,
            enqueued=True,
        )




queue_service = QueueService()
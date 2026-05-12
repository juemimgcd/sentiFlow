 # Day 9：RabbitMQ 接管任务投递

## 今天的总目标

- 把 Day 8 已经跑通的完整同步分析链，从 HTTP 请求里解耦出来
- 让创建任务之后的第一件事变成“写任务记录 + 投递队列消息”，而不是立刻跑完分析
- 建立最小 RabbitMQ 消息契约，让 worker 后续只消费稳定结构，不猜接口参数
- 让任务状态从 `pending` 能够进入 `queued`，为后续 `running`、`success`、`failed` 留出状态流转
- 为 Day 10 的 worker 消费和执行完整分析链准备清楚的输入

## 今天结束前，你必须拿到什么

- 一条真正清楚的 `create task -> enqueue RabbitMQ message -> queued -> wait for worker` 主链
- 一套 Day 9 最小队列消息 schema
- 一套 Day 9 最小 RabbitMQ publisher / queue service 设计
- 一份能讲清楚“投递任务”和“执行任务”边界的说明
- 一份当前仓库里 Day 9 应该新增哪些文件、哪些文件只做小改的落点说明
- 一份不依赖真实 worker 的本地验证方式

---

## Day 9 一图总览

一句话总结：

> Day 9 不是让后台 worker 把分析跑完，而是先让任务可靠地进入队列。

主链路先压缩成这一条：

```text
client creates task
-> FastAPI validates dataset
-> PostgreSQL stores task metadata
-> RabbitMQ receives analysis task message
-> task status becomes queued
-> Day 10 worker consumes message
```

今天最不能混淆的 5 件事：

- Day 8 的终点是完整同步分析链
- Day 9 的重点是任务投递，不是任务执行
- RabbitMQ 消息里只放任务索引，不放原始文本和分析结果
- `queued` 表示任务已经进入异步执行入口，不表示分析已经完成
- Day 10 才让 worker 消费消息并真正执行预处理、情感、主题和归因

---

## 为什么这一天重要

前面几天已经让 SentiFlow 有了：

- 数据集导入
- 任务创建
- 文本预处理
- 情感分析
- 关键词和主题分析
- 问题归因和代表样本

这些能力如果都在 HTTP 请求里同步跑，早期练习可以接受，但一旦进入真实批量舆情场景，就会出现几个问题：

```text
请求等待时间越来越长
用户关掉页面后任务是否继续执行不清楚
多个大任务同时进来时接口容易被拖住
失败重试和进度追踪没有稳定入口
```

所以 Day 9 的价值在于：

> 把“请求触发分析”改造成“请求登记任务并投递消息”。

这一步完成后，系统才真正开始进入异步任务模型：

```text
API 负责接收请求和登记任务
RabbitMQ 负责削峰和排队
worker 负责后台执行
PostgreSQL 负责任务事实
Redis 后续负责运行态进度
```

Day 9 只先把 RabbitMQ 这一层接进来。  
如果今天把 worker、Redis、结果持久化全部一起写，会把 Day 9 做得过重，也会让问题难以定位。

---

## Day 9 整体架构

```mermaid
flowchart LR
    A[POST /tasks] --> B[validate dataset]
    B --> C[create analysis_task]
    C --> D[build queue message]
    D --> E[publish to RabbitMQ]
    E --> F[mark task queued]
    F --> G[return task_id and queued status]
    E --> H[Day 10 worker consumes]
```

再压缩成仓库里真正的文件落点：

```text
router/tasks.py
-> services/task_service.py
-> crud/task_crud.py
-> services/queue_service.py
-> shcemas/queue_schema.py
-> conf/settings.py
-> pyproject.toml
-> Day 10 再新增 worker 消费入口
```

---

## 今天的边界要讲透

Day 9 解决的是：

```text
怎样定义分析任务消息
怎样连接 RabbitMQ
怎样把任务创建后的消息投递出去
怎样把任务状态推进到 queued
怎样让本地在没有 worker 时也能验证消息构建和投递入口
```

Day 9 不解决的是：

```text
worker 怎样消费消息
worker 怎样执行完整分析链
Redis 怎样记录阶段和进度
失败任务怎样自动重试
分析结果怎样完整持久化
前端怎样实时轮询状态
```

### 今天之后，各层职责应该怎么理解

| 位置 | Day 9 负责什么 | Day 9 不负责什么 |
| --- | --- | --- |
| `router/tasks.py` | 创建任务后触发队列投递，返回 queued 状态 | 在接口里跑完整分析链 |
| `services/task_service.py` | 继续构建任务创建载荷和响应 | 直接连接 RabbitMQ |
| `services/queue_service.py` | 构建消息并投递 RabbitMQ | 消费消息、执行分析 |
| `shcemas/queue_schema.py` | 定义队列消息和投递响应契约 | 承担 RabbitMQ 连接细节 |
| `crud/task_crud.py` | 提供最小任务状态更新方法 | 执行业务分析 |
| `conf/settings.py` | 提供 RabbitMQ 连接和队列配置 | 保存运行态进度 |
| `pyproject.toml` | 声明 RabbitMQ 客户端依赖 | 管理 broker 部署 |

### 对当前仓库的处理原则

基于当前项目实际状态，Day 9 的处理建议是：

| 分类 | 目录 / 文件 | 处理方式 |
| --- | --- | --- |
| 直接复用 | `router/tasks.py` `services/task_service.py` `crud/task_crud.py` | 在任务创建链路上接队列投递 |
| 小改接入 | `conf/settings.py` `pyproject.toml` `shcemas/task_schema.py` | 增加 RabbitMQ 配置和依赖，复用已有 `queued` 状态 |
| 新增文件 | `services/queue_service.py` `shcemas/queue_schema.py` | 作为 Day 9 主线落点 |
| 暂不新增 | `worker/` 或 `workers/` | Day 10 再真正接消费和执行 |

这里要注意当前仓库目录名是 `shcemas/`。  
Day 9 仍然沿用这个目录，不顺手改成 `schemas/`，避免把异步化任务和目录迁移混在一起。

---

## 今天开始，先不要急着写 worker

Day 9 最容易犯的错误就是：

- 一接 RabbitMQ，就同时写 producer 和 consumer
- 一看到任务状态，就把 Redis 进度一起接进来
- 一想到任务执行，就把预处理、情感、主题、归因全部搬进新文件
- 一想到队列可靠性，就立刻做事务消息、死信队列、重试调度和补偿任务

这些都不是 Day 9 的重点。

今天真正要解决的是：

> API 层怎样把分析任务登记下来，并把一个稳定消息投递给 RabbitMQ。

如果这件事没单独做稳，Day 10 写 worker 时会同时面对：

- 不清楚消息长什么样
- 不清楚任务状态什么时候变成 queued
- 不清楚 worker 应该拿 `task_id` 还是拿整包数据
- 不清楚 RabbitMQ 连接和业务执行该放在哪层

所以 Day 9 的关键词不是“后台执行”，而是：

```text
消息契约
任务投递
队列入口
状态 queued
HTTP 解耦
Day 10 handoff
```

---

## 第 1 层：Day 9 的本质是什么

Day 1 定的是：

```text
边界
```

Day 2 定的是：

```text
任务流和信息架构
```

Day 3 定的是：

```text
后端应用骨架
```

Day 4 定的是：

```text
输入进入系统并挂到任务上
```

Day 5 到 Day 8 定的是：

```text
同步分析主链
```

Day 9 定的是：

```text
同步触发怎样变成异步投递
```

也就是说，Day 9 不是继续增加分析能力。  
今天开始，系统要回答的是另一个工程问题：

```text
用户创建任务以后，系统怎样先接受任务，再慢慢执行任务
```

这一步走通后，SentiFlow 的请求链路就从：

```text
POST /tasks/{task_id}/sentiment
-> 在请求里跑模型
-> 同步返回结果
```

逐步变成：

```text
POST /tasks
-> 写入任务
-> 投递消息
-> 返回 queued
-> worker 后台执行
```

这才是面向批量评论分析更合理的任务模型。

---

## 第 2 层：Day 9 的主链一定要从任务创建出发

今天你要先把 Day 9 的主链牢牢记成这样：

```text
create task request
-> validate dataset
-> create task row
-> build AnalysisTaskMessage
-> publish RabbitMQ message
-> update task status to queued
-> return queued response
```

这里最重要的不是 RabbitMQ API 怎么调用，  
而是你要看清楚：

- Day 9 接的是任务创建链路
- Day 9 投递的是任务索引，不是分析结果
- Day 9 不重新读取上传文件
- Day 9 不执行情感、主题、归因
- Day 9 不负责展示最终结果

### 为什么一定要从任务创建出发

因为异步任务模型里，真正需要解耦的是：

```text
用户提交任务
```

和：

```text
系统执行任务
```

如果 Day 9 还只是在 `POST /tasks/{task_id}/sentiment`、`POST /tasks/{task_id}/topics` 这些同步分析接口后面补投递消息，系统仍然没有完成真正转型。

最稳的方式应该是：

```text
POST /tasks
-> 创建 task
-> task 进入 queued
```

后续由 worker 决定是否执行：

```text
preprocess
-> sentiment
-> topics
-> issues
```

这也让接口语义更清楚：  
创建任务就是把批量分析任务放入系统，分析执行交给后台。

---

## 第 3 层：为什么消息里不能放完整文本和结果

很多人第一次接队列时，会本能地把所有东西都塞进消息：

```text
dataset metadata
raw_text
all samples
analysis options
intermediate results
```

这会带来几个问题。

### 问题 1：消息过大，队列变成数据存储

RabbitMQ 适合传递任务通知和小型消息，不适合承载大批量评论正文。  
如果把全部文本塞进消息，队列会承担不该承担的存储压力。

### 问题 2：消息和数据库事实容易不一致

任务真实状态在 PostgreSQL。  
如果消息里复制了一份完整数据，后续数据集记录改动、任务状态改动、结果回写都容易出现口径不一致。

### 问题 3：worker 后续扩展更难

worker 应该通过 `task_id` 去加载任务事实和关联数据集。  
这样 Day 10、Day 11、Day 12 才能围绕同一个任务事实继续推进。

### Day 9 最稳的消息结构

消息里先只放这些：

```text
task_id
dataset_id
task_type
requested_at
trace_id
```

也就是说，RabbitMQ 消息只是告诉 worker：

```text
有一个任务需要执行，请根据 task_id 去数据库加载事实。
```

---

## 第 4 层：Day 9 先把队列消息契约讲清楚

今天最值得先定住的，不是队列连接参数到底怎么写，  
而是 worker 将来会消费什么样的消息。

### 分析任务消息至少应该有这些

```text
task_id
dataset_id
task_type
requested_at
trace_id
```

### 投递响应至少应该有这些

```text
task_id
dataset_id
status
queue_name
enqueued
```

### 为什么值得今天先保留 `task_type`

现在可以只有一个：

```text
full_analysis
```

但后面很可能出现：

```text
sentiment_only
topic_only
issue_only
```

Day 9 不需要把这些都实现出来。  
只要先把 `task_type` 放进消息契约，后面扩展时就不用改消息形状。

### 为什么值得今天先保留 `trace_id`

Day 11 会做 Redis 状态追踪，后面还会做日志查看。  
如果从 Day 9 开始每条消息都有 `trace_id`，后面排查问题时就能把：

```text
HTTP 请求
队列消息
worker 日志
任务状态
```

串到同一条链上。

---

## 第 5 层：Day 9 最小 RabbitMQ 投递步骤应该先有哪些

Day 9 最稳的做法，不是一次性做完整调度系统。  
而是先把最小、可验证的投递链路立住。

### 步骤 1：补 RabbitMQ 配置

至少需要：

```text
RABBITMQ_URL
RABBITMQ_QUEUE_NAME
```

建议默认队列名：

```text
sentiflow.analysis.tasks
```

### 步骤 2：补队列消息 schema

至少定义：

- `AnalysisTaskType`
- `AnalysisTaskMessage`
- `EnqueueTaskResponse`

### 步骤 3：补 RabbitMQ publisher

最小 publisher 只做：

- 连接 RabbitMQ
- 声明 durable queue
- 把消息序列化成 JSON
- 使用 persistent delivery mode 投递

### 步骤 4：补 queue service

queue service 负责：

- 根据 `task_id` 和 `dataset_id` 构造消息
- 调用 publisher 投递
- 返回统一投递响应

### 步骤 5：补任务状态更新方法

`crud/task_crud.py` 至少提供：

```text
update_task_status(...)
```

让任务创建后可以进入 `queued`。

### 步骤 6：改造任务创建入口

`POST /tasks` 从：

```text
create task
-> return pending
```

变成：

```text
create task
-> enqueue message
-> update queued
-> return queued
```

### 步骤 7：本地验证消息构建

如果本地暂时没有 RabbitMQ，至少要能用假 publisher 验证：

- 消息字段完整
- `QueueService` 会调用 publisher
- 投递响应结构稳定

真实 RabbitMQ 联调可以作为可选验证。

---

## 第 6 层：结合当前仓库，Day 9 最小落点应该放在哪

基于当前项目实际目录，Day 9 最稳的落点是：

```text
pyproject.toml
conf/settings.py
shcemas/queue_schema.py
services/queue_service.py
crud/task_crud.py
router/tasks.py
test_main.http
```

### `pyproject.toml`

负责：

- 新增 RabbitMQ 客户端依赖
- 建议使用 async 风格客户端，和当前 FastAPI 异步路由保持一致

建议依赖：

```toml
"aio-pika>=9"
```

### `conf/settings.py`

负责：

- 暴露 RabbitMQ URL
- 暴露队列名
- 保持默认值可本地运行

### `shcemas/queue_schema.py`

负责：

- 定义队列消息结构
- 定义投递响应结构
- 不承担连接、投递、重试逻辑

### `services/queue_service.py`

负责：

- 封装 RabbitMQ publisher
- 组装 `AnalysisTaskMessage`
- 对 router 暴露 `enqueue_analysis_task(...)`

### `crud/task_crud.py`

负责：

- 新增 `update_task_status(...)`
- 让任务进入 `queued`

### `router/tasks.py`

负责：

- 创建任务后调用 queue service
- 返回 `queued` 状态
- 不在 router 中写 RabbitMQ 连接细节

### `test_main.http`

负责：

- 保留最小手工验证请求
- 可补一个创建任务后观察返回 `queued` 的请求样例

---

## 第 7 层：Day 9 最小接口建议长什么样

今天最关键的接口仍然是：

- `POST /tasks`
- `GET /tasks/{task_id}`

### `POST /tasks`

它的职责是：

- 校验 dataset 是否存在
- 创建分析任务记录
- 投递 RabbitMQ 消息
- 把任务状态更新为 `queued`
- 返回任务创建和排队结果

它不负责：

- 执行预处理
- 执行情感分析
- 执行主题分析
- 执行问题归因
- 返回最终分析结果

### `GET /tasks/{task_id}`

它的职责是：

- 查询当前任务状态
- 让用户看到任务是否已经进入 `queued`

Day 9 暂时不需要新开一个复杂状态接口。  
Day 11 做 Redis 状态追踪时，再补更细的阶段、进度、错误信息。

---

## 第 8 层：Day 9 不建议做什么

### 不要今天就把 worker 写满

Day 10 会专门处理：

- 消费 RabbitMQ 消息
- 加载 task 和 dataset
- 执行完整分析链
- 写入成功或失败状态

Day 9 只保证消息可以被投递。

### 不要今天就接 Redis 进度

Day 11 会专门处理：

- 阶段状态
- 进度百分比
- 最近错误
- 前端轮询口径

Day 9 只需要 `queued` 这个最小数据库状态。

### 不要把原始文本塞进消息

RabbitMQ 消息只放索引和元信息。  
worker 后续根据 `task_id` 加载数据库事实。

### 不要在 router 里直接写 RabbitMQ 细节

router 层只应该知道：

```text
queue_service.enqueue_analysis_task(...)
```

连接、队列声明、消息序列化都放到 service 层。

### 不要今天就做完整事务消息

最完善的做法可能是 outbox pattern。  
但 Day 9 的目标是先建立异步投递入口，不把任务复杂度扩到事务消息系统。

今天可以先接受一个最小策略：

```text
创建任务记录
投递消息
更新 queued
```

后续如果要增强可靠性，再单独补 outbox 表和补偿扫描。

---

## 上午学习：09:00 - 12:00

## 09:00 - 09:50：把 Day 9 的主问题讲顺

### 今天你要能顺着说出来

```text
Day 8 已经有完整同步分析链
-> 但批量任务不应该阻塞 HTTP 请求
-> Day 9 先让创建任务变成登记和投递
-> RabbitMQ 只接收任务索引消息
-> task 状态进入 queued
-> Day 10 再由 worker 消费消息并执行完整分析链
```

### 你必须能回答这两个问题

1. 为什么 Day 9 的重点是“投递任务”，不是“执行任务”？
2. 为什么 RabbitMQ 消息里只放 `task_id`、`dataset_id` 等索引信息，而不是放完整文本？

---

## 09:50 - 10:40：先画 Day 9 的主链图

### Day 9 RabbitMQ 投递主链

```mermaid
flowchart LR
    A[CreateTaskRequest] --> B[validate dataset]
    B --> C[create task row]
    C --> D[AnalysisTaskMessage]
    D --> E[RabbitMQ queue]
    E --> F[task status queued]
    F --> G[API response]
    E --> H[Day 10 worker]
```

### 这张图要表达什么

系统真正围绕的是：

- 创建任务
- 生成消息
- 投递消息
- 更新状态
- 交给 worker

而不是“在创建任务接口里顺手跑分析”。

---

## 10:40 - 11:30：先整理 Day 9 的消息契约

### `steps/day9_queue_contract.md` 练手骨架版

````markdown
# Day 9 队列消息契约

## 分析任务消息最小结构

- TODO

## 投递响应最小结构

- TODO

## Day 10 会消费什么

- TODO

## 今天不放进消息的内容

- TODO
````

### `steps/day9_queue_contract.md` 参考答案

````markdown
# Day 9 队列消息契约

## 分析任务消息最小结构

- `task_id`
- `dataset_id`
- `task_type`
- `requested_at`
- `trace_id`

## 投递响应最小结构

- `task_id`
- `dataset_id`
- `status`
- `queue_name`
- `enqueued`

## Day 10 会消费什么

- 一个稳定的 `AnalysisTaskMessage`
- 根据 `task_id` 加载任务详情
- 根据 `dataset_id` 加载数据集
- 执行 Day 5 到 Day 8 的完整分析链

## 今天不放进消息的内容

- 原始上传文件
- 全部评论正文
- 情感分析结果
- 主题分析结果
- 问题归因结果
````

### 这一段你一定要看懂

Day 9 真正要统一的不是 RabbitMQ 的某个参数，  
而是后续 worker 能不能稳定理解“这条消息代表什么任务”。

---

## 11:30 - 12:00：先决定今天怎么验收

### Day 9 最直接的验收方式

今天至少要能回答：

1. 创建任务后返回的状态为什么应该是 `queued`？
2. 队列消息最小字段有哪些？
3. RabbitMQ publisher 放在哪一层？
4. 本地没有 worker 时怎样确认投递入口没有写偏？
5. Day 10 worker 能拿什么作为输入继续执行？

---

## 下午编码：14:00 - 18:00

## 14:00 - 14:30：先补 RabbitMQ 依赖和配置

当前 `pyproject.toml` 里已经有 `redis`，但还没有 RabbitMQ 客户端。  
Day 9 建议新增一个 async 客户端依赖：

```toml
"aio-pika>=9"
```

### `conf/settings.py` 建议新增字段

```python
RABBITMQ_URL: str = "amqp://guest:guest@127.0.0.1:5672/"
RABBITMQ_QUEUE_NAME: str = "sentiflow.analysis.tasks"
```

### 为什么配置先保持简单

Day 9 先使用默认 exchange + queue name 作为 routing key。  
这样最容易验证，也能减少 exchange、binding、routing key 同时引入带来的理解成本。

后面如果需要拆分不同队列，再引入：

```text
exchange
routing_key
dead letter queue
retry queue
```

---

## 14:30 - 15:10：先补 `shcemas/queue_schema.py`

建议先补：

- `AnalysisTaskType`
- `AnalysisTaskMessage`
- `EnqueueTaskResponse`

### `shcemas/queue_schema.py` 练手骨架版

```python
from enum import Enum

from pydantic import BaseModel


class AnalysisTaskType(str, Enum):
    # 你要做的事：
    # 1. 先定义 full_analysis
    # 2. 不要今天就扩展一堆任务类型
    # 3. 保留未来拆分 sentiment_only、topic_only 的入口
    raise NotImplementedError


class AnalysisTaskMessage(BaseModel):
    # 你要做的事：
    # 1. 定义 task_id
    # 2. 定义 dataset_id
    # 3. 定义 task_type
    # 4. 定义 requested_at
    # 5. 定义 trace_id
    raise NotImplementedError


class EnqueueTaskResponse(BaseModel):
    # 你要做的事：
    # 1. 返回 task_id 和 dataset_id
    # 2. 返回 queued 状态
    # 3. 返回 queue_name
    # 4. 返回是否已投递
    raise NotImplementedError
```

### `shcemas/queue_schema.py` 参考答案

```python
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from shcemas.task_schema import TaskStatus


class AnalysisTaskType(str, Enum):
    full_analysis = "full_analysis"


class AnalysisTaskMessage(BaseModel):
    task_id: str
    dataset_id: str
    task_type: AnalysisTaskType = AnalysisTaskType.full_analysis
    requested_at: datetime
    trace_id: str


class EnqueueTaskResponse(BaseModel):
    task_id: str
    dataset_id: str
    status: TaskStatus
    queue_name: str
    enqueued: bool
```

### 这里要先理解的点

1. `AnalysisTaskMessage` 是 worker 将来消费的稳定输入  
2. `EnqueueTaskResponse` 是 API 层可以返回给用户的最小排队结果  
3. `task_type` 今天只有一个值也值得保留，因为它代表任务语义  
4. 消息 schema 不应该引入 RabbitMQ 客户端对象  

---

## 15:10 - 16:10：在 `services/queue_service.py` 里立住投递主链

建议新增：

- `RabbitMQPublisher`
- `QueueService`
- `queue_service`

### `services/queue_service.py` 练手骨架版

```python
from shcemas.queue_schema import AnalysisTaskMessage, EnqueueTaskResponse


class RabbitMQPublisher:
    def __init__(self, url: str, queue_name: str) -> None:
        # 你要做的事：
        # 1. 保存 RabbitMQ URL
        # 2. 保存队列名
        # 3. 不要在初始化里立刻建立网络连接
        raise NotImplementedError

    async def publish(self, message: AnalysisTaskMessage) -> None:
        # 你要做的事：
        # 1. 建立 RabbitMQ 连接
        # 2. 声明 durable queue
        # 3. 把 message 序列化为 JSON bytes
        # 4. 使用 persistent delivery mode 投递
        # 5. 关闭连接或交给连接上下文管理
        raise NotImplementedError

    def _message_body(self, message: AnalysisTaskMessage) -> bytes:
        # 你要做的事：
        # 1. 使用 Pydantic JSON 序列化
        # 2. 编码成 UTF-8 bytes
        # 3. 不要手写字符串拼接 JSON
        raise NotImplementedError


class QueueService:
    def __init__(self, publisher: RabbitMQPublisher | None = None) -> None:
        # 你要做的事：
        # 1. 支持注入 publisher，方便本地测试
        # 2. 没有注入时根据 settings 创建 RabbitMQPublisher
        # 3. 不要在这里执行分析逻辑
        raise NotImplementedError

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
        raise NotImplementedError
```

### `services/queue_service.py` 参考答案

```python
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
        self.url = url
        self.queue_name = queue_name

    async def publish(self, message: AnalysisTaskMessage) -> None:
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(self.queue_name, durable=True)
            await channel.default_exchange.publish(
                Message(
                    body=self._message_body(message),
                    delivery_mode=DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=self.queue_name,
            )

    def _message_body(self, message: AnalysisTaskMessage) -> bytes:
        return message.model_dump_json().encode("utf-8")


class QueueService:
    def __init__(self, publisher: RabbitMQPublisher | None = None) -> None:
        self.publisher = publisher or RabbitMQPublisher(
            url=settings.RABBITMQ_URL,
            queue_name=settings.RABBITMQ_QUEUE_NAME,
        )

    async def enqueue_analysis_task(
        self,
        task_id: str,
        dataset_id: str,
    ) -> EnqueueTaskResponse:
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
```

### 这里要先理解的点

1. `RabbitMQPublisher` 只管 RabbitMQ 细节  
2. `QueueService` 只管业务消息构建和投递响应  
3. 连接不放在 `__init__` 里，避免应用启动时立刻依赖 broker 可用  
4. 支持注入 publisher，方便不用真实 RabbitMQ 也能测试消息构建  
5. Day 9 不在这里消费消息，也不执行分析链  

---

## 16:10 - 16:45：给 `crud/task_crud.py` 补最小状态更新

当前 `TaskStatus` 已经有 `queued`，但 `crud/task_crud.py` 还需要最小状态更新方法。

### `crud/task_crud.py` 练手骨架版

```python
from sqlalchemy.ext.asyncio import AsyncSession

from models.task_model import Task
from shcemas.task_schema import TaskStatus


async def update_task_status(
    session: AsyncSession,
    task_id: str,
    status: TaskStatus,
) -> Task | None:
    # 你要做的事：
    # 1. 根据 task_id 查询任务
    # 2. 任务不存在时返回 None
    # 3. 更新 task.status
    # 4. flush 并 refresh
    # 5. 不要在这里 commit，commit 留给调用方
    raise NotImplementedError
```

### `crud/task_crud.py` 参考答案

```python
async def update_task_status(
    session: AsyncSession,
    task_id: str,
    status: TaskStatus,
) -> Task | None:
    task = await get_task_detail(session=session, task_id=task_id)
    if task is None:
        return None

    task.status = status.value
    await session.flush()
    await session.refresh(task)
    return task
```

### 为什么 commit 不放在 CRUD 里

当前仓库的路由层已经在创建数据集和任务后显式 `commit`。  
Day 9 继续沿用这个风格，避免有些 CRUD 自动提交、有些不提交，导致事务边界越来越乱。

---

## 16:45 - 17:35：改造 `router/tasks.py` 的任务创建入口

Day 9 最关键的业务变化在这里：

```text
创建任务不再只是 pending
创建任务后要投递队列消息
成功投递后任务进入 queued
```

### `router/tasks.py` 练手骨架版

```python
@router.post("")
async def create_task_endpoint(payload: CreateTaskRequest, db=Depends(get_db)):
    # 你要做的事：
    # 1. 查询 dataset，不存在就返回统一错误
    # 2. 构建任务创建载荷
    # 3. 写入任务记录
    # 4. 提交任务记录，确保 worker 后续能查到
    # 5. 调用 queue_service.enqueue_analysis_task
    # 6. 更新任务状态为 queued
    # 7. 再次提交状态变更
    # 8. 返回 queued 响应
    raise NotImplementedError
```

### `router/tasks.py` 参考答案

```python
from crud.task_crud import create_task, get_task_detail, update_task_status
from services.queue_service import queue_service


@router.post("")
async def create_task_endpoint(payload: CreateTaskRequest, db=Depends(get_db)):
    dataset = await get_dataset_by_id(session=db, dataset_id=payload.dataset_id)
    if dataset is None:
        return error_response(message="dataset not found", code=1, data=None)

    task_payload, response_data = task_service.build_task_create_payload(
        dataset=dataset,
        payload=payload,
    )
    await create_task(session=db, payload=task_payload)
    await db.commit()

    enqueue_response = await queue_service.enqueue_analysis_task(
        task_id=response_data.task_id,
        dataset_id=response_data.dataset_id,
    )
    await update_task_status(
        session=db,
        task_id=response_data.task_id,
        status=TaskStatus.queued,
    )
    await db.commit()

    response_data.status = TaskStatus.queued
    return success_response(
        data={
            "task": response_data.model_dump(),
            "queue": enqueue_response.model_dump(),
        },
        message="task queued",
    )
```

### 这里要先理解的点

1. 第一段 `commit` 是为了让任务记录先成为数据库事实  
2. 投递成功后再更新为 `queued`，语义更清楚  
3. 如果投递失败，接口应该抛出错误，任务仍然可以保留为 `pending` 供后续补偿  
4. 今天不做 outbox，避免把 Day 9 变成事务消息系统  
5. 返回结构里可以同时包含 `task` 和 `queue`，便于前端和调试确认任务已排队  

---

## 17:35 - 18:00：整理本地验证方式

Day 9 会接外部 RabbitMQ，但本地验证不要只依赖 broker。

### 没有 RabbitMQ 时，至少验证这些

可以写一个假 publisher：

```python
class FakePublisher:
    def __init__(self) -> None:
        self.messages = []

    async def publish(self, message):
        self.messages.append(message)
```

然后验证：

```text
QueueService(fake).enqueue_analysis_task(...)
-> fake.messages 里有一条 AnalysisTaskMessage
-> response.status == queued
-> response.enqueued == True
```

### 有 RabbitMQ 时，手工验证这些

1. 启动本地 RabbitMQ
2. 配置 `.env` 中的 `RABBITMQ_URL`
3. 调用 `POST /tasks`
4. 确认响应里 task 状态是 `queued`
5. 确认 RabbitMQ 队列里有一条消息
6. 调用 `GET /tasks/{task_id}`，确认数据库状态是 `queued`

### 今天不要求验证这些

```text
worker 消费成功
完整分析链后台跑完
Redis 进度实时变化
结果持久化可查询
```

这些是 Day 10、Day 11、Day 12 的重点。

---

## 晚上复盘：20:00 - 21:00

### 今晚你必须自己讲顺的 8 个点

1. Day 9 的本质为什么是“任务投递”，不是“任务执行”？  
2. 为什么异步化应该从 `POST /tasks` 开始，而不是从某个分析接口开始？  
3. 为什么 RabbitMQ 消息里只放任务索引，不放原始文本？  
4. 为什么 `queue_service.py` 不应该承担预处理、情感、主题、归因逻辑？  
5. 为什么 Day 9 只需要 `queued`，不急着引入 Redis 进度？  
6. 为什么本地测试需要 fake publisher？  
7. 为什么今天不做 outbox 和复杂重试？  
8. Day 10 worker 能从 Day 9 拿到什么稳定输入？  

---

## 今日验收标准

- `steps/day9.md` 对 Day 9 的目标、边界和文件落点讲清楚
- Day 9 的 RabbitMQ 消息契约讲清楚
- `AnalysisTaskMessage` 和 `EnqueueTaskResponse` 的最小结构讲清楚
- `services/queue_service.py` 的 publisher 和 service 边界讲清楚
- `crud/task_crud.py` 的任务状态更新职责讲清楚
- `router/tasks.py` 的创建任务后投递入口讲清楚
- 本地无 RabbitMQ 时的 fake publisher 验证方式讲清楚
- Day 10 worker 消费入口的输入已经准备好

---

## 今天最容易踩的坑

### 坑 1：把 Day 9 和 Day 10 混在一起

问题：

- producer、consumer、分析执行、结果回写一起写
- 一旦出错，不知道是投递失败还是执行失败

规避建议：

- Day 9 只做 producer 和 queued 状态
- Day 10 再写 worker consumer

### 坑 2：消息里塞完整评论文本

问题：

- 队列承担大数据存储压力
- 消息和数据库事实容易不一致
- worker 后续扩展困难

规避建议：

- 消息只放 `task_id`、`dataset_id`、`task_type`、`requested_at`、`trace_id`
- worker 根据索引加载数据

### 坑 3：RabbitMQ 连接逻辑写在 router 里

问题：

- router 变成基础设施层
- 后续 worker 或测试很难复用投递逻辑

规避建议：

- router 只调用 `queue_service.enqueue_analysis_task(...)`
- RabbitMQ 细节放在 `services/queue_service.py`

### 坑 4：没有本地验证退路

问题：

- 没有 RabbitMQ 时完全无法验证代码
- 队列消息结构问题拖到联调时才暴露

规避建议：

- `QueueService` 支持注入 fake publisher
- 至少验证消息构建和响应结构

### 坑 5：今天就做复杂可靠性系统

问题：

- outbox、死信队列、重试策略、补偿扫描同时出现
- Day 9 的主线失焦

规避建议：

- 先做最小 RabbitMQ 投递
- 后续根据真实失败场景再补可靠性机制

### 坑 6：状态语义不清

问题：

- `pending`、`queued`、`running` 混着用
- 用户不知道任务到底有没有进入队列

规避建议：

- 创建前是请求
- 创建后未投递是 `pending`
- 投递成功是 `queued`
- worker 开始执行才是 `running`
- worker 执行完才是 `success` 或 `failed`

---

## 给明天的交接提示

明天开始，SentiFlow 就不只是“任务能进入队列”，  
而是要真正回答另一个工程问题：

```text
队列里的任务由谁消费，消费以后怎样执行完整分析链
```

也就是说，后面会继续走向：

```text
RabbitMQ message
-> worker consumes message
-> load task and dataset
-> run preprocess
-> run sentiment
-> run topics
-> run issue attribution
-> update running / success / failed
```

所以 Day 9 最关键的交接只有一句话：

```text
先让创建任务稳定生成 AnalysisTaskMessage 并进入 RabbitMQ，Day 10 的 worker 才是在消费一条清楚的任务消息，而不是继续猜 API 层到底传来了什么。
```

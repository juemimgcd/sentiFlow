# Day 4：建立数据导入与任务创建入口

## 今天的总目标

- 把 Day 3 已经立住的 FastAPI 骨架，真正接上一条可用的“文件接入 -> dataset -> 创建任务”主链路
- 采用“CSV / JSON 原生解析 + 其它格式交给 MarkItDown 尝试解析”的导入方案，而不是把上传能力写死成固定白名单
- 让来源平台、时间范围、产品线这些元信息有明确落点
- 明确“导入一批文本”和“创建一个分析任务”不是同一个动作
- 为 Day 5 的文本预处理与标准化准备稳定输入

## 今天结束前，你必须拿到什么

- 一个真正可调用的 `/tasks/import` 入口
- 一个真正可调用的 `/tasks` 任务创建入口
- 一套 Day 4 最小导入 schema
- 一套 Day 4 最小任务 schema
- 一份能讲清楚“为什么导入和任务创建要分开”的判断标准
- 一份可以直接交给 Day 5 继续做预处理的标准化输入

---

## Day 4 一图总览

一句话总结：

> Day 4 不是把分析做深，而是把“文件输入”稳定变成“dataset + task”这两个系统对象。

主链路先压缩成这一条：

```text
source file
-> import endpoint
-> content extraction
-> dataset
-> create task endpoint
-> analysis_task
-> Day 5 预处理
```

今天最不能混淆的 4 件事：

- `import` 负责把外部文件变成系统内部可消费输入
- `content extraction` 负责把不同文件格式统一成最小内部载体
- 上传入口不再做固定格式白名单，解析失败时再给出明确错误
- `task` 负责把内部输入变成可追踪执行对象
- Day 4 的终点是“可进入预处理”，不是“分析结果产出”

---

## 为什么这一天重要

很多人会误以为 Day 4 只是：

- 多写了一个上传接口
- 多写了一个创建任务接口
- 把 Day 3 的占位代码补成了真实代码

这都不够准确。

Day 4 真正重要的地方在于：

> 从今天开始，SentiFlow 才第一次把“外部世界的一批原始文本”正式接进系统内部主链。

没有这一步，后面的：

- 预处理
- 分析
- 状态追踪
- 结果查询
- 导出报表

都只是空转概念。

所以 Day 4 不是“接口数量增加了一天”，  
而是系统第一次获得稳定输入入口的一天。

---

## Day 4 整体架构

```mermaid
flowchart LR
    A[源文件] --> B[POST /tasks/import]
    B --> C[router/tasks.py]
    C --> D[content extraction]
    D --> E[normalized payload]
    E --> F[dataset_id + 样本预览 + 元信息]
    F --> G[POST /tasks]
    G --> H[analysis_task]
    H --> I[GET /tasks/{task_id}]
    H --> J[Day 5 文本预处理]
```

再压缩成仓库里真正的文件落点：

```text
main.py
-> router/tasks.py
-> shcemas/task_schema.py
-> services/task_service.py
-> content extraction adapter
-> models + crud 持久落点
-> Day 5 再接预处理逻辑
```

---

## 今天的边界要讲透

Day 4 解决的是：

```text
输入怎样进入系统
不同文件怎样先被统一抽取
输入怎样挂到任务上
任务怎样成为后续处理入口
```

Day 4 不解决的是：

```text
情感分析怎样算
主题归类怎样做
异步执行怎样调度
报表怎样导出
```

### 今天之后，各层职责应该怎么理解

| 位置 | Day 4 负责什么 | Day 4 不负责什么 |
| --- | --- | --- |
| `main.py` | 注册应用与路由入口 | 业务解析 |
| `router/tasks.py` | 收参数、收文件、调 service、统一返回 | 写文件解析细节 |
| `shcemas/task_schema.py` | 定义导入和任务边界模型 | 持有业务流程 |
| `models/` | 定义 `dataset` / `task` 持久结构 | 业务编排 |
| `crud/` | 承担查表、建表式数据读写 | HTTP 和业务聚合 |
| `services/task_service.py` | 内容抽取编排、调用 crud、组装任务详情 | HTTP 协议处理 |
| `MarkItDown adapter` | 负责 PDF / Office / HTML 等文件转 Markdown / 文本 | 任务状态流转 |
| `pipelines/` | 今天先不启用 | 今天不承接 Day 4 主线 |

### 对当前仓库的处理原则

Day 4 对现有目录先做三类判断：

| 分类 | 目录 / 文件 | 处理方式 |
| --- | --- | --- |
| 直接复用 | `main.py` `router/tasks.py` `utils/response.py` | 直接接上 Day 4 主线 |
| 小改接入 | `shcemas/` `services/` `crud/` `models/` | 新增 Day 4 专属 schema / service / crud / model 文件 |
| 暂时不动 | `pipelines/` `agent/` | 先保留，不在 Day 4 扩写 |

这个判断很重要。  
它能防止 Day 4 一上来就把整个仓库改成“看起来更完整”，但主链反而没先跑通。

---

## 今天开始，先不要急着写情感分析和主题识别

Day 4 最容易犯的错误就是：

- 一看到文本导入，就马上顺手把清洗、去噪、情感分析全塞进一个接口
- 一看到任务创建，就马上把异步队列、回调通知、报表导出一起接上
- 一看到当前仓库里已经有 `crud/`、`models/`、`pipelines/`，就马上开始做全套持久化和完整分层
- 一看到 `router/tasks.py` 里有占位接口，就直接把所有逻辑堆到 router

这些都不是 Day 4 的重点。

今天真正要解决的是：

> 用户交给系统的一批评论或舆情文本，怎样才能先变成一个可追踪的分析任务？

如果这个问题没讲清楚，  
后面会出现两个典型坏结果：

- 导入接口越来越重，最后既负责解析文件，又负责分析，还负责状态流转
- 任务对象越来越空，最后只能靠临时字段把结果、进度和元信息硬拼起来

所以 Day 4 的关键词不是“分析做深”，而是：

```text
导入
校验
抽取
adapter 分流
元信息
任务载体
动作分离
```

---

## 第 1 层：Day 4 的本质是什么

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
第一条真正可提交的业务入口
```

也就是说，Day 4 不是开始“做完整分析系统”，  
而是开始回答一个非常具体的问题：

```text
一批原始文本
-> 怎样进入系统
-> 怎样挂到一个任务上
-> 怎样让后面可以继续预处理和分析
```

这一步一旦走通，  
SentiFlow 就不再只是“有几个接口壳子”，  
而是有了第一条真正开始承接业务输入的主链。

---

## 第 2 层：Day 4 的主链路一定要分成两段

今天你要先把 Day 4 的主链牢牢记成这样：

```text
上传 source file
-> 校验格式
-> 抽取内容与元信息
-> 归一化成 dataset 输入
-> 创建 analysis_task
-> 返回 task_id
```

这里最重要的不是步骤名字，  
而是你要看清楚其中有两个动作：

### 动作 1：导入

导入解决的是：

- 文件能不能读
- 这个格式应该走原生解析还是 MarkItDown
- 内容能不能被可靠抽出来
- 样本能不能归一化出来
- 字段够不够用
- 元信息有没有地方存

### 动作 2：创建任务

任务创建解决的是：

- 这批输入由哪个 `task_id` 接住
- 当前状态是什么
- 后续预处理和分析从哪里接手
- 页面以后按什么对象查状态和结果

所以 Day 4 最关键的判断只有一句话：

> 导入是把“文件或原始数据”变成“系统能理解的统一输入”，任务创建是把“系统能理解的统一输入”变成“可追踪执行对象”。

这两个动作相关，  
但不能混成一个黑盒接口。

---

## 第 3 层：为什么 Day 4 一定要把导入和任务创建拆开

很多人会本能地写成这样：

```text
上传文件
-> 立刻创建任务
-> 立刻开始分析
-> 一次接口干完全部事情
```

这在演示里看起来很顺，  
但对后面的系统演进很不友好。

### 问题 1：你很难知道失败到底失败在哪一层

如果一个接口同时负责：

- 收文件
- 解析文件
- 写元信息
- 创任务
- 启动分析

那么一旦失败，  
你根本分不清是：

- 文件格式不对
- 样本字段不对
- 元信息缺失
- 任务没建成功
- 后续分析没启动

### 问题 2：Day 5 的预处理没有稳定接力点

Day 5 会进入：

```text
清洗
标准化
去空
去噪
样本有效性判断
```

如果 Day 4 没先把“导入后得到的标准化输入”单独立住，  
Day 5 就只能反复回头拆 Day 4 接口。

### 问题 3：页面和接口都不好长

后面页面会关心：

- 这次导入了多少条
- 有多少条有效样本
- 哪个文件导入失败了
- 哪个任务正在处理

如果导入与任务完全糊在一起，  
这些信息后面会越来越难查。

所以 Day 4 的核心边界要反复记：

```text
导入负责把输入收进来
任务负责把输入挂成可追踪执行对象
```

---

## 第 4 层：Day 4 先把导入输入边界和抽取边界讲清楚

今天要先区分两层概念：

### 外部输入层

长期看，外部文件类型可能会越来越多。  
现在既然已经接了 MarkItDown，Day 4 就不应该再把上传入口卡死在固定白名单上，而应该理解成：

```text
允许上传
= CSV / JSON 走原生解析
= 其它格式交给 MarkItDown 尝试抽取
= 解析失败时返回清晰错误
= 大小和安全检查通过
```

### Day 4 当前落地层

Day 4 可以把支持口径升级成：

```text
CSV / JSON
-> native adapter

其它上传文件
-> MarkItDown adapter
```

不要今天就扩成：

- Excel 多 sheet
- ZIP 批量包
- 自动抓取平台数据
- 流式实时接入

Day 4 只做最小可靠输入。

### 为什么这里值得先重构一下

如果你把 Day 4 的主链永久写死成：

```text
CSV / JSON
-> dataset
-> task
```

那后面一旦接 PDF / Word / HTML，  
你就得回头重写 Day 4 的核心表述。

更稳的写法应该是：

```text
source file
-> extraction adapter
-> normalized payload
-> dataset
-> task
```

这样：

- CSV / JSON 可以继续走原生 adapter
- 其它格式可以交给 MarkItDown adapter 尝试解析
- 后面新增更专门的格式处理时，只是增加 adapter，不是推翻 Day 4

### Day 4 的格式策略应该怎么说

更合理的说法不是：

```text
系统保证任何文件都能解析成功
```

而是：

```text
用户可以上传文件，系统优先用原生 CSV / JSON 解析，否则交给 MarkItDown 尝试抽取文本
```

### 为什么仍然要保留限制

因为即使用了 MarkItDown，系统仍然要控制：

- 文件大小是否超限
- 转换失败时返回什么错误
- 当前环境是否安装了 MarkItDown 所需依赖
- 文件大小是否超限
- 是否允许 ZIP / 嵌套包这类高风险输入
- 是否允许 ZIP、嵌套包、远程内容等高风险输入

### 每条样本至少需要什么

Day 4 最稳的标准是：

- 文本内容 `content`
- 来源平台 `source_platform`
- 时间信息 `published_at` 可选
- 额外元信息 `extra` 可选

### 文件级元信息至少需要什么

除了样本文本本身，  
这次导入还需要一个最小元信息层：

- `source_platform`
- `product_line`
- `date_start`
- `date_end`
- `file_name`
- `file_type`
- `extraction_mode`

### Day 4 不要在输入上追求“万能”

今天不需要把所有平台字段差异一次处理完。  
更稳的做法是先统一成内部最小结构：

```text
content
source_platform
published_at
extra
```

只要 Day 4 能把当前 adapter 输出统一成这套最小结构，  
后面 Day 5 的标准化就有明确对象可接。

---

## 第 5 层：Day 4 先把任务对象讲清楚

Day 4 创建的任务还不需要很复杂。  
今天只需要先让它成为系统中真正的中心载体。

### 最小任务信息建议先有这些

- `task_id`
- `dataset_id`
- `task_name`
- `status`
- `sample_count`
- `source_platform`
- `product_line`
- `created_at`

### 状态先沿用 Day 2 的最小集合

当前先沿用：

- `pending`
- `queued`
- `running`
- `success`
- `failed`
- `canceled`

但 Day 4 先真正落地的常用状态只需要优先用到：

- `pending`
- `queued`

原因很简单：

- Day 4 的重点是把任务建出来
- 不是今天就把完整执行状态机跑满

### Day 4 的任务真正表达的是什么

它表达的不是：

> 我们已经把分析做完了。

而是：

> 系统已经承认：这批输入属于一次可追踪的分析执行。

这是 Day 4 真正重要的地方。

---

## 第 6 层：结合当前仓库，Day 4 最小落点应该放在哪

基于当前项目实际目录，  
Day 4 最稳的做法不是引入更多层，  
而是在已经存在的骨架上接通最小业务入口：

```text
main.py
router/tasks.py
shcemas/task_schema.py
services/task_service.py
utils/response.py
```

如果你要顺手做这次“轻重构”，  
那今天最值得补齐的是“抽取边界 + model/crud 边界”：

```text
router/tasks.py
-> services/task_service.py
-> _extract_rows(...)
-> crud/dataset_crud.py
-> crud/task_crud.py
-> models/dataset_model.py
-> models/task_model.py
```

这一步的意义是：

- 先把“当前 CSV / JSON adapter”抽出来
- 先把“查表 / 写表”从 service 层移走
- 让 `get_task_detail` 这类读操作回到 `crud/`

### `main.py`

负责：

- 确保 `health` 和 `tasks` 路由真正注册

### `router/tasks.py`

负责：

- 接收上传文件
- 接收任务创建请求
- 调用 `services/task_service.py`
- 返回统一响应结构

### `shcemas/task_schema.py`

负责：

- 导入元信息模型
- 导入结果模型
- 任务创建请求模型
- 任务详情结果模型

### `services/task_service.py`

负责：

- 校验文件格式
- 按 adapter 抽取内容
- 提取样本与元信息
- 调用 `crud/` 写入 `dataset` 和 `task`
- 组装 `TaskDetailResponse`
- 返回 Day 4 的最小结果

### `crud/`

负责：

- `create_dataset`
- `get_dataset_by_id`
- `create_task`
- `get_task_detail`

### `models/`

负责：

- 定义 `dataset` 持久字段
- 定义 `task` 持久字段
- 为后续 ORM 接入提供稳定结构

---

## 第 7 层：Day 4 最小接口建议长什么样

今天最关键的接口就是这三个：

- `POST /tasks/import`
- `POST /tasks`
- `GET /tasks/{task_id}`

### `POST /tasks/import`

它的职责是：

- 收文件
- 校验文件类型
- 调用当前 adapter 做内容抽取
- 抽取样本
- 提取元信息
- 返回一个 `dataset_id`

它不负责：

- 启动分析
- 执行预处理
- 生成最终结果

### `POST /tasks`

它的职责是：

- 接收 `dataset_id`
- 创建一个新的 `analysis_task`
- 给出最小初始状态
- 返回 `task_id`

它不负责：

- 再去重新读文件
- 再做一遍格式解析
- 顺手把后续分析全部做完

### `GET /tasks/{task_id}`

它的职责是：

- 返回任务当前最小信息
- 证明任务对象已经稳定存在

Day 4 到这里就足够。

---

## 第 8 层：Day 4 不建议做什么

### 不要把“放开格式限制”理解成“任何文件都保证成功”

用了 MarkItDown 也不代表任何文件都一定能被抽取。  
Day 4 仍然应该坚持：

- 文件大小限制
- 依赖可用性检查
- 转换失败时的明确错误
- 高风险输入类型的单独策略

今天做的是“放开前置白名单，让 MarkItDown 尝试抽取”，不是“承诺所有文件都能成功”。

### 不要今天就把文本预处理做满

Day 5 会专门处理：

- 去空
- 去噪
- 清洗
- 标准化

Day 4 先只做最小可读解析。

### 不要今天就接完整数据库模型

当前仓库虽然已经有：

- `conf/db_conf.py`
- `crud/`
- `models/`

但 Day 4 的重点不是 ORM 设计，  
而是把输入边界和任务载体先跑顺。

如果今天就陷进表设计，  
很容易又回到 Day 2 提醒过的坑里。

### 不要今天就把队列和异步执行接满

Day 4 只需要任务创建口径稳定。  
真正运行、调度、状态推进，后面再逐步接。

### 不要顺手改目录命名

比如当前仓库里是：

```text
shcemas/
```

今天不要为了“名字不完美”顺手做重命名。  
Day 4 的重点是接主链，不是改目录历史。

---

## 可选增强：MarkItDown 放在哪里更合适

如果 Day 4 就决定把上传入口从“两个格式”升级成“尽量交给 MarkItDown 抽取”，  
那么可以直接把 Microsoft 的 `MarkItDown` 纳入导入设计里，作为非 CSV / JSON 文件的通用抽取 adapter。

但它在这个项目里更适合放在：

```text
外部文件
-> 文档转 Markdown / 文本
-> 再进入 SentiFlow 的导入与预处理链
```

而不是放成：

```text
把当前仓库所有文件统一转成 md
```

### Day 4 应该怎么接它

最稳的接法不是“把所有格式都丢给同一个黑盒”，  
而是这样分工：

- CSV / JSON：继续走原生 parser
- 其它格式：走 MarkItDown adapter 尝试解析
- 统一输出：`normalized payload`

也就是说，Day 4 现在可以升级成：

```text
上传文件
-> native adapter / markitdown adapter
-> normalized payload
-> dataset
-> task
```

### 如果后面接，建议放在哪

更合适的放法是：

- `services/file_ingest_service.py` 负责文件接入编排
- `clients/markitdown_client.py` 或 `utils/file_loader.py` 负责调用转换工具
- 转换后的 Markdown / 文本再进入 Day 5 的标准化流程

### Day 4 接入它时仍然要保留哪些限制

- 依赖可用性检查
- 单文件大小限制
- 转换失败时的明确错误响应
- 是否允许 ZIP / 嵌套包的单独策略

也就是说：

> MarkItDown 可以进入 Day 4 设计，但必须作为“原生 adapter + MarkItDown adapter 分流”方案的一部分，而不是“任何文件都保证成功”的承诺。

---

## 如果决定在 Day 4 真实接入 MarkItDown，实施步骤应该怎么排

如果这一天不只是写计划，  
而是准备把代码也按这个方案落下去，  
那更稳的推进顺序应该是下面这 6 步。

### 步骤 1：先定 adapter 分流规则

先在配置或 service 层明确：

```text
NATIVE_IMPORT_TYPES
= .csv .json

其他后缀
= MarkItDown adapter
```

这一步先解决的是：

- 哪些格式走原生结构化解析
- 哪些格式走 MarkItDown 文本抽取
- MarkItDown 失败时怎样返回清晰错误

### 步骤 2：先安装并验证 MarkItDown 依赖

这里不要只写“理论上支持”。  
要先在项目环境里验证：

- `markitdown` 主包是否安装成功
- PDF / DOCX / PPTX / XLSX 相关依赖是否可用
- 当前系统环境是否缺少外部组件

这一步的意义是：

- 防止计划里写得很宽，运行时却根本转不出来

### 步骤 3：先补 `models/` 和 `crud/`

先定义：

- `models/dataset_model.py`
- `models/task_model.py`
- `crud/dataset_crud.py`
- `crud/task_crud.py`

这里的原则要讲清楚：

- `model` 负责持久结构
- `crud` 负责查表和写表
- `service` 不直接吞掉数据访问细节

### 步骤 4：在 `services/task_service.py` 里形成 adapter 分流和业务编排

这一步建议明确改成：

```text
csv/json
-> native adapter

pdf/docx/pptx/xlsx/html
-> markitdown adapter
```

也就是说，真实代码里至少要出现这层分发：

- `_extract_rows(...)`
- `_parse_csv(...)`
- `_parse_json(...)`
- `_parse_with_markitdown(...)`

同时 service 里要只保留：

- 调用 crud
- 业务校验
- schema 组装

### 步骤 5：把导入响应补成可追踪结构

`/tasks/import` 不应该只返回 `dataset_id`。  
建议至少带上：

- `dataset_id`
- `file_type`
- `extraction_mode`
- `sample_count`
- `preview_texts`

这样后面你才能判断：

- 这次走的是原生 parser 还是 MarkItDown
- 转换结果是否合理

### 步骤 6：补导入失败口径

如果接了 MarkItDown，  
错误类型至少要分清这几类：

- 当前环境缺依赖
- 文件可读但抽取失败
- 抽取成功但没有有效内容
- 文件大小超限

也就是说，Day 4 真正落地时，  
最好不要继续只返回一个笼统的 `"error"`。

### 步骤 7：把 Day 5 的输入契约固定住

最后要确认一件事：

> 不管前面是 CSV adapter、JSON adapter 还是 MarkItDown adapter，交给 Day 5 的都必须是同一种 `normalized payload`。

最小统一结构仍然建议保持：

```text
content
source_platform
published_at
extra
```

这样 Day 5 才不用关心“这个样本原来来自 PDF 还是 CSV”。

### 这一组实施步骤最终会落到哪些文件

如果按当前仓库结构来做，  
Day 4 的真实落点应该是：

- `main.py`
- `router/tasks.py`
- `shcemas/task_schema.py`
- `models/dataset_model.py`
- `models/task_model.py`
- `crud/dataset_crud.py`
- `crud/task_crud.py`
- `services/task_service.py`
- `pyproject.toml`

---

## 上午学习：09:00 - 12:00

## 09:00 - 09:50：先把 Day 4 的主问题讲顺

先把今天的主问题讲成一句话：

```text
Day 3 立的是骨架
-> Day 4 要让第一批真实文本能进入系统
-> 进入系统以后不能只是散数据
-> 必须先变成 dataset 输入
-> 再变成 task
-> 这样 Day 5 才有稳定对象继续做预处理
```

### 你必须能回答这两个问题

1. 为什么 Day 4 的重点不是“分析”，而是“输入如何变成任务”？
2. 为什么 `/tasks/import` 和 `/tasks` 不能完全揉成一个动作？
3. 为什么用了 MarkItDown 之后仍然要保留大小限制、依赖检查和转换失败口径？

---

## 09:50 - 10:40：先画 Day 4 的最小输入链

今天先把输入链画成这样：

```text
source file
-> 抽取文本
-> 归一化 payload
-> create_dataset
-> create_task
-> get_task_by_id
-> 返回 task detail
```

### 这里最重要的不是“图漂亮”

而是你要讲清楚 3 个边界：

1. 文件级输入和任务级输入不是一回事
2. `dataset_id` 是 Day 4 很值得先立住的中间对象
3. `get_task_detail` 这种读操作应该下沉到 `crud/`
4. Day 5 会接的是 dataset 中的标准化样本，而不是原始上传动作本身

---

## 10:40 - 11:30：整理 Day 4 的 schema 边界

今天建议先定这几个最小 schema：

- `ImportMetadata`
- `ImportDatasetResponse`
- `CreateTaskRequest`
- `CreateTaskResponse`
- `TaskDetailResponse`

如果 Day 4 按 adapter 分流来做，  
还建议在导入输出里明确两类字段：

- `file_type`
- `extraction_mode`

### 这里先不要追求“所有字段一步到位”

今天 schema 最重要的价值是：

- 帮 router 收住边界
- 帮 service 明确输入输出
- 帮 Day 5 留下稳定接力点

只要今天能把：

```text
导入返回什么
创建任务需要什么
任务详情至少长什么样
```

讲清楚，  
Day 4 就已经很稳了。

---

## 11:30 - 12:00：先决定今天怎么验收

Day 4 验收不要看“功能数量”，  
要看主链有没有真的立住。

今天最小验收应该围绕这 5 个问题：

1. `/tasks/import` 能不能让 CSV / JSON 走原生解析，其它格式走 MarkItDown 尝试解析？
2. 导入之后能不能返回一个清楚的 `dataset_id` 和 `extraction_mode`？
3. `/tasks` 能不能根据 `dataset_id` 创建任务？
4. 任务创建之后能不能返回 `task_id` 和初始状态？
5. `GET /tasks/{task_id}` 能不能查到最小任务详情？

---

## 下午编码：14:00 - 18:00

## 14:00 - 14:40：先把 `shcemas/task_schema.py` 立起来

### `shcemas/task_schema.py` 练手骨架版

```python
from pydantic import BaseModel, Field


class ImportMetadata(BaseModel):
    # 你要做的事：
    # 1. 定义来源平台
    # 2. 定义产品线
    # 3. 定义时间范围
    raise NotImplementedError


class CreateTaskRequest(BaseModel):
    # 你要做的事：
    # 1. 至少接 dataset_id
    # 2. 至少接 task_name
    raise NotImplementedError
```

### `shcemas/task_schema.py` 参考答案

```python
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"


class ImportMetadata(BaseModel):
    source_platform: str = Field(..., description="来源平台")
    product_line: str | None = Field(default=None, description="产品线")
    date_start: date | None = Field(default=None, description="起始日期")
    date_end: date | None = Field(default=None, description="结束日期")


class ImportDatasetResponse(BaseModel):
    dataset_id: str
    file_name: str
    file_type: str
    extraction_mode: str
    sample_count: int
    preview_texts: list[str] = Field(default_factory=list)
    metadata: ImportMetadata


class CreateTaskRequest(BaseModel):
    dataset_id: str
    task_name: str = Field(..., min_length=1, description="任务名称")


class CreateTaskResponse(BaseModel):
    task_id: str
    dataset_id: str
    status: TaskStatus
    created_at: datetime


class TaskDetailResponse(BaseModel):
    task_id: str
    dataset_id: str
    task_name: str
    status: TaskStatus
    sample_count: int
    source_platform: str
    product_line: str | None = None
    created_at: datetime
```

### 这里要先理解的点

Day 4 的 schema 不是为了把未来所有分析结果一次定义完。  
而是为了先把“导入输出”和“任务输入”收成稳定接口契约。

---

## 14:40 - 15:10：先补 `models/` 持久结构

今天既然决定把查表下沉到 `crud/`，  
那 `models/` 也要先有最小落点。

建议先补：

- `models/dataset_model.py`
- `models/task_model.py`

### `models/dataset_model.py` 参考答案

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DatasetModel(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(32))
    extraction_mode: Mapped[str] = mapped_column(String(64))
    source_platform: Mapped[str] = mapped_column(String(64))
    product_line: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### `models/task_model.py` 参考答案

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class TaskModel(Base):
    __tablename__ = "analysis_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.dataset_id"))
    task_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    source_platform: Mapped[str] = mapped_column(String(64))
    product_line: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## 15:10 - 15:40：把查表和写表下沉到 `crud/`

建议先补：

- `crud/dataset_crud.py`
- `crud/task_crud.py`

### `crud/task_crud.py` 参考答案

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task_model import Task
from shcemas.task_schema import CreateTaskPayload


async def create_task(session: AsyncSession, payload: CreateTaskPayload) -> Task:
    task = Task(**payload.model_dump(mode="python"))
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


async def get_task_detail(session: AsyncSession, task_id: str) -> Task | None:
    stmt = select(Task).where(Task.task_id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

### `crud/dataset_crud.py` 参考答案

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dataset_model import Dataset
from shcemas.task_schema import CreateDatasetPayload


async def create_dataset(session: AsyncSession, payload: CreateDatasetPayload) -> Dataset:
    dataset = Dataset(**payload.model_dump())
    session.add(dataset)
    await session.flush()
    await session.refresh(dataset)
    return dataset


async def get_dataset_by_id(session: AsyncSession, dataset_id: str) -> Dataset | None:
    stmt = select(Dataset).where(Dataset.dataset_id == dataset_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

---

## 15:40 - 16:30：在 `services/task_service.py` 里只保留业务编排

### `services/task_service.py` 练手骨架版

```python
from fastapi import UploadFile


class TaskService:
    async def build_dataset_import(self, file: UploadFile, metadata):
        # 你要做的事：
        # 1. 提取文件后缀，没有后缀时使用 bin
        # 2. 调用抽取逻辑，CSV / JSON 走原生解析，其它格式走 MarkItDown
        # 3. 生成 dataset payload
        # 4. 返回 dataset payload + response schema
        raise NotImplementedError

    def build_task_create_payload(self, dataset, payload):
        # 你要做的事：
        # 1. 根据 dataset 组装 task payload
        # 2. 返回 task payload + response schema
        raise NotImplementedError
```

### `services/task_service.py` 参考答案

```python
import csv
import json
from datetime import datetime
from io import BytesIO, StringIO
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from models.dataset_model import Dataset
from shcemas.task_schema import (
    CreateDatasetPayload,
    CreateTaskRequest,
    CreateTaskPayload,
    CreateTaskResponse,
    ImportDatasetResponse,
    ImportMetadata,
    TaskStatus,
)

NATIVE_IMPORT_TYPES = {"csv", "json"}


class TaskService:
    async def build_dataset_import(
            self,
            file: UploadFile,
            metadata: ImportMetadata,
    ) -> tuple[CreateDatasetPayload, ImportDatasetResponse]:
        suffix = self._extract_suffix(file.filename)
        file_bytes = await file.read()
        rows, extraction_mode = self._extract_rows(file_bytes=file_bytes, file_type=suffix)

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="empty dataset is not allowed",
            )

        dataset_id = str(uuid4())
        dataset_payload = CreateDatasetPayload(
            dataset_id=dataset_id,
            file_name=file.filename or "unknown",
            file_type=suffix,
            extraction_mode=extraction_mode,
            source_platform=metadata.source_platform,
            product_line=metadata.product_line,
            sample_count=len(rows),
            raw_text="\n".join(item["content"] for item in rows),
        )

        preview_texts = [item["content"] for item in rows[:3]]
        response = ImportDatasetResponse(
            dataset_id=dataset_id,
            file_name=file.filename or "unknown",
            file_type=suffix,
            extraction_mode=extraction_mode,
            sample_count=len(rows),
            preview_texts=preview_texts,
            metadata=metadata,
        )
        return dataset_payload, response

    def build_task_create_payload(
            self,
            dataset: Dataset,
            payload: CreateTaskRequest,
    ) -> tuple[CreateTaskPayload, CreateTaskResponse]:
        task_id = str(uuid4())
        now = datetime.utcnow()
        task_payload = CreateTaskPayload(
            task_id=task_id,
            dataset_id=payload.dataset_id,
            task_name=payload.task_name,
            status=TaskStatus.pending,
            sample_count=dataset.sample_count,
            source_platform=dataset.source_platform,
            product_line=dataset.product_line,
            created_at=now,
        )
        response = CreateTaskResponse(
            task_id=task_id,
            dataset_id=payload.dataset_id,
            status=TaskStatus.pending,
            created_at=now,
        )
        return task_payload, response

    @staticmethod
    def _extract_suffix(filename: str | None) -> str:
        if not filename or "." not in filename:
            return "bin"
        return filename.rsplit(".", 1)[-1].lower()

    def _extract_rows(self, file_bytes: bytes, file_type: str) -> tuple[list[dict], str]:
        if file_type == "csv":
            return self._parse_csv(file_bytes.decode("utf-8")), "csv_adapter"
        if file_type == "json":
            return self._parse_json(file_bytes.decode("utf-8")), "json_adapter"
        return self._parse_with_markitdown(file_bytes=file_bytes, file_type=file_type)

    @staticmethod
    def _parse_with_markitdown(file_bytes: bytes, file_type: str) -> tuple[list[dict], str]:
        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"markitdown support is not installed for .{file_type} files",
            ) from exc

        stream = BytesIO(file_bytes)
        stream.name = f"upload.{file_type}"

        converter = MarkItDown(enable_plugins=False)
        try:
            result = converter.convert_stream(stream)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"markitdown failed to parse .{file_type} file",
            ) from exc

        markdown_text = (result.text_content or "").strip()
        if not markdown_text:
            return [], "markitdown_adapter"

        rows = [
            {
                "content": markdown_text,
                "published_at": None,
                "extra": {"file_type": file_type, "byte_size": len(file_bytes)},
            }
        ]
        return rows, "markitdown_adapter"

    def _parse_csv(self, raw_text: str) -> list[dict]:
        reader = csv.DictReader(StringIO(raw_text))
        rows = []
        for item in reader:
            content = (item.get("content") or "").strip()
            if not content:
                continue
            rows.append(
                {
                    "content": content,
                    "published_at": item.get("published_at"),
                    "extra": item,
                }
            )
        return rows

    def _parse_json(self, raw_text: str) -> list[dict]:
        payload = json.loads(raw_text)
        if not isinstance(payload, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="json payload must be a list",
            )

        rows = []
        for item in payload:
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            rows.append(
                {
                    "content": content,
                    "published_at": item.get("published_at"),
                    "extra": item,
                }
            )
        return rows


task_service = TaskService()
```

### 这里要先理解的点

1. `dataset_id` 的价值非常大，它把导入和任务创建自然分开了  
2. `TaskService` 里今天先形成“adapter -> normalized payload”的抽取边界  
3. `TaskService` 不应该接 `session`，它只负责构建 payload 和 response  
4. `router / service / crud` 之间传递的数据格式应该优先用 `schemas/` 里的类，而不是裸 `dict`  
5. `create_dataset / get_dataset_by_id / create_task / get_task_detail` 这种操作应该落在 `crud/`  
6. `NATIVE_IMPORT_TYPES` 只标记原生结构化解析入口，其它格式交给 MarkItDown 尝试抽取  
7. Day 5 仍然接的是统一后的 dataset，不把清洗和标准化提前写满

---

## 15:30 - 16:20：更新 `router/tasks.py`

### `router/tasks.py` 练手骨架版

```python
from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/import")
async def import_task_data():
    raise NotImplementedError


@router.post("")
async def create_task():
    raise NotImplementedError


@router.get("/{task_id}")
async def get_task_detail(task_id: str):
    raise NotImplementedError
```

### `router/tasks.py` 参考答案

```python
from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile

from conf.db_conf import get_db
from crud.dataset_crud import create_dataset, get_dataset_by_id
from crud.task_crud import create_task, get_task_detail
from services.task_service import task_service
from shcemas.task_schema import CreateTaskRequest, ImportMetadata, TaskDetailResponse, TaskStatus
from utils.response import error_response, success_response

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/import")
async def import_task_data(
    file: UploadFile = File(...),
    source_platform: str = Form(...),
    product_line: str | None = Form(default=None),
    date_start: date | None = Form(default=None),
    date_end: date | None = Form(default=None),
    db=Depends(get_db),
):
    metadata = ImportMetadata(
        source_platform=source_platform,
        product_line=product_line,
        date_start=date_start,
        date_end=date_end,
    )
    dataset_payload, response_data = await task_service.build_dataset_import(file=file, metadata=metadata)
    await create_dataset(session=db, payload=dataset_payload)
    await db.commit()
    return success_response(data=response_data.model_dump(), message="dataset imported")


@router.post("")
async def create_task_endpoint(payload: CreateTaskRequest, db=Depends(get_db)):
    dataset = await get_dataset_by_id(session=db, dataset_id=payload.dataset_id)
    if dataset is None:
        return error_response(message="dataset not found", code=1, data=None)

    task_payload, response_data = task_service.build_task_create_payload(dataset=dataset, payload=payload)
    await create_task(session=db, payload=task_payload)
    await db.commit()
    return success_response(data=response_data.model_dump(), message="task created")


@router.get("/{task_id}")
async def get_task_detail_endpoint(task_id: str, db=Depends(get_db)):
    task = await get_task_detail(session=db, task_id=task_id)
    if task is None:
        return error_response(message="task not found", code=1, data=None)

    data = TaskDetailResponse(
        task_id=task.task_id,
        dataset_id=task.dataset_id,
        task_name=task.task_name,
        status=TaskStatus(task.status),
        sample_count=task.sample_count,
        source_platform=task.source_platform,
        product_line=task.product_line,
        created_at=task.created_at,
    )
    return success_response(data=data.model_dump(), message="task detail")
```

### 为什么 router 层今天一定要克制

因为 Day 4 的 router 只应该做：

- 接收参数
- 组装 schema
- 调用 service
- 返回统一响应

如果你今天就在 router 里写文件解析和任务拼装，  
后面会很难继续演进。

---

## 16:20 - 17:10：把 `main.py` 的路由入口补齐

如果当前项目里的 `main.py` 还没有把 `health` 和 `tasks` 稳定注册起来，  
那 Day 4 应该顺手把这个入口补齐。

### `main.py` 参考答案

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from conf.db_conf import close_db
from conf.logging import app_logger, setup_logger
from conf.settings import settings
from router.health import router as health_router
from router.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logger()
    app_logger.bind(module="system").info("application starts")
    try:
        yield
    finally:
        app_logger.bind(module="system").info("application ends")
        logger_complete = app_logger.complete()
        if logger_complete:
            await logger_complete
        await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.APP_DEBUG,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    app.include_router(health_router, prefix=settings.APP_API_PREFIX)
    app.include_router(tasks_router, prefix=settings.APP_API_PREFIX)
    return app


app = create_app()
```

### 今天为什么值得补这一步

因为 Day 4 不是只写局部文件，  
而是要让这条链真正能从 HTTP 入口走到 service。

---

## 17:10 - 18:00：整理 Day 5 的输入

Day 5 会开始进入：

- 文本去空
- 文本清洗
- 字段标准化
- 无效样本过滤

所以 Day 4 结束前，  
你至少要准备好这些输入：

- dataset 里已经有最小样本列表
- 每条样本至少有 `content`
- 文件级元信息已经有稳定落点
- `task_id` 和 `dataset_id` 的关系已经能讲清楚

这会让 Day 5 非常顺。

---

## 晚上复盘：20:00 - 21:00

### 今晚你必须自己讲顺的 8 个点

1. Day 4 的本质为什么是“输入变任务”，不是“分析做深”？
2. 为什么导入动作和任务创建动作不能完全混在一个黑盒接口里？
3. `dataset_id` 为什么值得先立住？
4. 为什么用了 MarkItDown 也仍然要保留大小限制、依赖检查和失败口径？
5. 为什么 `router/tasks.py` 不该直接堆业务逻辑？
6. 为什么 `get_task_detail` 这种读操作不能直接堆在 service 里查表？
7. 今天的任务状态为什么先以 `pending` / `queued` 为主？
8. Day 5 会接着 Day 4 的哪个对象继续往下做？

---

## 今日验收标准

- `steps/day4.md` 对 Day 4 的目标、边界和文件落点讲清楚
- `/tasks/import` 的职责和输入输出边界讲清楚
- `/tasks` 的职责和输入输出边界讲清楚
- `shcemas/task_schema.py` 的最小设计讲清楚
- `models/`、`crud/`、`services/task_service.py` 的分层职责讲清楚
- 原生 adapter 和 `MarkItDown adapter` 的分流边界讲清楚
- `dataset_id -> task_id` 这条中间链路讲清楚
- Day 5 的预处理输入已经准备好

---

## 今天最容易踩的坑

### 坑 1：把导入和任务创建完全写成一个接口

问题：

- 失败点不清楚
- 后面难扩预处理
- 页面也不好查输入和任务的关系

规避建议：

- 先导入，拿到 `dataset_id`
- 再创建任务，拿到 `task_id`

### 坑 1.5：把 MarkItDown 理解成“什么都能成功解析”

问题：

- 文件可以进入 MarkItDown，但不代表一定能抽取出有效文本
- 环境没装依赖时错误不清楚
- 大文件和压缩包会把导入边界打穿

规避建议：

- 明确 CSV / JSON 原生解析，其它格式交给 MarkItDown 尝试
- 明确大小限制和依赖检查
- MarkItDown 解析失败时返回清晰错误

### 坑 2：在 router 里直接写解析逻辑

问题：

- HTTP 层过厚
- 后面不好测试
- 逻辑没地方复用

规避建议：

- router 只组装参数
- 真正解析放进 `services/task_service.py`

### 坑 3：把 crud 和 service 混成一层

问题：

- `get_task_detail` 这种查表动作会直接粘在 service 里
- 后面 service 会越来越像“业务 + SQL 杂糅层”

规避建议：

- 查表 / 写表下沉到 `crud/`
- service 只保留编排、校验和 schema 组装

### 坑 4：今天就开始做完整 ORM 之外的大扩写

问题：

- 花很多时间在结构搭建
- 主链反而没先跑通

规避建议：

- Day 4 先把最小输入和任务边界立住
- 持久化后面再逐步加

### 坑 5：把 Day 5 的预处理偷偷提前做满

问题：

- Day 4 职责失焦
- 接口越来越重

规避建议：

- Day 4 只做最小可读解析
- Day 5 再专门进入标准化

### 坑 6：顺手去改当前目录命名和结构

问题：

- 任务目标被打断
- 文档和代码容易失配

规避建议：

- 先沿用当前仓库真实结构
- 等主链稳定后再谈整理

---

## 给明天的交接提示

明天开始，SentiFlow 就不只是“能收进一批文本”，  
而是要开始真正把这批文本整理成后续分析能消费的标准输入。

也就是说，后面会继续走向：

```text
导入文本
-> 建立 dataset
-> 创建 task
-> 预处理
-> 分析
-> 查结果
```

所以 Day 4 最关键的交接只有一句话：

```text
先把“文件输入”稳定变成“dataset + task”这两个对象，后面的预处理和分析主链才有明确接力点。
```

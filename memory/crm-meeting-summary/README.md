# CRM Object Memory Design

## 目标

这套 CRM memory 先服务 **CRM 对象本身**，不是先服务某个 summary 组件。

它解决的问题只有两个：
1. 让对象拥有可持续积累的记忆
2. 让后续消费方能在不覆盖当前证据的前提下读取这些记忆

当前对象范围：
- `account`
- `opportunity`
- `contact`
- `person`

`crm-meeting-summary` 只是消费方之一，不是这套 memory 的定义中心。

## 最小心智模型

### 对象层
每个对象都有自己的 memory profile。

### 时间层
每个 profile 只分两层：
- `today`：当前这次 interaction 之后，这个对象今天的状态
- `long_term`：跨多次互动后稳定下来的对象特性和模式

### 基本原则
- memory 是对象记忆，不是会议纪要堆积
- 当前 evidence 优先于旧 memory
- CRM fact 不自动等于 memory
- 字段定义看 `schema.md`
- 演化规则看 `lifecycle.md`

## 文档地图

### [schema.md](schema.md)
回答：**这个 profile 长什么样？**

内容包括：
- 顶层字段
- `today` / `long_term` 结构约束
- 四类对象字段定义
- 最小合法示例

### [lifecycle.md](lifecycle.md)
回答：**什么时候写 `today`，什么时候升 `long_term`？**

内容包括：
- `today` / `long_term` 的语义边界
- 状态定义
- CRM fact → `today` → `long_term` 的升级路径
- 不进入 memory 的情况
- 使用红线

### [index.html](index.html)
回答：**怎么最快看懂这套设计？**

内容包括：
- 一句话目标
- 总图
- 四类对象概览
- 一个最小 profile 示例
- 一张写入规则简表

## 使用边界

这套 memory 的消费边界只有 3 条：
1. 当前 meeting evidence 优先
2. 当前 CRM facts 次之
3. memory 只补对象解释层，不覆盖当前证据

`memory_conflicts` 属于 skill 的输出 / 消费层概念，用来显式暴露旧 memory 与当前 meeting 或 CRM evidence 的冲突；它不是 profile schema 本身的字段。

## 推荐阅读顺序

1. [README.md](README.md)
2. [schema.md](schema.md)
3. [lifecycle.md](lifecycle.md)
4. [index.html](index.html)

如果你要先建立主线，先看 `README.md`。
如果你要落结构，直接看 `schema.md`。
如果你要判断写入和升级，直接看 `lifecycle.md`。
如果你要快速扫一眼全貌，再看 `index.html`。

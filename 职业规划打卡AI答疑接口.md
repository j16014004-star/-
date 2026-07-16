# 职业规划打卡 AI 答疑接口

> 本文只包含本次新增接口。接口均需要 JWT 登录态，后端必须校验执行任务属于当前用户。

## 调用流程

1. 用户在打卡任务下填写学习问题。
2. 前端创建答疑任务。
3. 前端复用 `GET /api/ai/tasks/{task_id}` 轮询。
4. AI 任务成功后，前端获取问答详情并展示。

## 1. 提交学习问题

`POST /api/career-plan-executions/tasks/{execution_task_id}/questions`

请求：

```json
{
  "question": "FastAPI 的 Depends 和直接调用函数有什么区别？在这个练习里应该怎样使用？"
}
```

校验：`question` 去除首尾空格后为 5~1000 字。

返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "task_career_question_xxx",
    "task_type": "career_plan_question",
    "status": "pending",
    "result_id": null,
    "question_id": 801,
    "poll_after_seconds": 1
  }
}
```

后端处理：

- 创建问答记录，状态为 `pending`。
- 创建通用 AI 任务，`task_type = career_plan_question`。
- Agent 上下文应包含当前问题、任务标题和描述、所属阶段、周次、用户已确认的职业规划，以及必要的职业规划知识库召回内容。
- 回答应针对当前问题给出解释、操作步骤和与当前任务相关的示例，不能虚构用户已完成的内容。
- AI 成功后把问答状态改为 `answered`，保存回答，并让 AI Task 的 `result_id` 指向 `question_id`。

## 2. 获取某个打卡任务的历史问答

`GET /api/career-plan-executions/tasks/{execution_task_id}/questions`

返回：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 801,
      "execution_task_id": 701,
      "question": "FastAPI 的 Depends 应该怎样使用？",
      "answer": "Depends 用于声明并复用依赖关系……",
      "status": "answered",
      "error_message": null,
      "created_at": "2026-07-16T15:00:00",
      "answered_at": "2026-07-16T15:00:08"
    }
  ]
}
```

按 `created_at` 倒序返回。状态：`pending`、`answering`、`answered`、`failed`。

## 3. 获取单条问答详情

`GET /api/career-plan-executions/questions/{question_id}`

返回单个问答对象，结构与历史问答数组元素相同。

## 通用 AI 任务要求

现有接口 `GET /api/ai/tasks/{task_id}` 需要支持 `task_type = career_plan_question`。成功时 `result_id` 返回问答记录 ID。

## 安全与业务要求

- 问题、任务、执行计划和职业规划必须属于当前 JWT 用户，越权统一返回 404。
- 后端应限制提交频率和单用户并发，避免重复点击造成多次模型调用。
- 不把用户问题、规划正文、模型 Prompt 或密钥完整写入日志。
- 对密码、Token、API Key 等敏感内容进行提示或脱敏，不把它们作为普通知识长期保存。
- 模型失败时保存 `failed` 状态和可展示的 `error_message`，历史记录仍可查询。

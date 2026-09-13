# 自动续火（AstrBot 插件）

每天固定时间向配置的群聊列表和私聊列表各发送一次续火消息。

## 配置

- `group_targets`：群聊 UMO，每行一个，例如 `qq:GroupMessage:123456`。
- `private_targets`：私聊 UMO，每行一个，例如 `qq:FriendMessage:987654`。
- `send_time`：每天发送时间，只填一个 `HH:MM`，默认 `09:00`。
- `message`：发送内容。
- `enabled`：是否启用。
- `admin_only`：是否仅管理员可执行命令。

## 命令

- `/续火 开启`：将当前群聊或私聊加入对应列表并启用调度。
- `/续火 关闭`：从对应列表移除当前会话。
- `/续火 状态`：查看群聊、私聊目标数量和发送时间。

插件使用 AstrBot 的 UMO 发送入口，由 AstrBot 根据 `GroupMessage` 和 `FriendMessage` 分别路由到群聊或私聊适配器。

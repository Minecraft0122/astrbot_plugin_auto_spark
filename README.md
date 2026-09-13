# 自动续火（AstrBot 插件）

每天在一个固定时间向配置的群聊列表和私聊列表各发送一次续火消息。插件分别处理两类目标，多个目标和多个机器人互不影响。

## 配置

- `platform_ids`：机器人实例 ID 列表，可以填写多个，例如 `qq1`、`qq2`。
- `group_targets`：群聊列表。填写群号时，会自动绑定到每个 `platform_ids` 机器人；也可以填完整 UMO，例如 `qq1:GroupMessage:123456`。
- `private_targets`：私聊列表。填写用户 QQ 时，会自动绑定到每个 `platform_ids` 机器人；也可以填完整 UMO，例如 `qq1:FriendMessage:987654`。
- `send_time`：每天发送时间，只填一个 `HH:MM`，默认 `09:00`。每天只发送一次。
- `message`：发送内容。
- `enabled`：是否启用。

如果目标列表填写的是纯数字但没有填写 `platform_ids`，插件会跳过这些目标并在日志中提示需要填写机器人实例 ID，或者改用完整 UMO。

配置示例：

```yaml
enabled: true
platform_ids:
  - qq1
  - qq2
group_targets:
  - "123456"
  - "234567"
private_targets:
  - "987654"
send_time: "09:00"
message: "续火啦 🔥"
```

多个机器人实例也可以使用完整 UMO 精确绑定：

```yaml
group_targets:
  - "qq1:GroupMessage:123456"
  - "qq2:GroupMessage:123456"
private_targets:
  - "qq1:FriendMessage:987654"
```

群聊和私聊最终通过 AstrBot 的会话发送入口发出；AstrBot 会根据 `GroupMessage` 或 `FriendMessage` 自动调用对应适配器的群聊或私聊发送方法。

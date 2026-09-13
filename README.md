# 自动续火（AstrBot 插件）

每天在一个固定时间向配置的群聊列表和私聊列表各发送一次续火消息。插件分别处理两类目标，多个目标互不影响。

## 配置

- `platform_id`：平台实例 ID，例如 `qq`。填写后，下面两个列表可以直接填群号或用户 QQ。
- `group_targets`：群聊列表，可以填 `123456`，也可以填完整 UMO `qq:GroupMessage:123456`。
- `private_targets`：私聊列表，可以填 `987654`，也可以填完整 UMO `qq:FriendMessage:987654`。
- `send_time`：每天发送时间，只填一个 `HH:MM`，默认 `09:00`。每天只发送一次。
- `message`：发送内容。
- `enabled`：是否启用。

配置示例：

```yaml
platform_id: qq
group_targets:
  - "123456"
  - "234567"
private_targets:
  - "987654"
  - "876543"
send_time: "09:00"
message: "续火啦 🔥"
enabled: true
```

如果使用多个平台实例，请在列表中直接填写完整 UMO，例如 `qq:GroupMessage:123456` 或 `qq:FriendMessage:987654`。

群聊和私聊最终都通过 AstrBot 的会话发送入口发出；AstrBot 会根据 `GroupMessage` 或 `FriendMessage` 自动调用对应适配器的群聊或私聊发送方法。

# 自动续火（AstrBot 插件）

插件按会话独立维护定时任务，同时支持群聊和私聊。每个会话通过 `unified_msg_origin` 唯一标识，因此可同时续火多个群和多个私聊。

## 使用

在目标群聊或私聊中发送：

- `/续火 开启 [间隔秒]`：开启当前会话，间隔可选（默认配置间隔）。
- `/续火 关闭`：关闭当前会话。
- `/续火 状态`：查看当前会话及活动会话数量。

会话列表会保存到 AstrBot 的插件数据目录 `plugin_data/astrbot_plugin_auto_spark/targets.json`，重启后自动恢复。插件配置中的 `targets` 可填写启动时要续火的会话 ID（每行一个），`message` 设置发送内容。

配置示例（不同平台的消息类型名称以 AstrBot 的 `MessageType` 为准）：

```yaml
targets: |
  qq:GroupMessage:123456
  qq:FriendMessage:987654
```

每条 UMO 都包含平台实例、消息类型和会话 ID；因此多个机器人实例、多个群和多个私聊可以同时运行。

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from scheduler import SparkScheduler

def test_daily_scheduler_sends_group_and_private_once():
    async def run():
        sent=[]
        async def send_group(umo, message): sent.append(("group", umo, message)); return True
        async def send_private(umo, message): sent.append(("private", umo, message)); return True
        groups=["qq:GroupMessage:g1", "qq:GroupMessage:g2"]
        privates=["qq:FriendMessage:u1"]
        scheduler=SparkScheduler(send_group, send_private, "续火", "09:00", target_provider=lambda: (groups, privates))
        assert await scheduler.send_once() == (2, 1)
        assert sent == [("group", groups[0], "续火"), ("group", groups[1], "续火"), ("private", privates[0], "续火")]
        scheduler.start()
        assert not scheduler.start()
        await scheduler.stop()
        scheduler.start()
        await scheduler.stop()
    asyncio.run(run())

if __name__ == "__main__":
    test_daily_scheduler_sends_group_and_private_once()
    print("daily scheduler test passed")

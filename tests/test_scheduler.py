import asyncio
from scheduler import SparkScheduler

def test_daily_scheduler_sends_separate_lists():
    async def run():
        got=[]
        async def group(umo, msg): got.append(("group", umo)); return True
        async def private(umo, msg): got.append(("private", umo)); return True
        s=SparkScheduler(group, private, "续火", "09:00")
        assert await s.send_once(["qq:GroupMessage:g1"], ["qq:FriendMessage:u1"]) == (1, 1)
        assert got == [("group", "qq:GroupMessage:g1"), ("private", "qq:FriendMessage:u1")]
        s.start(); await s.stop(); s.start(); await s.stop()
    asyncio.run(run())

if __name__ == "__main__":
    test_daily_scheduler_sends_separate_lists()
    print("daily scheduler test passed")

import asyncio
from scheduler import SparkScheduler

def test_multiple_group_and_private_targets():
    async def run():
        sent=[]
        async def send(umo, message): sent.append((umo,message)); return True
        scheduler=SparkScheduler(send, 10, "火还在吗？", True)
        targets=["qq:GroupMessage:g1","qq:GroupMessage:g2","qq:FriendMessage:u1","qq:FriendMessage:u2"]
        for target in targets: assert scheduler.start(target)
        assert not scheduler.start(targets[0])
        await asyncio.sleep(0.03)
        assert {target for target,_ in sent} == set(targets)
        assert await scheduler.stop(targets[0])
        await scheduler.stop_all()
    asyncio.run(run())

if __name__ == "__main__":
    test_multiple_group_and_private_targets()
    print("multi-target scheduler test passed")

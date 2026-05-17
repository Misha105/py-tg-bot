"""Tests for bot.services.context_manager module."""

from bot.services.context_manager import ConversationContext


async def test_add_and_get_history() -> None:
    ctx = ConversationContext(max_history=10)
    await ctx.add_message(user_id=1, role="user", content="hello")
    await ctx.add_message(user_id=1, role="assistant", content="hi")
    history = await ctx.get_history(user_id=1)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "hello"}
    assert history[1] == {"role": "assistant", "content": "hi"}


async def test_max_history_limit() -> None:
    ctx = ConversationContext(max_history=3)
    for i in range(4):
        await ctx.add_message(user_id=1, role="user", content=f"msg_{i}")
    history = await ctx.get_history(user_id=1)
    assert len(history) == 3
    assert history[0]["content"] == "msg_1"
    assert history[2]["content"] == "msg_3"


async def test_clear_history() -> None:
    ctx = ConversationContext(max_history=10)
    await ctx.add_message(user_id=1, role="user", content="hello")
    await ctx.clear(user_id=1)
    history = await ctx.get_history(user_id=1)
    assert history == []


async def test_empty_history() -> None:
    ctx = ConversationContext(max_history=10)
    history = await ctx.get_history(user_id=999)
    assert history == []


async def test_multiple_users_isolated() -> None:
    ctx = ConversationContext(max_history=10)
    await ctx.add_message(user_id=1, role="user", content="user1_msg")
    await ctx.add_message(user_id=2, role="user", content="user2_msg")
    assert (await ctx.get_history(1))[0]["content"] == "user1_msg"
    assert (await ctx.get_history(2))[0]["content"] == "user2_msg"

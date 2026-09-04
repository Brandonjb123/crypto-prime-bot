from src.application.shutdown import ShutdownHandler


class TestShutdownHandler:
    async def test_register_and_shutdown(self):
        handler = ShutdownHandler()
        called = []

        def hook():
            called.append("shutdown")

        handler.register(hook)
        await handler.shutdown()
        assert called == ["shutdown"]

    async def test_multiple_hooks(self):
        handler = ShutdownHandler()
        order = []

        handler.register(lambda: order.append("first"))
        handler.register(lambda: order.append("second"))
        await handler.shutdown()
        assert order == ["second", "first"]  # reversed

    async def test_async_hook(self):
        handler = ShutdownHandler()
        called = []

        async def async_hook():
            called.append("async_done")

        handler.register(async_hook)
        await handler.shutdown()
        assert called == ["async_done"]

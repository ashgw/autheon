from typing import Callable, Coroutine
from fastapi.routing import APIRoute
from fastapi import Request, Response


class AutheonRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[None, None, Response]]:
        original_route_handler = super().get_route_handler()

        async def route_handler(request: Request) -> Response:
            return await original_route_handler(Request(request.scope, request.receive))

        return route_handler

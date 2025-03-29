from typing import Optional, final

from fastapi import Query, APIRouter
from overrides import override
from starlette.requests import Request
from starlette.responses import Response

from autheon.libtypes import FallbackSecrets
from autheon.providers.base import Provider
from autheon.authorize import Authorize
from autheon.callback import Callback
from autheon.signout import Signout
from autheon.signin import SignInCallback
from autheon.oauth2_baseflow import OAuth2Base
from autheon.jwts.handler import JWTHandler
from autheon.adapters.fastapi.route import AutheonRoute
from autheon.csrf import CSRF


@final
class FastAPIOAuthFlow(OAuth2Base):
    def __init__(
        self,
        *,
        provider: Provider,
        fallback_secrets: FallbackSecrets,
        signin_uri: str,
        signout_url: str,
        callback_uri: str,
        jwt_uri: str,
        csrf_token_uri: str,
        post_signin_uri: str,
        post_signout_uri: str,
        error_uri: str,
        jwt_max_age: int,
        signin_callback: Optional[SignInCallback],
    ) -> None:
        super().__init__(
            provider=provider,
            fallback_secrets=fallback_secrets,
            signin_uri=signin_uri + "/" + provider.provider,
            signout_url=signout_url,
            callback_uri=callback_uri,
            jwt_uri=jwt_uri,
            csrf_token_uri=csrf_token_uri,
            post_signin_uri=post_signin_uri,
            signin_callback=signin_callback,
            post_signout_uri=post_signout_uri,
            error_uri=error_uri,
            jwt_max_age=jwt_max_age,
        )
        CSRF.init_once(fallback_secrets=fallback_secrets)
        self.auth_route = APIRouter()
        self.auth_route.route_class = AutheonRoute
        self.activate()

    @property
    def router(self) -> APIRouter:
        return self.auth_route

    @override
    def on_signin(self) -> None:
        @self.router.get(self.signin_uri)
        async def authorize(request: Request):  # type:ignore
            return Authorize(provider=self.provider, request=request)()

        @self.router.get(self.callback_uri + "/" + self.provider.provider)
        async def callback(  #  type: ignore
            req: Request,
            code: str = Query(...),
            state: str = Query(...),
        ):
            return await Callback(
                code=code,
                request=req,
                state=state,
                fallback_secrets=self.fallback_secrets,
                debug=self.debug,
                provider=self.provider,
                post_signin_uri=self.post_signin_uri,
                signin_callback=self.signin_callback,
                logger=self.logger,
                error_uri=self.error_uri,
                jwt_max_age=self.jwt_max_age,
            )()

    @override
    def on_signout(self) -> None:
        @self.router.get(self.signout_uri)
        def signout(request: Request) -> Response:
            return Signout(
                post_signout_uri=self.post_signout_uri,
                request=request,
                error_uri=self.error_uri,
                logger=self.logger,
                debug=self.debug,
                fallback_secrets=self.fallback_secrets,
            )()

    @override
    def jwt(self) -> None:
        @self.router.get(self.jwt_uri)
        def get_jwt(request: Request, response: Response) -> Response:
            return JWTHandler(
                request=request,
                response=response,
                fallback_secrets=self.fallback_secrets,
                logger=self.logger,
                debug=self.debug,
            ).get_jwt()

    @override
    def activate(self) -> None:
        self.on_signin()
        self.jwt()
        self.on_signout()

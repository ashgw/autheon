from logging import Logger
from typing import Annotated, Optional

from fastapi import APIRouter
from overrides import override
from fastauth.providers.base import Provider
from fastauth.authorize import Authorize
from fastauth.callback import Callback
from fastauth.signout import Signout
from fastauth.responses import OAuthRedirectResponse, OAuthResponse
from fastauth.requests import OAuthRequest
from fastauth.signin import SignIn
from fastauth.oauth2.base import OAuth2Base
from fastauth.data import CookiesData
from fastauth.log import logger as authlogger
from fastauth.jwts.handler import JWTHandler


class OAuth2(OAuth2Base):
    def __init__(
        self,
        *,
        provider: Provider,
        secret: str,
        debug: bool = True,
        signin_uri: str = "/auth/signin",
        signout_url: str = "/auth/signout",
        callback_uri: str = "/auth/callback",
        jwt_uri: str = "/auth/jwt",
        csrf_token_uri: str = "/auth/csrf-token",
        post_signin_uri: str = "/out",  # TODO: change
        post_signout_uri: str = "/in",  # TODO: change
        error_uri: str = "/auth/error",
        on_signin: Optional[SignIn] = None,
        jwt_max_age: int = CookiesData.JWT.max_age,
        logger: Logger = authlogger,
    ) -> None:
        super().__init__(
            provider=provider,
            secret=secret,
            debug=debug,
            signin_uri=signin_uri + "/" + provider.provider,
            signout_url=signout_url,
            callback_uri=callback_uri,
            jwt_uri=jwt_uri,
            csrf_token_uri=csrf_token_uri,
            post_signin_uri=post_signin_uri,
            post_signout_uri=post_signout_uri,
            error_uri=error_uri,
            jwt_max_age=jwt_max_age,
            logger=logger,
        )

    @property
    def router(self) -> APIRouter:
        return self.auth_route

    @override
    def on_signin(self) -> None:
        @self.router.get(self.signin_uri)
        async def authorize(request: OAuthRequest) -> OAuthRedirectResponse:
            return Authorize(provider=self.provider, request=request)()

        @self.router.get(self.callback_uri + "/" + self.provider.provider)
        async def callback(
            req: OAuthRequest,
            code: Annotated[
                str, "valid for 15 minutes max"
            ],  # TODO: change this to Query
            state: Annotated[str, "valid for 15 minutes max"],
        ) -> OAuthRedirectResponse:
            return Callback(
                code=code,
                request=req,
                state=state,
                debug=self.debug,
                provider=self.provider,
                post_signin_uri=self.post_signin_uri,
                secret=self.secret,
                logger=self.logger,
                error_uri=self.error_uri,
                jwt_max_age=self.jwt_max_age,
            )()

    @override
    def on_signout(self) -> None:
        @self.router.get(self.signout_uri)
        def signout(request: OAuthRequest) -> OAuthRedirectResponse:
            return Signout(
                post_signout_uri=self.post_signout_uri,
                request=request,
                secret=self.secret,
                error_uri=self.error_uri,
                logger=self.logger,
                debug=self.debug,
            )()

    @override
    def jwt(self) -> None:
        @self.router.get(self.jwt_uri)
        def get_jwt(request: OAuthRequest, response: OAuthResponse) -> OAuthResponse:
            return JWTHandler(
                request=request,
                response=response,
                secret=self.secret,
                logger=self.logger,
                debug=self.debug,
            ).get_jwt()

    @override
    def activate(self) -> None:
        self.on_signin()
        self.jwt()
        self.on_signout()

from logging import Logger

from starlette.requests import Request
from starlette.responses import Response

from autheon.providers.base import Provider
from autheon.const_data import CookieData
from autheon.cookies import Cookies
from autheon.adapters.use_response import use_response
from autheon.libtypes import FallbackSecrets, AccessToken
from autheon.jwts.operations import encipher_user_info
from autheon.signin import SignInCallback, check_signin_signature
from autheon.exceptions import InvalidState, CodeVerifierNotFound
from autheon.csrf import CSRF

from autheon.libtypes import UserInfo
from typing import Optional


class _CallbackCheck:
    def __init__(
        self,
        provider: Provider,
        post_signin_uri: str,
        error_uri: str,
        code: str,
        state: str,
        fallback_secrets: FallbackSecrets,
        logger: Logger,
        request: Request,
        jwt_max_age: int,
        signin_callback: Optional[SignInCallback],
        debug: bool,
    ) -> None:
        self.code = code
        self.provider = provider
        self.fallback_secrets = fallback_secrets
        self.logger = logger
        self.state = state
        self.debug = debug
        self.jwt_max_age = jwt_max_age
        self.signin_callback = signin_callback
        __base_url = request.base_url
        __response = use_response(response_type="redirect")
        self.success_response = __response(url=__base_url + post_signin_uri)  # type: ignore
        self.error_response = __response(url=__base_url + error_uri)  # type: ignore
        self.cookie = Cookies(request=request, response=self.success_response)

    def _is_state_valid(self) -> bool:
        if self.cookie.get(CookieData.State.name) != self.state:
            err = InvalidState()
            self.logger.error(err)
            if self.debug:
                raise err
            return False
        return True

    def _get_code_verifier(self) -> Optional[str]:
        code_verifier: Optional[str] = self.cookie.get(CookieData.Codeverifier.name)
        if code_verifier is None:
            err = CodeVerifierNotFound()
            self.logger.error(err)
            if self.debug:
                raise err
            return None
        return code_verifier


class Callback(_CallbackCheck):
    def __init__(
        self,
        *,
        provider: Provider,
        post_signin_uri: str,
        error_uri: str,
        code: str,
        state: str,
        fallback_secrets: FallbackSecrets,
        logger: Logger,
        jwt_max_age: int,
        signin_callback: Optional[SignInCallback],
        request: Request,
        debug: bool,
    ) -> None:
        super().__init__(
            provider=provider,
            post_signin_uri=post_signin_uri,
            error_uri=error_uri,
            code=code,
            state=state,
            fallback_secrets=fallback_secrets,
            logger=logger,
            jwt_max_age=jwt_max_age,
            signin_callback=signin_callback,
            request=request,
            debug=debug,
        )

    def set_jwt_cookie(self, user_info: UserInfo, max_age: int) -> None:
        self.cookie.set(
            key=CookieData.JWT.name,
            value=encipher_user_info(
                user_info=user_info,
                max_age=max_age,
                fallback_secrets=self.fallback_secrets,
            ),
            max_age=max_age,
        )

    def set_csrf_cookie(self) -> None:
        self.cookie.set(
            key=CookieData.CSRFToken.name,
            value=CSRF.gen_csrf_token(),
            max_age=CookieData.CSRFToken.max_age,
        )

    async def get_user_info(self) -> Optional[UserInfo]:
        valid_state: bool = self._is_state_valid()
        if not valid_state:
            return None
        code_verifier: Optional[str] = self._get_code_verifier()
        if code_verifier is None:
            return None
        access_token: Optional[AccessToken] = await self.provider.get_access_token(
            code_verifier=code_verifier, code=self.code, state=self.state
        )
        if access_token is None:
            return None
        user_info: Optional[UserInfo] = await self.provider.get_user_info(access_token)
        return user_info

    async def __call__(self) -> Response:
        user_info: Optional[UserInfo] = await self.get_user_info()
        if not user_info:
            return self.error_response
        self.set_csrf_cookie()
        self.set_jwt_cookie(user_info=user_info, max_age=self.jwt_max_age)
        if self.signin_callback:
            check_signin_signature(self.signin_callback)
            await self.signin_callback(user_info=user_info)
        return self.success_response

from logging import Logger
from typing import List
from fastauth.data import CookiesData, StatusCode
from fastauth.cookies import Cookie
from fastauth.utils import name_cookie
from fastauth.responses import OAuthRedirectResponse
from fastauth.requests import OAuthRequest
from fastauth.jwts.operations import decipher_jwt
from fastauth.exceptions import JSONWebTokenTampering
from jose.exceptions import JWTError  # type: ignore


class Signout:
    def __init__(
        self,
        *,
        post_signout_uri: str,
        secret: str,
        error_uri: str,
        logger: Logger,
        request: OAuthRequest,
        debug: bool,
        domain: str | None = None,
    ):
        self.post_signout_uri = post_signout_uri
        self.error_uri = error_uri
        self.logger = logger
        self.request = request
        self.domain = domain
        self.secret = secret
        self.debug = debug
        self.success_response = OAuthRedirectResponse(self.post_signout_uri)
        self.cookie = Cookie(request=request, response=self.success_response)

    def __call__(self) -> OAuthRedirectResponse:
        encrypted_jwt = self.cookie.get(name_cookie(name=CookiesData.JWT.name))
        if encrypted_jwt:
            try:
                decipher_jwt(encrypted_jwt=encrypted_jwt, key=self.secret)
            except JWTError as e:
                error = JSONWebTokenTampering(error=e)
                if self.debug:
                    raise error
                self.logger.warning(error)
                return OAuthRedirectResponse(
                    url=self.error_uri, status_code=StatusCode.BAD_REQUEST
                )

        cookies: List[str] = [
            CookiesData.State.name,
            CookiesData.Codeverifier.name,
            CookiesData.JWT.name,
            CookiesData.CSRFToken.name,
        ]
        for cookie in cookies:
            self.cookie.delete(
                key=name_cookie(name=cookie),
            )
        return self.success_response

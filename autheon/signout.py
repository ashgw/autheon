from logging import Logger
from typing import List

from starlette.requests import Request

from autheon.const_data import CookieData, StatusCode
from autheon.libtypes import FallbackSecrets
from autheon.cookies import Cookies
from fastapi.responses import Response
from autheon.adapters.use_response import use_response
from autheon.jwts.operations import decipher_jwt
from autheon.exceptions import JSONWebTokenTampering
from jose.exceptions import JWTError


class Signout:
    def __init__(
        self,
        *,
        post_signout_uri: str,
        request: Request,
        fallback_secrets: FallbackSecrets,
        error_uri: str,
        logger: Logger,
        debug: bool,
    ) -> None:
        self.post_signout_uri = post_signout_uri
        self.error_uri = error_uri
        self.request = request
        self.fallback_secrets = fallback_secrets
        self.logger = logger
        self.debug = debug
        self.__base_url = request.base_url
        self.redirect_response = use_response(response_type="redirect")
        self.success_response = self.redirect_response(
            url=str(self.__base_url) + self.post_signout_uri
        )  # type: ignore
        self.failure_response = self.redirect_response(
            url=str(self.__base_url) + self.error_uri,
            status_code=StatusCode.BAD_REQUEST,
        )  # type: ignore

        self.cookie = Cookies(request=request, response=self.success_response)

    def __call__(self) -> Response:
        encrypted_jwt = self.cookie.get(CookieData.JWT.name)
        if encrypted_jwt:
            try:
                decipher_jwt(
                    encrypted_jwt=encrypted_jwt, fallback_secrets=self.fallback_secrets
                )
            except JWTError as e:
                error = JSONWebTokenTampering(error=e)
                self.logger.warning(error)
                if self.debug:
                    raise error
                return self.failure_response

        cookies: List[str] = [
            CookieData.State.name,
            CookieData.Codeverifier.name,
            CookieData.JWT.name,
            CookieData.CSRFToken.name,
        ]
        for cookie in cookies:
            self.cookie.delete(
                key=cookie,
            )
        return self.success_response

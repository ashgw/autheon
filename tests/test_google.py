# TODO: write these better
import pytest

from unittest.mock import AsyncMock
from unittest.mock import patch


from typing import cast, Dict, Any

from dotenv import load_dotenv
from os import getenv


from autheon.providers.google.google import Google
from autheon.providers.google.schemas import (
    GoogleUserJSONData,
    serialize_user_info,
    serialize_access_token,
)
from pydantic import ValidationError
from autheon.exceptions import (
    InvalidUserInfoAccessRequest,
    InvalidTokenAcquisitionRequest,
    SchemaValidationError,
)
from autheon.const_data import StatusCode
from autheon.utils import gen_oauth_params
from autheon.libtypes import GrantSecurityParams
from autheon.config import AuthConfig
from .utils import get_method_to_patch

load_dotenv()

client_id: str = cast(str, getenv("GOOGLE_CLIENT_ID"))
client_secret: str = cast(str, getenv("GOOGLE_CLIENT_SECRET"))
redirect_uri: str = cast(str, getenv("GOOGLE_REDIRECT_URI"))


@pytest.mark.asyncio
async def test_valid_token_acquisition(valid_token_response, op, google) -> None:
    method_to_patch = get_method_to_patch(
        patched_class=Google, method_name=Google._request_access_token.__name__
    )

    with patch(method_to_patch) as mock_token_request:
        mock_response = AsyncMock()
        mock_response.status_code = StatusCode.OK
        mock_response.json = valid_token_response
        mock_token_request.return_value = mock_response
        _result = await google._request_access_token(
            state=op.state,
            code_verifier=op.code_verifier,
            code="...",
        )
        json = _result.json
        status = _result.status_code
        assert json == valid_token_response
        assert status == StatusCode.OK
        token = await google.get_access_token(
            state=op.state,
            code_verifier=op.code_verifier,
            code="...",
        )
        assert token == serialize_access_token(json)


@pytest.mark.asyncio
async def test_invalid_token_acquisition(invalid_token_response, op, google) -> None:
    method_to_patch = get_method_to_patch(
        patched_class=Google, method_name=Google._request_access_token.__name__
    )
    with patch(method_to_patch) as mock_token_request:
        mock_response = AsyncMock()
        mock_response.status_code = StatusCode.OK
        mock_response.json = invalid_token_response
        mock_token_request.return_value = mock_response
        _result = await google._request_access_token(
            state=op.state,
            code_verifier=op.code_verifier,
            code="...",
        )
        json = _result.json
        status = _result.status_code
        assert json == invalid_token_response
        assert status == StatusCode.OK
        AuthConfig.debug = True  # raise in debug
        with pytest.raises(SchemaValidationError):
            _ = await google.get_access_token(
                state=op.state,
                code_verifier=op.code_verifier,
                code="...",
            )
        AuthConfig.debug = False  # hush in normal
        assert (
            await google.get_access_token(
                state=op.state,
                code_verifier=op.code_verifier,
                code="...",
            )
            is None
        )


@pytest.mark.asyncio
async def test_valid_user_info_acquisition(valid_user_data, google) -> None:
    with patch(
        get_method_to_patch(
            patched_class=Google, method_name=Google._request_user_info.__name__
        )
    ) as mock_inf_request:
        mock_response = AsyncMock()
        mock_response.status_code = StatusCode.OK
        mock_response.json = valid_user_data
        mock_inf_request.return_value = mock_response
        _result = await google._request_user_info(access_token="...")
        json = _result.json
        status = _result.status_code
        assert json == valid_user_data
        assert status == StatusCode.OK
        user_info = await google.get_user_info(access_token="...")
        assert user_info == serialize_user_info(json)


@pytest.mark.asyncio
async def test_invalid_user_info_acquisition(invalid_user_data, google) -> None:
    with patch(
        get_method_to_patch(
            patched_class=Google, method_name=Google._request_user_info.__name__
        )
    ) as mock_inf_request:
        mock_response = AsyncMock()
        mock_response.status_code = StatusCode.OK
        mock_response.json = invalid_user_data
        mock_inf_request.return_value = mock_response
        _result = await google._request_user_info(access_token="...")
        json = _result.json
        status = _result.status_code
        assert json == invalid_user_data
        assert status == StatusCode.OK
        AuthConfig.debug = True  # raise in debug
        with pytest.raises(SchemaValidationError):
            _ = await google.get_user_info(access_token="valid_one")
        AuthConfig.debug = False  # hush in  normal
        assert await google.get_user_info(access_token="valid_one") is None


@pytest.mark.asyncio
async def test_invalid_op_normal(op: GrantSecurityParams, google: Google) -> None:
    AuthConfig.debug = False
    assert (
        await google.get_access_token(
            state=op.state, code_verifier=op.code_verifier, code="..."
        )
        is None
    )


@pytest.mark.asyncio
async def test_invalid_op_debug(op: GrantSecurityParams, google: Google) -> None:
    AuthConfig.debug = True
    with pytest.raises(InvalidTokenAcquisitionRequest):
        _ = await google.get_access_token(
            state=op.state, code_verifier=op.code_verifier, code="..."
        )


@pytest.mark.asyncio
async def test_is_unauthorized(google):
    result = await google._request_user_info(access_token="...")
    assert result.status_code == StatusCode.UNAUTHORIZED


@pytest.mark.asyncio
async def test_user_info_invalid_token_debug(google):
    AuthConfig.debug = True
    with pytest.raises(InvalidUserInfoAccessRequest):
        _ = await google.get_user_info(access_token="...")


@pytest.mark.asyncio
async def test_user_info_invalid_token_normal(google):
    AuthConfig.debug = False
    assert await google.get_user_info(access_token="...") is None


def test_serialize_user_info(valid_user_data) -> None:
    valid_data = valid_user_data
    expected_result = {
        "user_id": "123",
        "email": "example@gmail.com",
        "name": "John Doe",
        "avatar": "https://example.com/hosted/pic",
        "extras": {
            "locale": "en",
            "verified_email": True,
            "given_name": "John",
            "family_name": "Doe",
        },
    }
    assert serialize_user_info(valid_data) == expected_result
    # avatar is not presented as a URL then

    with pytest.raises(ValidationError):
        serialize_user_info(
            GoogleUserJSONData(
                email="example@gmail",  # type: ignore   # invalid email
                verified_email=True,
                given_name="John",
                family_name="Doe",
                picture="htps://example.com/hosted/pic",  # type: ignore   # not an actual HTTP(s) URL
                locale="en",
                id="123",
                name="John Doe",
            ).dict()
        )


@pytest.fixture
def google() -> Google:
    return Google(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )


@pytest.fixture
def op() -> GrantSecurityParams:
    return gen_oauth_params()


@pytest.fixture
def valid_user_data() -> Dict[str, Any]:
    return GoogleUserJSONData(
        email="example@gmail.com",  # type: ignore
        verified_email=True,
        given_name="John",
        family_name="Doe",
        picture="https://example.com/hosted/pic",  # type: ignore
        locale="en",
        id="123",
        name="John Doe",
    ).dict()


@pytest.fixture
def invalid_user_data() -> Dict[str, Any]:
    return {
        "id": "123",
        "email": "not@gmail",  #
        "verified_email": True,
        "name": "John Doe",
        "given_name": "John",
        "family_name": "Doe",
        "picture": "htps://lh3.googleusercontent.com/a/abc",  #
        "locale": "en",
    }


@pytest.fixture
def valid_token_response():
    return {
        "access_token": "ya29.--MQ2DXEK727auj8---U4eLDI0g0171",
        "expires_in": 3599,
        "scope": "openid https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
        "token_type": "Bearer",
        "id_token": "...",
    }


@pytest.fixture
def invalid_token_response():
    return {
        "access_token": "",
        "expires_in": "3599",
        "scope": "openid https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
        "token_type": "Bearer",
        "id_token": "...",
    }

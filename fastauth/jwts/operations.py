from jose.jwt import encode as encode_jwt # type: ignore
from jose.jwt import decode as decode_jwt
from jose.jwt import ALGORITHMS
from jose.jwe import encrypt, decrypt # type: ignore
from datetime import datetime, timedelta
from fastauth.data import Cookies
from fastauth.jwts.helpers import check_key_length
from fastauth._types import JWTPayload, UserInfo

JWT_MAX_AGE = Cookies.JWT.max_age
def encipher_user_info(
    user_info: UserInfo, key: str, exp: int = JWT_MAX_AGE
) -> str:
    """
    Encrypts a given user-info payload and returns an encrypted JWT.
    :param user_info: The UserInfo payload
    :param key: The secret key for the entire oauth flow
    :param exp: expiry date of jwt
    :raises: JOSEError
    :return: The encrypted JWT
    """
    check_key_length(key)
    now = datetime.utcnow()
    plain_jwt: str = encode_jwt(
                         claims=JWTPayload(
                             iss="fastauth",
                             sub="client",
                             iat=now,exp=now + timedelta(seconds=exp),
                             user_info=user_info
                         ), key=key[:32], algorithm=ALGORITHMS.HS256)
    encrypted_jwt: str = encrypt(
        plaintext=plain_jwt.encode(),
        key=key,
        algorithm=ALGORITHMS.DIR,
        encryption=ALGORITHMS.A256GCM,
    ).rstrip(b"=").decode()
    return encrypted_jwt

def decipher_jwt(encrypted_jwt: str, key: str) -> JWTPayload:
    """
    Decrypts an encrypted JWT and returns the payload.
    :param encrypted_jwt: The encrypted JWT.
    :param key: The secret key for the entire oauth flow.
    :raises: JOSEError
    :return: JWTPayload
    """
    check_key_length(key)
    decrypted_jwt: str = decrypt(jwe_str=encrypted_jwt, key=key).rstrip(b"=").decode()
    jwt: JWTPayload = decode_jwt(
        token=decrypted_jwt,
        key=key[:32],
        algorithms="HS256",
        issuer="fastauth",
        subject="client",
    )
    return jwt

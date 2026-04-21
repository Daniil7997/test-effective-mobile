import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.pydantic_schemas import AccessTokensPayload


public_key_bytes = bytes.fromhex(settings.PUBLIC_KEY_HEX)

PUBLIC_KEY = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
TOKEN_ALGORITHM = 'EdDSA'


def decode_token(token):
    try:
        token = jwt.decode(algorithms=TOKEN_ALGORITHM,
                           key=PUBLIC_KEY,
                           jwt=token)

    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=[{"loc": ["header", "Authorization"],
                                     "msg": "token expired",
                                     "type": "token-expired"}],
                            headers={"WWW-Authenticate": "Bearer"})

    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=[{"loc": ["header", "Authorization"],
                                     "msg": "invalid token",
                                     "type": "invalid-token"}],
                            headers={"WWW-Authenticate": "Bearer"})

    return AccessTokensPayload(**token)

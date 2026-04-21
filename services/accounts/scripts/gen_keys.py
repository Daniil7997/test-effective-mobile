from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
)

hex_private_key = private_bytes.hex()
hex_publick_key = public_bytes.hex()
print(f"{hex_private_key=}\n{hex_publick_key=}")

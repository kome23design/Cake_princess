import base64
try:
    import ecdsa
except ImportError:
    print("Please install ecdsa first: pip install ecdsa")
    exit(1)

private_key = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
public_key = private_key.get_verifying_key()
priv_der = private_key.to_string()
private_key_b64 = base64.urlsafe_b64encode(priv_der).decode('utf-8').rstrip('=')
pub_der = b'\x04' + public_key.to_string()
public_key_b64 = base64.urlsafe_b64encode(pub_der).decode('utf-8').rstrip('=')

print("\n--- VAPID KEYS FOR YOUR .env FILE ---")
print(f"VAPID_PUBLIC_KEY={public_key_b64}")
print(f"VAPID_PRIVATE_KEY={private_key_b64}")
print("VAPID_ADMIN_EMAIL=mailto:admin@cakeprincess.com")
print("-------------------------------------\n")

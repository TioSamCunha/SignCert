"""
Server-side PKCS#12 parsing and signing using the cryptography library.
The .pfx file is received from the browser over HTTPS, parsed in memory,
the private key signs the PDF hash, and the key is never persisted.
"""
import base64
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, ec


def load_pfx(pfx_bytes: bytes, password: str) -> dict:
    """
    Parse a PKCS#12 file in memory.
    Returns dict with cert_pem, chain_pems, and a callable sign_fn.
    The private key is not returned — only the signing function is exposed.
    """
    pw = password.encode('utf-8') if password else None
    private_key, cert, additional_certs = pkcs12.load_key_and_certificates(pfx_bytes, pw)

    cert_pem = cert.public_bytes(Encoding.PEM).decode()
    chain_pems = [c.public_bytes(Encoding.PEM).decode() for c in (additional_certs or [])]

    def sign_fn(data: bytes) -> bytes:
        return _sign(private_key, data)

    return {'cert_pem': cert_pem, 'chain_pems': chain_pems, 'sign_fn': sign_fn}


def _sign(private_key, data: bytes) -> bytes:
    """Sign data with RSA (PKCS1v15) or EC (ECDSA) key."""
    if hasattr(private_key, 'sign'):
        try:
            # RSA
            return private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
        except TypeError:
            # EC
            return private_key.sign(data, ec.ECDSA(hashes.SHA256()))
    raise ValueError('Tipo de chave não suportado')


def sign_pdf_hash(pdf_bytes: bytes, pfx_bytes: bytes, password: str) -> dict:
    """
    Parse .pfx, sign the SHA-256 hash of the PDF, and return:
      {cert_pem, chain_pems, signature_b64, pdf_hash_hex}
    """
    import hashlib
    pdf_hash = hashlib.sha256(pdf_bytes).digest()

    key_data = load_pfx(pfx_bytes, password)
    sig_bytes = key_data['sign_fn'](pdf_hash)

    return {
        'cert_pem': key_data['cert_pem'],
        'chain_pems': key_data['chain_pems'],
        'signature_b64': base64.b64encode(sig_bytes).decode(),
        'pdf_hash_hex': hashlib.sha256(pdf_bytes).hexdigest(),
    }

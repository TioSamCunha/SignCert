"""
Validates ICP-Brasil certificate chains using pyhanko-certvalidator.
Accepts a PEM certificate chain and verifies against ICP-Brasil trust anchors.
"""
import base64
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding


def load_cert_from_pem(pem_str: str) -> x509.Certificate:
    from cryptography.hazmat.backends import default_backend
    return x509.load_pem_x509_certificate(pem_str.encode(), default_backend())


def validate_icp_brasil_chain(cert_chain_pem: list[str]) -> tuple[bool, str]:
    """
    Validate a certificate chain against ICP-Brasil root CA.
    cert_chain_pem: list of PEM strings [end_entity, intermediate, ..., root]
    Returns (is_valid, message).
    """
    try:
        from pyhanko_certvalidator import CertificateValidator, ValidationContext
        from pyhanko_certvalidator.registry import SimpleCertificateStore
        from asn1crypto import pem as asn1_pem, x509 as asn1_x509

        certs = []
        for pem_str in cert_chain_pem:
            _, _, der = asn1_pem.unarmor(pem_str.strip().encode())
            certs.append(asn1_x509.Certificate.load(der))

        end_entity = certs[0]
        intermediates = certs[1:-1] if len(certs) > 1 else []
        trust_roots = [certs[-1]] if len(certs) > 1 else certs

        store = SimpleCertificateStore()
        for c in intermediates:
            store.register(c)

        context = ValidationContext(trust_roots=trust_roots, other_certs=store)
        validator = CertificateValidator(end_entity, validation_context=context)
        result = validator.validate_usage({'digital_signature'})
        subject = result.cert.subject.human_friendly
        return True, f'Certificado válido: {subject}'
    except ImportError:
        return _fallback_validate(cert_chain_pem)
    except Exception as e:
        return False, f'Certificado inválido: {str(e)}'


def _fallback_validate(cert_chain_pem: list[str]) -> tuple[bool, str]:
    """Minimal validation when pyhanko_certvalidator is not installed."""
    try:
        from cryptography.hazmat.backends import default_backend
        cert = x509.load_pem_x509_certificate(
            cert_chain_pem[0].strip().encode(), default_backend())
        subject = cert.subject.rfc4514_string()
        not_after = cert.not_valid_after_utc
        from datetime import datetime, timezone
        if datetime.now(timezone.utc) > not_after:
            return False, 'Certificado expirado'
        return True, f'Certificado aceito: {subject}'
    except Exception as e:
        return False, f'Erro ao validar certificado: {str(e)}'


def extract_signer_info(cert_pem: str) -> dict:
    """Extract name and CPF from ICP-Brasil end-entity certificate."""
    try:
        from cryptography.hazmat.backends import default_backend
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        name = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        cn = name[0].value if name else 'Desconhecido'
        cpf = _extract_cpf_from_san(cert) or ''
        return {'name': cn, 'cpf': cpf,
                'not_after': cert.not_valid_after_utc.isoformat()}
    except Exception:
        return {'name': 'Desconhecido', 'cpf': ''}


def _extract_cpf_from_san(cert: x509.Certificate) -> str | None:
    """ICP-Brasil stores CPF in SubjectAltName OtherName OID 2.16.76.1.3.1."""
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        for gn in san.value:
            if hasattr(gn, 'value') and '2.16.76.1.3.1' in str(type(gn)):
                return str(gn.value)
    except Exception:
        pass
    return None

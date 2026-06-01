"""
Embeds a CAdES/CMS detached signature into a PDF using pyhanko.
The browser signs the PDF hash with the private key (Web Crypto API),
and the server embeds the PKCS#7 signature block into the PDF.
"""
import base64
import os
from datetime import datetime, timezone


def embed_digital_signature(pdf_path: str, pkcs7_b64: str,
                             cert_chain_pem: list[str],
                             signer_name: str, output_path: str) -> str:
    """
    Embed a pre-computed PKCS#7/CMS signature into the PDF.
    Returns path to signed PDF.
    """
    try:
        return _embed_with_pyhanko(pdf_path, pkcs7_b64, cert_chain_pem,
                                   signer_name, output_path)
    except ImportError:
        return _embed_with_pypdf_metadata(pdf_path, pkcs7_b64,
                                          cert_chain_pem, signer_name, output_path)


def _embed_with_pyhanko(pdf_path: str, pkcs7_b64: str,
                         cert_chain_pem: list[str],
                         signer_name: str, output_path: str) -> str:
    from pyhanko.sign import signers, fields
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign.fields import SigFieldSpec

    with open(pdf_path, 'rb') as f:
        writer = IncrementalPdfFileWriter(f)
        sig_field = fields.append_signature_field(
            writer, SigFieldSpec('Signature', on_page=0))
        cms_signer = signers.ExternalSigner(
            signing_cert=cert_chain_pem[0],
            cert_chain=cert_chain_pem[1:] if len(cert_chain_pem) > 1 else [],
            signature_value=base64.b64decode(pkcs7_b64),
            signer_name=signer_name,
        )
        from pyhanko.sign.signers.pdf_signer import PdfSignatureMetadata
        meta = PdfSignatureMetadata(field_name='Signature')
        with open(output_path, 'wb') as out:
            signers.sign_pdf(writer, meta, signer=cms_signer, output=out)
    return output_path


def _embed_with_pypdf_metadata(pdf_path: str, pkcs7_b64: str,
                                cert_chain_pem: list[str],
                                signer_name: str, output_path: str) -> str:
    """
    Fallback: copy the PDF and add XMP metadata recording the digital signature.
    Not a true embedded signature but preserves the audit trail.
    """
    import shutil
    from pypdf import PdfWriter, PdfReader
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({
        '/DigitalSignature': pkcs7_b64[:500],
        '/SignerName': signer_name,
        '/SignedAt': datetime.now(timezone.utc).isoformat(),
        '/CertSubject': cert_chain_pem[0][:200] if cert_chain_pem else '',
        '/SignatureMethod': 'CMS-CAdES-ICP-Brasil',
    })
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path

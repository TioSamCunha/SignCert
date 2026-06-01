from datetime import datetime, timezone
from flask import Blueprint, render_template, abort
from app.models.signature_request import SignatureRequest
from app.models.document import Document
from app.services.signature.token_service import decode_signing_jwt
from app.services.geo_service import get_geolocation
from app.extensions import db
import app.services.audit_service as audit
from flask import request

bp = Blueprint('signing_view', __name__, url_prefix='/sign')


def _get_sig_req_from_token(token: str):
    payload = decode_signing_jwt(token)
    if not payload:
        return None, None
    sig_req = SignatureRequest.query.get(payload.get('sig_req_id'))
    if not sig_req or sig_req.token != token:
        return None, None
    return sig_req, payload


@bp.route('/<token>')
def sign(token):
    sig_req, payload = _get_sig_req_from_token(token)
    if not sig_req:
        return render_template('signing/expired.html'), 410

    doc = Document.query.get(payload['document_id'])

    if sig_req.status in ('signed', 'cancelled'):
        return render_template('signing/already_done.html', sig_req=sig_req)

    if sig_req.status == 'expired':
        return render_template('signing/expired.html'), 410

    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    ua = request.user_agent.string
    geo = get_geolocation(ip)

    if sig_req.status == 'pending':
        sig_req.status = 'link_opened'
        sig_req.link_opened_at = datetime.now(timezone.utc)
        sig_req.ip_address = ip
        sig_req.user_agent = ua
        if geo:
            sig_req.geolocation_country = geo.get('country')
            sig_req.geolocation_region = geo.get('region')
            sig_req.geolocation_city = geo.get('city')
            sig_req.geolocation_lat = geo.get('lat')
            sig_req.geolocation_lon = geo.get('lon')
        db.session.commit()
        audit.log('SIGNING_LINK_OPENED', document_id=doc.id,
                  signature_request_id=sig_req.id,
                  actor_email=sig_req.signatory_email,
                  ip=ip, user_agent=ua, geo=geo)

    return render_template('signing/view.html', sig_req=sig_req, doc=doc, token=token)

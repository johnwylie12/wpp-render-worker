"""wpp_partner.py — ONE mapping from a wpp_signoff() row to what each engine needs.

Every printed piece asks the same question — whose name goes on this — and each
engine had its own answer hardcoded to John Wylie:

    cover/WPP_EOP_CoverLetter_TEMPLATE      name, title, email, phone (x2 blocks)
    note_card/note_card_engine.py           DEFAULT_SIGNOFF name
    portal_sticker/portal_sticker.py        C_NAME/C_TITLE/C_PHONE/C_EMAIL + BOOK_URL
    meeting_label/meeting_label.py          C_NAME/C_TITLE/C_PHONE/C_EMAIL + BOOK_URL

With one operator that was invisible. With two it silently mails 24 letters under
the wrong name, and the booking QR puts another partner's prospects on John's
calendar. This module is the single place that turns a signoff row into engine
fields, so a third partner is a database row and not four more edits.

FAIL CLOSED. Nothing here substitutes a default for a missing partner. A piece
that cannot say who it is from does not print.
"""
from wpp_signatures import signature_for_partner, signature_width_px, UnknownSignature  # noqa: F401

REQUIRED = ("signoff_name", "signoff_title", "signoff_firm", "signoff_email", "signoff_phone")


class PartnerError(Exception):
    """The sender could not be resolved. Never downgraded to a default."""


def normalize(signoff, *, need_signature=True, need_booking=False):
    """Validate a wpp_signoff() row -> a dict every engine can read.

    need_signature  the piece prints a signature mark (cover letter, note card)
    need_booking    the piece prints a book-a-meeting QR. There is no booking_url
                    on partner_signature yet, so this refuses for any partner
                    who has not got one rather than falling back to John's link.
    """
    if not signoff:
        raise PartnerError("no partner signoff resolved; refusing to print an unattributed piece")
    s = dict(signoff)

    if s.get("is_renderable") is False:
        raise PartnerError(f"partner is not renderable; missing {s.get('missing') or 'unknown'}")
    missing = [f for f in REQUIRED if not str(s.get(f) or "").strip()]
    if missing:
        raise PartnerError(f"partner signoff is missing {', '.join(missing)}")

    out = {
        "partner_id": s.get("partner_id"),
        "name": s["signoff_name"].strip(),
        "title": s["signoff_title"].strip(),
        "firm": s["signoff_firm"].strip(),
        "email": s["signoff_email"].strip(),
        "phone": s["signoff_phone"].strip(),
        "tagline": (s.get("tagline") or "Value Through Insight").strip(),
        # "Senior Consultant, ERA Group" — the one-line form the labels print.
        "title_line": f"{s['signoff_title'].strip()}, {s['signoff_firm'].strip()}",
    }

    if need_signature:
        key = signature_for_partner(s.get("partner_id"), s.get("signature_key"))   # raises; never borrows
        out["signature_key"] = key
        out["signature_width_px"] = signature_width_px(key)

    if need_booking:
        url = str(s.get("booking_url") or "").strip()
        if not url:
            raise PartnerError(
                f"partner {s.get('partner_id')} ({out['name']}) has no booking_url; refusing to "
                f"print a book-a-meeting QR that would point at someone else's calendar")
        out["booking_url"] = url

    return out

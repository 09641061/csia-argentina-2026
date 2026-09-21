from __future__ import annotations

from app.shared.domain.text_masking import mask_free_text


def mask_outbound_payload(value: object) -> object:
    """
    Mask every string that is about to leave towards the security model.

    Sensitive material is not limited to JSON values: a key, a JSONPath, a
    filename or an error message can carry an email, a token or an identifier.
    Applying the free-text masker to the whole payload right before it is
    serialized means no branch of the prompt builder can forget one.
    """

    if isinstance(value, str):
        return mask_free_text(value)
    if isinstance(value, dict):
        return {mask_free_text(str(key)): mask_outbound_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [mask_outbound_payload(item) for item in value]
    return value

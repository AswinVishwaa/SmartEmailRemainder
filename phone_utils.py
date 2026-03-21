import re


def normalize_phone_number(raw_phone):
    """
    Convert phone values like 'whatsapp:+91 93606-15435' into canonical digits only.
    """
    if raw_phone is None:
        return ""

    phone = str(raw_phone).strip().lower()
    phone = phone.replace("whatsapp:", "")
    return re.sub(r"\D", "", phone)

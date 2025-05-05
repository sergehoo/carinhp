import base64
from io import BytesIO

import qrcode
from django import template

register = template.Library()


@register.filter(name='sum_dict_values')
def sum_dict_values(values):
    try:
        return sum(values)
    except TypeError:
        return 0


@register.filter
def get_item(dictionary, key):
    if not dictionary or not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0)


@register.filter
def dict_get(d, key):
    return d.get(key)


@register.filter
def qr_code_image(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(data))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

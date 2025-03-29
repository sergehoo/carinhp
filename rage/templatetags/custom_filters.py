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

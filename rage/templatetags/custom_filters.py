from django import template

register = template.Library()


@register.filter
def sum_dict_values(dictionary):
    return sum(dictionary.values())

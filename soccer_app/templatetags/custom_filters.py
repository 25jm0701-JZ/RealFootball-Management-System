"""自定义模板过滤器。"""
import builtins

from django import template

register = template.Library()


@register.filter
def field_value(obj, name):
    """在模板中安全读取对象属性或字典键：{{ obj|field_value:'field' }}。"""
    if isinstance(obj, dict):
        return obj.get(name, '')
    return builtins.getattr(obj, name, '')

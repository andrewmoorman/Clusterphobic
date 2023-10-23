'''
Module docstring
'''
from jinja2 import Environment, PackageLoader, select_autoescape

template_env = Environment(
    loader=PackageLoader("clusterphobic"),
    autoescape=select_autoescape()
)

def get_template(filename):
    '''
    Helper function wrapping Jinja2 'get_template' for this environment
    '''
    return template_env.get_template(filename)

import ast
 
from django import template
 
register = template.Library()
 
 
class StripNode(template.Node):
    """
    Strips leading and trailing characters in the enclosed content.
 
    Examples::
 
        {% strip "/ " %}  /products/lord-of-the-rings-part-1/ {% endstrip %}
        {% strip %}
        leading and trailing white-space   {% endstrip %}
 
    is output as::
 
        products/lord-of-the-rings-part-1
        leading and trailing white-space
    """
    def __init__(self, parser, token):
        options = token.split_contents()
        if len(options) > 1:
            try:
                self.strip_chars = ast.literal_eval(options[1])
            except SyntaxError:
                raise SyntaxError(
                    'Argument to strip tag ("{0}") is not a valid python string literal'.format(options[1])
                )
        else:
            self.strip_chars = None
        self.nodelist = parser.parse(('endstrip',))
        parser.delete_first_token()
 
    def render(self, context):
        content = self.nodelist.render(context).strip()
        if self.strip_chars:
            return content.strip(self.strip_chars)
        return content.strip()
 
 
register.tag('strip', StripNode)
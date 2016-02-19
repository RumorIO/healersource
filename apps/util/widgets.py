from django.conf import settings
from django.forms.util import flatatt
from django.forms.widgets import Widget
from django.template.defaultfilters import escapejs
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


class TinyEditor(Widget):
	def __init__(self, *args, **kwargs):
		no_width = kwargs.pop('no_width', False)
		if no_width:
			self.width = '100%'
		else:
			self.width = '700'
		super(TinyEditor, self).__init__(*args, **kwargs)

	def render(self, name, value, attrs=None):
		if value is None:
			value = ''
		final_attrs = self.build_attrs(attrs, name=name)
		textarea = u'<textarea%s>%s</textarea>' % (flatatt(final_attrs), conditional_escape(force_unicode(value)))
		js = """
			<script type='text/javascript'>
				var settings = {
					id:'%s',
					height:260,
					width: '%s',
					content: '%s',
					cssclass:'te',
					controlclass:'tecontrol',
					rowclass:'teheader',
					dividerclass:'tedivider',
					controls:['bold','italic','underline','|',
						'orderedlist','unorderedlist','|',
						'outdent','indent','|',
						'image','hr','link','unlink','|',
						'unformat',
						'n',
						'undo','redo','|',
						'cut','copy','paste'],
					footer:true,
					fonts:['Verdana','Arial','Georgia','Trebuchet MS'],
					xhtml:true,
					bodyid:'editor',
					footerclass:'tefooter',
					toggle:{text:'source',activetext:'wysiwyg',cssclass:'toggle'},
					resize:{cssclass:'resize'}
				}

				$(document).ready(function() {
					if(window['first'] == undefined || first==true){
						var editor = new TINY.editor.edit('editor', settings);
						var form = $('#%s').closest('form');
						if(form.length) {
							form.bind('submit', function() {editor.post()});
						}
					}
					first=false;
				});
			</script>
			"""
		js %= (attrs['id'], self.width, escapejs(force_unicode(value)), attrs['id'])
		return mark_safe(textarea + js)

	class Media:
		js = [settings.STATIC_URL + "tinyeditor/tinyeditor.js"]
		css = {'all': [settings.STATIC_URL + "tinyeditor/style.css"]}

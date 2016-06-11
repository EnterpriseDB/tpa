from django import forms
from django.template.loader import render_to_string
from django.forms.fields import EMPTY_VALUES
from django.utils.translation import ugettext as _
from django.utils.html import mark_safe

class RangeWidget(forms.MultiWidget):
    def __init__(self, widget, *args, **kwargs):
        widgets = (widget, widget)

        super(RangeWidget, self).__init__(widgets=widgets, *args, **kwargs)

    def decompress(self, value):
        return value

    def format_output(self, rendered_widgets):
        widget_context = {'min': rendered_widgets[0], 'max': rendered_widgets[1],}
        return render_to_string('widgets/range_widget.html', widget_context)

class RangeField(forms.MultiValueField):
    default_error_messages = {
        'invalid_start': _(u'Enter a valid start value.'),
        'invalid_end': _(u'Enter a valid end value.'),
    }

    def __init__(self, field_class, widget=forms.TextInput, *args, **kwargs):
        if not 'initial' in kwargs:
            kwargs['initial'] = ['','']

        fields = (field_class(), field_class())

        super(RangeField, self).__init__(
                fields=fields,
                widget=RangeWidget(widget),
                *args, **kwargs
                )

    def compress(self, data_list):
        if data_list:
            return [self.fields[0].clean(data_list[0]),self.fields[1].clean(data_list[1])]

        return None
    
class SingleRadioInput(forms.widgets.Input):

    input_type = 'radio'
    def render(self, value, checked, attrs=None):
        output = []
        if value:
            is_cover = ''
            if checked : is_cover = 'checked'
            output.append(
                ('<input type="radio" name="inline" value="%s" %s/>') 
                % (value, is_cover)
            )

        return mark_safe(u''.join(output))
    
    
    
class MaintenanceHoursWidget(forms.HiddenInput):
    class Media:
            js = (
                  'https://ajax.googleapis.com/ajax/libs/jquery/1.12.2/jquery.min.js',
                  'js/rangeslider.js',
                  )
            css = {'all': (
                           'https://ajax.googleapis.com/ajax/libs/jquery/1.12.2/jquery-ui.custom.css',
                           'css/custom.css',
            )}
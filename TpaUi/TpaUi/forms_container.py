from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms import models
from django.forms.formsets import BaseFormSet
from django.utils.datastructures import MultiValueDict
from collections import OrderedDict
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe


class FormContainerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        form_classes = OrderedDict(
            (prefix, attrs.pop(prefix))
            for prefix, form_class in attrs.items()
            if isinstance(form_class, type) and issubclass(form_class, (forms.BaseForm, BaseFormSet))
        )

        new_class = super(FormContainerMetaclass, cls).__new__(cls, name, bases, attrs)

        new_class.form_classes = form_classes

        # Making the form container look like a form, for the
        # sake of the FormWizard.
        new_class.base_fields = {}
        for prefix, form_class in new_class.form_classes.items():
            if issubclass(form_class, BaseFormSet):
                new_class.base_fields.update(form_class.form.base_fields)
            else:
                new_class.base_fields.update(form_class.base_fields)

        return new_class

@python_2_unicode_compatible
class StrAndUnicode(object):
    def __str__(self):
        return self.CodeType

class FormContainer(StrAndUnicode):
    __metaclass__ = FormContainerMetaclass

    def __init__(self, **kwargs):
        self._errors = {}
        self.forms = OrderedDict()
        container_prefix = kwargs.pop('prefix', '')

        # Instantiate all the forms in the container
        for form_prefix, form_class in self.form_classes.items():
            self.forms[form_prefix] = form_class(
                prefix='-'.join(p for p in [container_prefix, form_prefix] if p),
                **self.get_form_kwargs(form_prefix, **kwargs)
            )

    def get_form_kwargs(self, prefix, **kwargs):
        """Return per-form kwargs for instantiating a specific form

        By default, just returns the kwargs provided. prefix is the
        label for the form in the container, allowing you to specify
        extra (or less) kwargs for each form in the container.
        """
        return kwargs

    def __unicode__(self):
        "Render all the forms in the container"
        return mark_safe(u''.join([f.as_table() for f in self.forms.values()]))

    def __iter__(self):
        "Return each of the forms in the container"
        for prefix in self.forms:
            yield self[prefix]

    def __getitem__(self, prefix):
        "Return a specific form in the container"
        try:
            form = self.forms[prefix]
        except KeyError:
            raise KeyError('Prefix %r not found in Form container' % prefix)
        return form

    def is_valid(self):
        return all(f.is_valid() for f in self.forms.values())

    @property
    def data(self):
        "Return a compressed dictionary of all data from all subforms"
        all_data = MultiValueDict()
        for prefix, form in self.forms.items():
            for key in form.data:
                all_data.setlist(key, form.data.getlist(key))
        return all_data

    @property
    def files(self):
        "Return a compressed dictionary of all files from all subforms"
        all_files = MultiValueDict()
        for prefix, form in self.forms.items():
            for key in form.files:
                all_files.setlist(key, form.files.getlist(key))
        return all_files

    @property
    def errors(self):
        "Return a compressed dictionary of all errors form all subforms"
        return dict((prefix, form.errors) for prefix, form in self.forms.items())

    def save(self, *args, **kwargs):
        "Save each of the subforms"
        return [f.save(*args, **kwargs) for f in self.forms.values()]

    def save_m2m(self):
        """Save any related objects -- e.g., m2m entries or inline formsets

        This is needed if the original form collection was saved with commit=False
        """
        for prefix, form in self.forms.items():
            try:
                for subform in form.saved_forms:
                    # Because the related instance wasn't saved at the time the
                    # form was created, the new PK value hasn't propegated to
                    # the inline object on the formset. We need to re-set the
                    # instance to update the _id attribute, which will allow the
                    # inline form instance to save.
                    setattr(subform.instance, form.fk.name, form.instance)
                    subform.instance.save()
            except AttributeError:
                pass

            try:
                form.save_m2m()
            except AttributeError:
                pass


# And now, an example of usage:
# Assuming you have a UserDetailsForm, and an AddressesFormSet...
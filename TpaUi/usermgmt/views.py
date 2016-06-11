from django.shortcuts import render_to_response
from django.template.context import RequestContext
from formtools.wizard.views import SessionWizardView
from django.conf import settings
from random import choice
from string import ascii_uppercase
import logging, json, uuid
from TpaUi import forms

logr = logging.getLogger(__name__)

# Create your views here.

def first_view(req):
    return render_to_response('index.html', locals(), context_instance = RequestContext(req))
STEP1 ="step1"
STEP2= "step2"

FORMS = [(STEP1, forms.ProvisionFormPage1),
         (STEP2, forms.InstancesFormSet),
         ("step3", forms.ProvisionFormPage3),
         ("step4", forms.ProvisionFormPage4),
         ]

TEMPLATES = {STEP1: "provision.html",
             STEP2: "provision.html",
             "step3": "provision.html",
             "step4": "provision.html"
             }

def assert_configure_ha(wizard):
    # Return true if user checks High Availability in step1
    cleaned_data = wizard.get_cleaned_data_for_step('step1') or {'HighAvailability': False}
    return cleaned_data['HighAvailability'] == True

class ProvisioningWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]
    
    def get_form_initial(self, step):
        
        if step == STEP2:
            form_class = self.form_list[step]
            data = self.get_cleaned_data_for_step(STEP1)
            
            #print data
            if data is not None:
                extra = int(data['InstanceCount'])
                form_class.extra = extra
            
        return SessionWizardView.get_form_initial(self, step)
    
    def done(self, form_list, **kwargs):
        form_data = process_form_data(form_list)
        temp = {"Instances": form_data[1], "Maintenance":form_data[2], "IAM":form_data[3]}
        temp2 = form_data[0]
        temp2['Properties'] = temp
        resourceId = uuid.uuid4().urn[9:]
        temp2['ResourceId'] = resourceId
        customerId=''.join(choice(ascii_uppercase) for i in range(4))
        temp2['CustomerId'] = customerId
        out_json = json.dumps(temp2, indent=4, sort_keys=False)
        #handler = open(settings.BASE_DIR + '/json/out_'+customerId+'_'+resourceId+'.json','r+')
        handler = open(settings.BASE_DIR + '/json/out.json','r+')
        handler.write(out_json)
        handler.close();
        return render_to_response('success.html', {'form_data':form_data})

def process_form_data(form_list):
    form_data = [form.cleaned_data for form in form_list]
    return form_data
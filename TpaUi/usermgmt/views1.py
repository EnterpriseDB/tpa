from django.shortcuts import render_to_response
from django.template.context import RequestContext
from formtools.wizard.views import SessionWizardView
from django.conf import settings
from random import choice
from string import ascii_uppercase
import logging, json, uuid
from _codecs import decode

logr = logging.getLogger(__name__)

# Create your views here.

def first_view(req):
    return render_to_response('index.html', locals(), context_instance = RequestContext(req))

class ProvisioningWizard(SessionWizardView):
    template_name = 'provision.html'
    def done(self, form_list, **kwargs):
        form_data = process_form_data(form_list)
        print form_data
        temp = {"Instance": form_data[1], "Database":form_data[2], "Others":form_data[3]}
        temp2 = form_data[0]
        temp2['Properties'] = temp
        resourceId = uuid.uuid4().urn[9:]
        temp2['ResourceId'] = resourceId
        customerId=''.join(choice(ascii_uppercase) for i in range(4))
        temp2['CustomerId'] = customerId
        out_json = json.dumps(temp2, indent=4, sort_keys=False)
        handler = open(settings.BASE_DIR + '/json/out.json','r+')
        handler.write(out_json)
        handler.close();
        return render_to_response('success.html', {'form_data':form_data})
    
class HaPopup():
    print "HA"

        
def process_form_data(form_list):
    form_data = [form.cleaned_data for form in form_list]
    return form_data
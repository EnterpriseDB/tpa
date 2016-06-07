"""TpaUi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
#import usermgmt
#from usermgmt import views
from usermgmt.views import ProvisioningWizard, FORMS
from TpaUi.forms import ProvisionFormPage1, ProvisionFormPage3, ProvisionFormPage4
from django.conf.urls.static import static
from django.conf import settings
#import TpaUi

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', 'usermgmt.views.first_view'),
    #url(r'^provision/', ProvisioningWizard.as_view([ProvisionFormPage1, TpaUi.forms.InstancesFormSet, 
     #                                               ProvisionFormPage3, ProvisionFormPage4])),
     url(r'^provision/$', ProvisioningWizard.as_view(FORMS)),
     url(r'^provision1/$', ProvisioningWizard.as_view(FORMS)),
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

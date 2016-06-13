from django import forms
import settings
import json
from django.forms.formsets import formset_factory, BaseFormSet
from models import MaintenanceHours
from customwidgets import MaintenanceHoursWidget
from django.core.exceptions import ValidationError

jsonIn = open(settings.BASE_DIR + '/json/in.json','r')
data1 =  json.load(jsonIn)
jsonIn.close()

properties = data1['Properties']

class FormWithDescription (forms.Form):
    def __init__ (self, title, desc):
        self.title = title
        self.desc = desc
        super (FormWithDescription, self).__init__ () # call base class

class ProvisionFormPage1(forms.Form):
    #desc = forms.CharField(initial='Cluster Basics', widget = forms.HiddenInput, label ='')
    
    ENGINE1="postgresql_9_4"
    ENGINE2="postgresql_9_5"
    ENGINE3="postgresql_9_6"
    ENGINE4="2q_postgresql_9_4"
    ENGINE5="2q_postgresql_9_5"
    ENGINE6="2q_postgresql_9_6"
    ENGINE7="postgresxl_9_5"
    ENGINE8="2q_postgresxl_9_5"
    ENGINE9="2q_bdr_9_4"
    ENGINE_CHOICES = (
                      (ENGINE1, "PostgreSQL 9.4"),
                      (ENGINE2, "PostgreSQL 9.5"),
                      (ENGINE3, "PostgreSQL 9.6"),
                      (ENGINE4, "2ndQuadrant PostgreSQL 9.4"),
                      (ENGINE5, "2ndQuadrant PostgreSQL 9.5"),
                      (ENGINE6, "2ndQuadrant PostgreSQL 9.6"),
                      (ENGINE7, "Postgres-XL 9.5"),
                      (ENGINE8, "2ndQuadrant Postgres-XL 9.5"),
                      (ENGINE9, "2ndQuadrant BDR 9.5")
    )

    ClusterType = forms.ChoiceField(choices=ENGINE_CHOICES, label='Cluster Type', initial= data1['ClusterType'], widget=forms.Select(attrs={'class':'form-control'}))
    ClusterName = forms.CharField(max_length=16, initial = data1['ClusterName'], label='Cluster Name', widget=forms.TextInput(attrs={'class':'form-control'}))
    
    ClusterTags = forms.CharField(max_length=256, initial = json.dumps(data1['ClusterTags']), label='Cluster Tags',  widget= forms.Textarea(attrs={'rows':6,'cols':20, 'class':'form-control'}))
    InstanceCount = forms.IntegerField(max_value=999, initial = data1['InstanceCount'],label = "Number of Instances (>1 for HA)", widget=forms.NumberInput(attrs={'class':'form-control'}) )

    def clean(self):
        if 'ClusterTags' in self.cleaned_data.keys():
                self.cleaned_data['ClusterTags'] = json.loads(self.cleaned_data['ClusterTags'])
        return self.cleaned_data
    

class InstanceForm(forms.Form):
    data = properties['Instances'][0]
    TYPE_CHOICES = (("t1_micro","t1.micro"),
                    ("m1_small","m1.small")
                    )# | db.m1.medium | db.m1.large | db.m1.xlarge | db.m2.xlarge |db.m2.2xlarge | db.m2.4xlarge | db.m3.medium | db.m3.large | db.m3.xlarge | db.m3.2xlarge | db.m4.large | db.m4.xlarge | db.m4.2xlarge | db.m4.4xlarge | db.m4.10xlarge | db.r3.large | db.r3.xlarge | db.r3.2xlarge | db.r3.4xlarge | db.r3.8xlarge | db.t2.micro | db.t2.small | db.t2.medium | db.t2.large)
    
    Name = forms.CharField(max_length = 16, label = "Name", initial= data['Name'],widget=forms.TextInput(attrs={'class':'form-control'}))
    Type = forms.ChoiceField(choices = TYPE_CHOICES, label = "Instance Type", initial= data['Type'], widget=forms.Select(attrs={'class':'form-control'}))
    REGION_CHOICES = (("us_east_1","us-east-1"),
                      ("us_west_1","us-west-1"),
                      ("us_west_2","us-west-2"))
    
    Region = forms.ChoiceField(choices = REGION_CHOICES, label = "Availability Zone", initial= data['Region'], widget=forms.Select(attrs={'class':'form-control'}))

    Subnet = forms.CharField(max_length = 16, label ="Subnet", initial= data['Subnet'],widget=forms.TextInput(attrs={'class':'form-control'}) )
    Tags= forms.CharField(max_length = 256, label ="Instance Tags (Use JSON KVP)", initial= json.dumps(data['Tags']),widget=forms.TextInput(attrs={'class':'form-control'}))
    
    Primary = forms.BooleanField(label = "Make this instance primary" , initial = data['Primary'], required = False, widget=forms.CheckboxInput(attrs={'class':'checkbox'}))

    def has_changed(self):
        changed_data = super(forms.Form, self).has_changed()
        print "Changed "+str(changed_data)
        print bool(self.initial or changed_data)
        if self.initial:
            return True
        elif changed_data:
            return True
        else:
            return True


    ''' The ongoing radiobutton implementation of Primary, which did not work as expected
    RADIO_CHOICES = ((0, False),
                    (1, True))

    ###Primary = forms.BooleanField(required = False,  widget = forms.RadioSelect(attrs={'class':'form-control'},choices = RADIO_CHOICES,))
    
    def __init__ (self, *args, **kwargs):
        super(InstanceForm, self).__init__(*args, **kwargs)
        CHOICES = ((self.prefix, ''),)
        self.fields['Primary'] = forms.BooleanField(label = "Make this instance primary",required = False, widget = forms.RadioSelect(attrs={'class':'radio'}, choices = CHOICES))

    def add_prefix(self, field):
        if field == 'Primary':
            ret = ('%s_%s') %(field, self.data)
            print 'Primary filed data:: ' + field
            print ret
            print '~~~~~~~~~~~~~~~~~~~~~~'
            return ret
        else:
            ret = self.prefix and ('%s-%s' % (self.prefix, field)) or field
            print 'Non primary data:: ' + field
            print ret
            print '~~~~~~~~~~~~~~~~~~~~~~'
            return ret'''

class CustomFormSet(BaseFormSet):
    def clean(self):
        count = 0
        for form in self.forms:
            if 'Tags' in form.cleaned_data.keys():
                form.cleaned_data['Tags'] = json.loads(form.cleaned_data['Tags'])

            if 'Primary' in form.cleaned_data.keys():
                if form.cleaned_data['Primary'] == True:
                    count += 1
                    if count > 1:
                        raise ValidationError("Please mark only one instance as primary.")

        if count < 1:
            raise ValidationError("Please choose a primary instance.")

        #return self.cleaned_data

instances = properties['Instances']
InstancesFormSet = formset_factory(InstanceForm, CustomFormSet, extra = len(instances))

class ProvisionFormPage3(forms.Form):
    HOURS = ((1,"01:00"),(2,"02:00"),(3,"03:00"),(4,"04:00"))
    data = properties['Maintenance']
    AutoMinorVersionUpgrade = forms.BooleanField(initial=json.dumps(data['AutoMinorVersionUpgrade']), label='Auto Minor Version Upgrade', widget=forms.CheckboxInput(attrs={'class':'checkbox'}))
    BackupRetentionPeriod = forms.CharField(max_length=8, initial=data['BackupRetentionPeriod'], label='Backup Retention Period', widget=forms.TextInput(attrs={'class':'form-control'}))
    BackupFrequency = forms.CharField(max_length=8, initial=data['BackupFrequency'], label='Backup Frequency', widget=forms.TextInput(attrs={'class':'form-control'}))
    PreferredBackupWindow = forms.MultipleChoiceField(choices= HOURS, initial=data['PreferredBackupWindow'], label='Preferred Backup Window', widget=forms.SelectMultiple(attrs={'class':'form-control'}))
    PreferredMaintenanceWindow = forms.MultipleChoiceField(choices= HOURS, initial=data['PreferredMaintenanceWindow'], label='Preferred Maintenance Window', widget=forms.SelectMultiple(attrs={'class':'form-control'}))

    def clean(self):
        backupWindow = self.cleaned_data['PreferredBackupWindow']
        if(len(backupWindow) != 2):
            raise ValidationError("Please select two items as start time and end time from backup window listbox.")

        maintainenceWindow = self.cleaned_data['PreferredMaintenanceWindow']
        if(len(maintainenceWindow) != 2):
            raise ValidationError("Please select two items as start time and end time from maintenance window listbox.")
        return self.cleaned_data

    ''' These lines are for including extra fields from input JSON, something to be considered for July release
    def __init__(self, *args, **kwargs):
        data = properties['Maintenance']
        print 'Before delete'
        print data
        if 'AllowMajorVersionUpgrade' in data:
            del data['AllowMajorVersionUpgrade']
        if 'AutoMinorVersionUpgrade' in data:
            del data['AutoMinorVersionUpgrade']
        if 'BackupRetentionPeriod' in data:
            del data['BackupRetentionPeriod']
        if 'BackupFrequency' in data:
            del data['BackupFrequency']
        if 'PreferredBackupWindow' in data:
            del data['PreferredBackupWindow']
        if 'PreferredMaintenanceWindow' in data:
            del data['PreferredMaintenanceWindow']
        extra = data
        super(ProvisionFormPage3, self).__init__(*args, **kwargs)
        print extra

        for i, key in enumerate(extra):
            name,type = key.split('_')
            if (type == 'bool' ):
                self.fields[key] = forms.BooleanField(label=name, initial=data[key], required = False, widget=forms.CheckboxInput(attrs={'class':'checkbox'}))
            elif type == 'int':
                self.fields[key] = forms.IntegerField(label=name, initial=data[key], widget=forms.NumberInput(attrs={'class':'form-control'}))
            elif type == 'select':
                print 'XX Selecy '
                print data[key]
                CHOICES = []
                for choice in data[key]:
                    CHOICES.append((str(choice), choice))

                self.fields[key] = forms.ChoiceField(label=name,required = False, widget=forms.Select(attrs={'class':'form-control'}))

            else:
                self.fields[key] = forms.CharField(label=name, initial=data[key], widget=forms.TextInput(attrs={'class':'form-control'}))
             '''   

class ProvisionFormPage4(forms.Form):
    data = properties['IAM']
    AwsKeyId = forms.CharField(max_length=16, initial=data['AwsKeyId'], label='AwsKeyId', widget=forms.TextInput(attrs={'class':'form-control'}))
    AwsSecret = forms.CharField(max_length=32, initial=data['AwsSecret'], label='AwsSecret', widget=forms.PasswordInput(attrs={'class':'form-control'})  )
    
class ProvisionFormPage5(forms.ModelForm):
    class Meta:
        model = MaintenanceHours
        fields = ('weekday', 'from_hour', 'to_hour')
        widgets = {
            'weekday': forms.HiddenInput(attrs={'class': 'hours-weekday'}),
            'from_hour': MaintenanceHoursWidget(attrs={'class': 'hours-start'}),
            'to_hour': forms.HiddenInput(attrs={'class': 'hours-end'}),
        }
        
        
BackupFormSet = formset_factory(ProvisionFormPage5, extra=0)


    
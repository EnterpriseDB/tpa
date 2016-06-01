from django import forms
import settings
import json
from django.forms.formsets import formset_factory

jsonIn = open(settings.BASE_DIR + '/json/in.json','r')
#data1= jsonIn.readlines()
data1 =  json.load(jsonIn)
#data2 = json.dumps(jsonIn)
for x in data1:
    print x


jsonIn.close()


print data1
properties = data1['Properties']

class FormWithDescription (forms.Form):
    def __init__ (self, title, desc):
        self.title = title
        self.desc = desc
        super (FormWithDescription, self).__init__ () # call base class

class ProvisionFormPage1(forms.Form):
    #desc = forms.CharField(initial='Cluster Basics', widget = forms.HiddenInput, label ='')
    
    ENGINE1="postgresql_9_5"
    ENGINE2="postgresql_9_4"
    ENGINE3="postgresql_9_3"
    ENGINE4="postgresxl_9_2"
    ENGINE5="postgresxc_9_3"
    ENGINE_CHOICES = (
                      (ENGINE1, "PostgreSQL 9.5"),
                      (ENGINE2, "PostgreSQL 9.4"),
                      (ENGINE3, "PostgreSQL 9.3"),
                      (ENGINE1, "Postgres-XL 9.2"),
                      (ENGINE1, "Postgres-XC 9.3"),
    )

    ClusterType = forms.ChoiceField(choices=ENGINE_CHOICES, label='Cluster Type', initial= data1['ClusterType'], widget=forms.Select(attrs={'class':'form-control'}))
    ClusterName = forms.CharField(max_length=16, initial = data1['ClusterName'], label='Cluster Name', widget=forms.TextInput(attrs={'class':'form-control'}))
    
    ClusterTags = forms.CharField(max_length=256, initial = json.dumps(data1['ClusterTags']), label='Cluster Tags',  widget= forms.Textarea(attrs={'rows':6,'cols':20, 'class':'form-control'}))
    InstanceCount = forms.IntegerField(max_value=999, initial = data1['InstanceCount'],label = "Number of Instances (>1 for HA)", widget=forms.NumberInput(attrs={'class':'form-control'}) )
    #InstanceCount = forms.BooleanField(initial=data1['HighAvailability'], label="High Availability")
    

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
    
    Image = forms.CharField(max_length = 16, label = "AMI", initial= data['Image'], widget=forms.TextInput(attrs={'class':'form-control'}))
    Subnet = forms.CharField(max_length = 16, label ="Subnet", initial= data['Subnet'],widget=forms.TextInput(attrs={'class':'form-control'}) )
    AllocatedStorage = forms.IntegerField(max_value=999, label='Allocated Storage (in GB)', initial= data['AllocatedStorage'],widget=forms.NumberInput(attrs={'class':'form-control'}))
    Tags= forms.CharField(max_length = 256, label ="Instance Tags (Use JSON KVP)", initial= json.dumps(data['Tags']),widget=forms.TextInput(attrs={'class':'form-control'}))
    
    

InstancesFormSet = formset_factory(InstanceForm, extra = 2)
        
class ProvisionFormPage3(forms.Form):
    HOURS = ((1,"01:00"),(2,"02:00"),(3,"03:00"),(4,"04:00"))
    data = properties['Maintenance']
    AllowMajorVersionUpgrade = forms.BooleanField(initial=data['AllowMajorVersionUpgrade'], label='Allow Major Version Upgrade', required = False, widget=forms.CheckboxInput(attrs={'class':'checkbox'}))
    AutoMinorVersionUpgrade = forms.BooleanField(initial=json.dumps(data['AutoMinorVersionUpgrade']), label='Auto Minor Version Upgrade', widget=forms.CheckboxInput(attrs={'class':'checkbox'}))
    BackupRetentionPeriod = forms.CharField(max_length=8, initial=data['BackupRetentionPeriod'], label='Backup Retention Period', widget=forms.TextInput(attrs={'class':'form-control'}))
    BackupFrequency = forms.CharField(max_length=8, initial=data['BackupFrequency'], label='Backup Frequency', widget=forms.TextInput(attrs={'class':'form-control'}))
    PreferredBackupWindow = forms.CharField(max_length=16, initial=data['PreferredBackupWindow'], label='Preferred Backup Window', widget=forms.TextInput(attrs={'class':'form-control'}))
    #PreferredMaintenanceWindow = forms.CharField(max_length=16, initial=data['PreferredMaintenanceWindow'], label='Preferred Maintenance Window', widget=forms.TextInput(attrs={'class':'form-control'}))
    PreferredMaintenanceWindow = forms.MultipleChoiceField(choices= HOURS, initial=data['PreferredMaintenanceWindow'], label='Preferred Maintenance Window', widget=forms.SelectMultiple(attrs={'class':'form-control'}))
    
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
            if isinstance( data[key], bool ):
                self.fields[key] = forms.BooleanField(label=key, initial=data[key], required = False, widget=forms.CheckboxInput(attrs={'class':'checkbox'}))
            elif isinstance( data[key], ( int, long ) ):
                self.fields[key] = forms.IntegerField(label=key, initial=data[key], widget=forms.NumberInput(attrs={'class':'form-control'}))
            else:
                self.fields[key] = forms.CharField(label=key, initial=data[key], widget=forms.TextInput(attrs={'class':'form-control'}))

class ProvisionFormPage4(forms.Form):
    data = properties['IAM']
    AwsKeyId = forms.CharField(max_length=16, initial=data['AwsKeyId'], label='AwsKeyId', widget=forms.TextInput(attrs={'class':'form-control'}))
    AwsSecret = forms.CharField(max_length=32, initial=data['AwsSecret'], label='AwsSecret', widget=forms.PasswordInput(attrs={'class':'form-control'})  )

    
    
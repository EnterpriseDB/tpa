from pgadmin import celery
import config
import time, random
@celery.task(bind=True)
def create_service_async(self,serviceId):
    for i in range(0,100):
        message = "Task iD %s provisioning ..%d of 100%%"  %(str(self.request.id), i)
        print message
        self.update_state(state='PROGRESS', meta={'current':i,'total':100,'status':message})
        time.sleep(1)   
    print "Celery got task to create service "+str(serviceId)   
    print "Celery got task to create for App "+str(config.APP_NAME)
    return "Created Services"
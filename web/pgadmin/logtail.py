import os, re
from xml.sax.saxutils import escape

def log_tail(service_id):
        path_to_tail = '/var/log/syslog'
        log = open(path_to_tail,'r')
        if not log:
            return
        stats = os.stat(path_to_tail)
        ino = stats.st_ino
        size = stats.st_size
        #log.seek(-150*1024, 2)
        '''for i in range(0,10):
            print "%d-%s" %(i,log.readline())
        print "Size "+ str(size)
        if(size > 150*1024 and log.seek(-150*1024, 2)):
            print "Log Line Dummy"
            dummy = log.readline()
            print dummy'''
        count = 0    
        '''for line in log:
            count+=1
            
         
            '''
        data = log.readlines()
        lc=len(data)
        count = 0
        i=0    
        for line in data:
            count+=1
            #Get Last 150 lines
            if count>lc -150:
                i+=1
                print "%d: %s" %(i,line)
                
        print re.compile(re.escape(("."))).pattern            
            
            
log_tail(1)
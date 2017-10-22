from threading import Thread
import boto3

# Version 1.2
## Author: David Cedar(2017)

### ------------------------------------
###    Save Products to DynamoDB Class
### ------------------------------------
class SaveProducts:
    
    products_buffer = list()
    
    #Constructor function
    def __init__ (self):
        ### Save prodct into database
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('productfinder_product_2')
        #Helper
        self.stopped = False
    
    ###---------------------------------------------------
    ###   Main handler function for the multi threading
    ###--------------------------------------------------- 
    def start(self):
        Thread(target=self.update, args=()).start()
        return self
    
    ### Runs on Multi Thread
    def update(self):
        with self.table.batch_writer() as batch:
            #Keep Running for Thread Life
            while True:
                # keep looping infinitely until the thread is stopped
                if len(self.products_buffer) > 0:
                    try:
                        self.table.put_item(Item = self.products_buffer[0].ReturnJson()) #Save oldest product
                        self.products_buffer.pop(0) #Remove oldest product
                        print("[**] Successfully Uploaded Product")
                        print("[*] Buffer Size: {}".format(len(self.products_buffer)))
                    except:
                        #Failed to save product into db.
                        #TODO: Add err message
                        print("[-] Upload Error")
                        self.stopped = True
                        

                # if the thread indicator variable is set, stop the thread
                # and resource camera resources
                if self.stopped:
                        return
                    
    def append(self, product):
        # Append product into buffer
        if product != None:
            self.products_buffer.append(product)
            print("yes")
            
    def alive(self):
        if len(self.products_buffer) < 1: 
            return False
        else:
            return True
        
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
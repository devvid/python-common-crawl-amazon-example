from bs4 import BeautifulSoup
from product import Product
from rake import Rake
import SmartStopList
import requests
import json
import re
import productfinder_helper
from threading import Thread

# Version 1.2
## Author: David Cedar(2017)

class ProductFinder:
    
    record_list = list()
    save_thread = None
    
    def __init__(self, record_list):
        self.record_list = record_list
        #Helper
        self.stopped = False
        self.finished = False
    
    ###---------------------------------------------------
    ###   Main handler function for the multi threading
    ###--------------------------------------------------- 
    def start(self, savethread):
        print("[*] Starting Product Finder Thread")
        self.save_thread = savethread
        Thread(target=self.update, args=()).start()
        return self
    
    ### Runs on Multi Thread
    def update(self):
        i = 0
        for record in self.record_list:
            i = i + 1
            #URL Checkers. Bad: artist-redirect, %%%, 
            if len(record['url']) > 23 and record['url'].count('%') < 5 and record['url'].count('artist-redirect') < 1:
                print("[{} of {}]".format(i, len(self.record_list)))
                #Ok to download and inspect
                html_content = productfinder_helper.download_page(record)
                print "[*] Retrieved {} bytes for {}".format(len(html_content), record['url'])
                #Collects all the pages to a list
                product, errs = productfinder_helper.extract_product(html_content, record['url'])
                if product: 
                    self.save_thread.append(product)
                    print("[Success Append]")
                    if errs:
                        print("[Errors:]")
                        for err in errs:
                            print(" *  {}".format(err))
                else:
                    print("Failed to EXTRACT Product")
                    
            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                return
        self.finished = True
        print "[*] Total external links discovered: %d" % len(products)
        
    def check_status(self):
        return self.finished


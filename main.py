## Author: David Cedar(2017) https://www.cedar.net.au

# Super big thanks to Justin for the inspiration https://www.bellingcat.com/resources/2015/08/13/using-python-to-mine-common-crawl/

## PRODUCT FINDER ##
# Scans common crawl infomation for products and
# saves them to Amazon DynomoDB database.

#Install
#   boto3: https://github.com/boto/boto3. Make sure to add AWS Credentials on our machine, see docs.
#   

#Test Make sure code is working with local example - Run
#   python productfinder_helper.py
#Run
#   python main --domain amazon.com

# Version 1.2

import requests
import argparse
import time
import json
import StringIO
import gzip
import boto3
from bs4 import BeautifulSoup

#Own
from product import Product
from saveproducts import SaveProducts
from productfinder import ProductFinder

import sys
reload(sys)
sys.setdefaultencoding('utf8')

# parse the command line arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d","--domain", required=True, help="The domain to target ie. youtube.com")
args = vars(ap.parse_args())

domain = args['domain']

# list of available indices, "2014-52"
# index_list = ["2017-39", "2017-34", "2017-30", "2017-26", "2017-22", "2017-17"]
index_list = ["2017-39"]


### -----------------------
### Searches the Common Crawl Index for a domain.
### -----------------------
def search_domain(domain):
    record_list = []
    print "[*] Trying target domain: %s" % domain
    
    for index in index_list:
        print "[*] Trying index %s" % index
        cc_url  = "http://index.commoncrawl.org/CC-MAIN-%s-index?" % index
        cc_url += "url=%s&matchType=domain&output=json" % domain
        
        response = requests.get(cc_url)
        
        if response.status_code == 200:
            records = response.content.splitlines()
            for record in records:
                record_list.append(json.loads(record))  
            print "[*] Added %d results." % len(records)
    print "[*] Found a total of %d hits." % len(record_list)
    return record_list        

### -----------------------
###     Main Function
### -----------------------
def main():
    print("Starting CommonCrawl Search")
    #Finds all relevant domins
    record_list = search_domain(domain)
    
    #Creating save object - Products are saved to Amazon DynamoDB
    savethread = SaveProducts().start()
    
    #Downloads page from CommconCrawl and Inspects, then Extracts infomation
    product_finder_1 = ProductFinder(record_list[0: int(len(record_list)/2)]).start(savethread)
    product_finder_2 = ProductFinder(record_list[int(len(record_list)/2): int(len(record_list))]).start(savethread)
    
    #Idle Main Thread
    while product_finder_1.check_status() != True and product_finder_2.check_status() != True:
        time.sleep(1)
        
    while savethread.alive(): 
        time.sleep(1)
        
    #Stop Threads    
    product_finder_1.stop()
    product_finder_2.stop()
    savethread.stop()

if __name__ == '__main__':
    main()
    #Fin

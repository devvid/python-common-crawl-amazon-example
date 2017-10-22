import requests
import argparse
import time
import json
import StringIO
import gzip
import boto3
from bs4 import BeautifulSoup
from product import Product
from rake import Rake
import SmartStopList
import json
import re

# Version 1.2
## Author: David Cedar(2017)
#
# Downloads full page
#
def download_page(record):

    offset, length = int(record['offset']), int(record['length'])
    offset_end = offset + length - 1

    # We'll get the file via HTTPS so we don't need to worry about S3 credentials
    # Getting the file on S3 is equivalent however - you can request a Range
    prefix = 'https://commoncrawl.s3.amazonaws.com/'

    # We can then use the Range header to ask for just this set of bytes
    resp = requests.get(prefix + record['filename'], headers={'Range': 'bytes={}-{}'.format(offset, offset_end)})

    # The page is stored compressed (gzip) to save space
    # We can extract it using the GZIP library
    raw_data = StringIO.StringIO(resp.content)
    f = gzip.GzipFile(fileobj=raw_data)

    # What we have now is just the WARC response, formatted:
    data = f.read()

    response = ""

    if len(data):
        try:
            warc, header, response = data.strip().split('\r\n\r\n', 2)
        except:
            pass

    return response

#
# Helper function for Check_Page. Searchs a page for a table and loops through to find target.
#
def search_table(parsed, att, target):
    table_1 = parsed.find("table", attrs=att)
    if table_1 == None:
        #print("Failed to search table")
        return (False, None)
    table_1_rows = table_1.find_all('tr')
    found = False
    value = ""
    #Loop rows
    for row in table_1_rows:
        ths = row.find_all("th")
        tds = row.find_all("td")
        rn = ths[0].get_text()
        #Check th of table
        if target in rn:
            value = tds[0].get_text().strip()
            if len(value) > 2:
                found = True  
    if found:
        return (True, value)
    else:
        return (False, None)

#
# Perform Precheck to see if page is a product
#
def check_page(parsed):
    parser = parsed

    #First Check of ASIN
    found, asin = search_table(parser, {"id": "productDetails_detailBullets_sections1"}, "ASIN")
    if found:
        return (True, asin)

    #Second Check of ASIN
    check_asin_2 = parser.find("b", text="ASIN:")    
    check_asin_3 = parser.find("b", text="ASIN: ")    

    if check_asin_2 == None and check_asin_3 == None:
        print("Page is Not a Product")
        return (False, None)
    else:
        if check_asin_2 != None:
            asin = check_asin_2.findParent().text[5:]
        if check_asin_3 != None:
            asin = check_asin_3.findParent().text[5:]
        #TODO: Add additional checks to confirm the page is definatly a product!
        print("Page is a Product")
        return (True, asin)

#
# Extract Product from the single HTML page.   
#
def extract_product(html_content, url):
    #String Buffer
    string_buffer = "" 
    errs = list()

    #Read page and read to extract product infomation
    parser = BeautifulSoup(html_content, "html.parser")  

    #Check if the page is a product, if not skip page.
    truth, asin = check_page(parser)
    if not truth:
        errs.append("Not product")
        return (False, errs)

    #New Product as a object
    product = Product()
    #New Keyword rank
    keyword = Rake(SmartStopList.words())


    #Find URL
    product.SetUrl(url)

    #Find Brand: Note: Some products have an image for the brand 
    truth, string_buffer = search_table(parser, {"id": "productDetails_techSpec_section_1"}, "Brand Name")
    if truth:
        product.SetBrand(string_buffer)
    else:
        string_buffer = parser.find("a", attrs={"id": "brand"})
        if string_buffer != None:
            product.SetBrand(string_buffer.get_text().strip())
        else:
            errs.append("Could not find Brand")

    #Find Title
    string_buffer = parser.find("span", attrs={"id": "productTitle"})
    if string_buffer != None:
        product.SetTitle(string_buffer.get_text().strip())
    else:
        errs.append("Could not find Title")
        return (False, errs) 

    #Find Image
    string_buffer = parser.find("img", attrs={"id": "landingImage"})
    if string_buffer != None:
        string_buffer = string_buffer.get("data-old-hires")
        if len(string_buffer) < 2:
            string_buffer = parser.find("img", attrs={"id": "landingImage"}).get("data-a-dynamic-image")
            m = re.search('https://(.+?).jpg', string_buffer)
            if m:
                string_buffer = m.group(1)
                string_buffer = "https://{}.jpg".format(string_buffer)
        #print ("Img Url: "+string_buffer)
        product.SetImage(string_buffer)
    else:
        errs.append("Could not find Image")

    #Find Small Blob
    #TODO: Need to perform keyword analysis
    string_buffer = parser.find("div", attrs={"id": "feature-bullets"})
    if string_buffer != None:
        string_buffer = string_buffer.find("ul")
    try:        
        string_buffer = string_buffer.find_all("li")
        if string_buffer != None:
            string_buffer_2 = ""
            for span in string_buffer:
                string_buffer_3 = span.find("span")
                if string_buffer_3 != None:
                    string_buffer_3 = string_buffer_3.get_text()
                    try:
                        string_buffer_2 = "{} {}".format(string_buffer_2, string_buffer_3.strip())
                    except: 
                        pass
            saved_buffer = string_buffer_2.strip()
            #Calculating Key Words
            keywords_1 = keyword.run(saved_buffer)
            product.SetSmallBlog(keywords_1)
    except:	
        errs.append("Error finding li")

    else:
        errs.append("Could not find small section keywords")


    #Find Large Blob
    #TODO: Need to perform keyword analysis
    string_buffer = parser.find("div", attrs={"id": "productDescription"})
    if string_buffer != None:
        string_buffer = string_buffer.find("p")
    if string_buffer != None:	
        string_buffer = string_buffer.get_text()
        saved_buffer = string_buffer.strip()
        #Calculating Key Words
        keywords_2 = keyword.run(saved_buffer)
        product.SetLargeBlob(keywords_2)
    else:
        errs.append("Could not find large section keywords")

    #Find ASIN
    product.SetSourceID(asin)

    #TODO: Perform price save!

    #Append the product to large list of products
    if product.FormCompleted():
        return (product, errs)
    else:
        return (False, errs)

### Example code running from html file 
if __name__ == '__main__':
    print("Script Starting")
    html = open("test_html/amazon2.html")
    url = "https://www.amazon.com/gp/product/B018YHS8BS/ref=s9u_cartx_gw_i3?ie=UTF8&fpl=fresh&pd_rd_i=B018YHS8BS&pd_rd_r=1ZPRY1Q53VY71P1MH3R1&pd_rd_w=E8D0B&pd_rd_wg=l88CZ&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=&pf_rd_r=EQZ2X5XE1BBK1J41FKVB&pf_rd_t=36701&pf_rd_p=eb9f3a57-8cdf-4fa3-a48e-183b5d4b6520&pf_rd_i=desktop"
    products = list()
    product, errs = extract_product(html, url)
    if product:
        products.append( product )
        product.Print()
        print("[Success Append]")
    else:
        print("Returned False")
    if errs:
        print("[Errors:]")
        for err in errs:
            print(" *  {}".format(err))    
    print("Script Finished")

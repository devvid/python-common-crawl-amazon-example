## Author: David Cedar(2017)
import json
import hashlib
from time import gmtime, strftime

# Version 1.2

########  Product Class   ########
class Product:
    title = "e"
    brand = "e"
    url = "e"
    image_url = "e"
    blob_small = "Unknown"
    blob_large = "Unknown"
    source_id = "asin"
    source_domain = "amazon"
    
    ## Inti
    def __init__(self, product=None ):
        #Initialise Object with a Json array instead of using Setters.
        if product != None:           
            self.title = product.title
            self.brand = product.brand
            self.url = product.url
            self.images = product.images
            self.blob_small = product.blob_small
            self.blob_large = product.blob_large
            self.source_id = product.source_id
            self.source_domain = product.source_domain
        print("New Product object Initialised in memory")
        
    ## Setters and Getters    
    def SetTitle(self, title):
        self.title = title.strip()

    def SetBrand(self, brand):
        self.brand = brand    
    
    def SetUrl(self, url):
        self.url = url
        
    def SetImage(self, url):
        if len(url) > 1:
            self.image_url = url
    
    def SetSmallBlog(self, blob):
        self.blob_small = blob
    
    def SetLargeBlob(self, blob):
        self.blob_large = blob
        
    def SetSourceID(self, id):
        #Strip removes white spaces and any other none standard chars
        self.source_id = id.strip()
    
    def SetSourceDomain(self, domain):
        self.source_domain = domain
    
    
    ## Support 
    def FormCompleted(self):
        #TODO: Returns True if the fields have been filled in.
        if len(self.title) > 1 and len(self.brand) > 1 and len(self.url) > 1 and len(self.source_id) > 1 and len(self.source_domain) > 1 :
            return True
        else:
            return True

    def ReturnJson(self):
        #Reutnrs Object infomation in form of a Json array
        m = hashlib.md5()
        m.update(self.source_id)
        product = {
            'uid':        m.hexdigest(), #Set as main index in DynamoDB
            'title':      self.title,
            'brand':      self.brand,
            'url':        self.url,
            'image_url':     self.image_url,
            'small_keywords': self.blob_small,
            'large_keywords': self.blob_large,
            'sid':        self.source_id,
            'domain':     self.source_domain,
            'date':       strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }
        return (product)

    def Print(self):
        print("### Printing Product ###")
        print(self.ReturnJson())
        print("###        end       ###")
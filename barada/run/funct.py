
import datetime
from datetime import datetime as dt
from pymongo import MongoClient

# List of reusable functions 

# Connect and fetch data from MongoDB
def connect_to_mongodb(mongo_uri,db_name):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    db.auth
    collection = db.jobs_items
    #if db_collection == 'jobs_items':
    #    collection = db.jobs_items
    #elif db_collection == 'contacts_items':
    #    collection = db.contacts_items

    return collection

# Check if current fetched URL is duplicate before processing and storing in DB
def is_url_duplicate(url_to_test, data_collection):
    duplicate = False

    for item in data_collection.find():
        if url_to_test == item['job_url']:
            duplicate = True
            #print('Duplicate found!')
            break
        else:
            pass
    return duplicate

# Clean dirty dates and transform them from String to Datetime
def convert_date(site, dirty_date):
    if site == 'emploi.ci':
        clean_date = dt.strptime(dirty_date.strip('Publiée le '), '%d.%m.%Y')
    elif site == 'educarriere.ci': 
        clean_date = dt.strptime(dirty_date, '%d/%m/%Y')
    else:
        clean_date = dt.strptime(dirty_date, '%Y-%m-%d')

    return clean_date

    ### Normalement la date de publication est au format Y-m-d pour tout le monde...
import requests 
import json 
import pandas as pd 
from dateutil import parser
import math
import zipcodes
import pytz
import glob
import re
import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from time import sleep
from tqdm import tqdm
import warnings
import time
import os
import random
import paramiko
from itertools import chain
import boto3
import concurrent.futures
from PIL import Image
import subprocess

#PROMPT EXTRACTS ALL DATA FROM WA AND OUTPUTS DATASET. USER CAN SEARCH USING ADDRESS. (STATIC DATA)

# extract property data main script
def extract_main():
    # set dates and covert time to PST
    day_of_month = datetime.datetime.today().day
    pst = pytz.timezone('US/Pacific')
    utc_now = datetime.datetime.now(tz=pytz.UTC)
    pst_now = utc_now.astimezone(pst)
    today = pst_now.strftime('%Y-%m-%d-%H:%M')
    
    # set states
    states = [
        # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#States.
        "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA",
        "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO",
        "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK",
        "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI",
        "WV", "WY"
    ]

    allode_operating_states = ["WA"]
    
    # main functions
    df = extract_properties(day_of_month, states, allode_operating_states)
    df = cleanup_dataframe(df)
    df = df[df['status'] == 'For Sale']
    df = df.sort_values(by='list_date')
    
    # upload dataframe to s3
    file_name = "Allode-{}.csv".format(today) 
    df.to_csv(file_name, index=False)
    
    # pass photos to be uploaded to sftp separately
    all_photos = list(chain.from_iterable(filter(None, [entry.split(',') if entry is not None else None for entry in df['all_photos']])))
    
    return df

# retry sessions function
def requests_retry_session(
        retries=3,
        backoff_factor=0.5,
        # status_forcelist=(500, 502, 504),
        session=None,
    ):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor
        # status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# extracts all zipcodes for a state
def extract_zip_codes_by_state(state):
    return [{"postal_code": entry['zip_code'], "city": entry['city'], "state": state, "county": entry['county']} for entry in zipcodes.filter_by(state=state)]

# extracts all zipcodes for all states using function above
def extract_all_zip_codes(states):
    result = []
    for state in states:
        result += extract_zip_codes_by_state(state)
    return result

# main function to web-scrape realtor.com
def scrape_zip(dict, offset=0):
    results = []
    proxies = {
    "http": "http://mdeguzman827:SexyDexy0827901@pr.oxylabs.io:7777"
    }

    # set request variables
    url = "https://www.realtor.com/api/v1/hulk?client_id=rdc-x&schema=vesta"
    headers = {"content-type": "application/json"}

    # set query details for scrape
    body = r'{"query":"\n\nquery ConsumerSearchMainQuery($query: HomeSearchCriteria!, $limit: Int, $offset: Int, $sort: [SearchAPISort], $sort_type: SearchSortType, $client_data: JSON, $geoSupportedSlug: String!, $bucket: SearchAPIBucket, $by_prop_type: [String])\n{\n  home_search: home_search(query: $query,\n    sort: $sort,\n    limit: $limit,\n    offset: $offset,\n    sort_type: $sort_type,\n    client_data: $client_data,\n    bucket: $bucket,\n  ){\n    count\n    total\n    results {\n      property_id\n      list_price\n      primary_photo (https: true){\n        href\n      }\n      source {\n        id\n        agents{\n          office_name\n        }\n        type\n        spec_id\n        plan_id\n      }\n      community {\n        property_id\n        description {\n          name\n        }\n        advertisers{\n          office{\n            hours\n            phones {\n              type\n              number\n            }\n          }\n          builder {\n            fulfillment_id\n          }\n        }\n      }\n      products {\n        brand_name\n        products\n      }\n      listing_id\n      matterport\n      virtual_tours{\n        href\n        type\n      }\n      status\n      permalink\n      price_reduced_amount\n      other_listings{rdc {\n      listing_id\n      status\n      listing_key\n      primary\n    }}\n      description{\n        beds\n        baths\n        baths_full\n        baths_half\n        baths_1qtr\n        baths_3qtr\n        garage\n        stories\n        type\n        sub_type\n        lot_sqft\n        sqft\n        year_built\n        sold_price\n        sold_date\n        name\n        text\n}\n      location{\n        street_view_url\n        address{\n          line\n          postal_code\n          state\n          state_code\n          city\n          coordinate {\n            lat\n            lon\n          }\n        }\n        county {\n          name\n          fips_code\n        }\n      }\n      tax_record {\n        public_record_id\n      }\n      lead_attributes {\n        show_contact_an_agent\n        opcity_lead_attributes {\n          cashback_enabled\n          flip_the_market_enabled\n        }\n        lead_type\n      }\n      open_houses {\n        start_date\n        end_date\n        description\n        methods\n        time_zone\n        dst\n      }\n      flags{\n        is_coming_soon\n        is_pending\n        is_foreclosure\n        is_contingent\n        is_new_construction\n        is_new_listing (days: 14)\n        is_price_reduced (days: 30)\n        is_plan\n        is_subdivision\n      }\n      list_date\n      last_update_date\n      coming_soon_date\n      photos(limit: 50, https: true){\n        href\n      }\n      tags\n      branding {\n        type\n        photo\n        name\n      }\n    }\n  }\n  geo(slug_id: $geoSupportedSlug) {\n    parents {\n      geo_type\n      slug_id\n      name\n    }\n    geo_statistics(group_by: property_type) {\n      housing_market {\n        by_prop_type(type: $by_prop_type){\n          type\n           attributes{\n            median_listing_price\n            median_lot_size\n            median_sold_price\n            median_price_per_sqft\n            median_days_on_market\n          }\n        }\n        listing_count\n        median_listing_price\n        median_rent_price\n        median_price_per_sqft\n        median_days_on_market\n        median_sold_price\n        month_to_month {\n          active_listing_count_percent_change\n          median_days_on_market_percent_change\n          median_listing_price_percent_change\n          median_listing_price_sqft_percent_change\n        }\n      }\n    }\n    recommended_cities: recommended(query: {geo_search_type: city, limit: 20}) {\n      geos {\n        ... on City {\n          city\n          state_code\n          geo_type\n          slug_id\n        }\n        geo_statistics(group_by: property_type) {\n          housing_market {\n            by_prop_type(type: [\"home\"]) {\n              type\n              attributes {\n                median_listing_price\n              }\n            }\n            median_listing_price\n          }\n        }\n      }\n    }\n    recommended_neighborhoods: recommended(query: {geo_search_type: neighborhood, limit: 20}) {\n      geos {\n        ... on Neighborhood {\n          neighborhood\n          city\n          state_code\n          geo_type\n          slug_id\n        }\n        geo_statistics(group_by: property_type) {\n          housing_market {\n            by_prop_type(type: [\"home\"]) {\n              type\n              attributes {\n                median_listing_price\n              }\n            }\n            median_listing_price\n          }\n        }\n      }\n    }\n    recommended_counties: recommended(query: {geo_search_type: county, limit: 20}) {\n      geos {\n        ... on HomeCounty {\n          county\n          state_code\n          geo_type\n          slug_id\n        }\n        geo_statistics(group_by: property_type) {\n          housing_market {\n            by_prop_type(type: [\"home\"]) {\n              type\n              attributes {\n                median_listing_price\n              }\n            }\n            median_listing_price\n          }\n        }\n      }\n    }\n    recommended_zips: recommended(query: {geo_search_type: postal_code, limit: 20}) {\n      geos {\n        ... on PostalCode {\n          postal_code\n          geo_type\n          slug_id\n        }\n        geo_statistics(group_by: property_type) {\n          housing_market {\n            by_prop_type(type: [\"home\"]) {\n              type\n              attributes {\n                median_listing_price\n              }\n            }\n            median_listing_price\n          }\n        }\n      }\n    }\n  }\n}","variables":{"query":{"status":["for_sale","ready_to_build"],"primary":true,"postal_code":"%s"},"client_data":{"device_data":{"device_type":"web"},"user_data":{"last_view_timestamp":-1}},"limit":200,"offset":%s,"zohoQuery":{"silo":"search_result_page","location":"%s","property_status":"for_sale","filters":{},"page_index":"1"},"sort_type":"relevant","geoSupportedSlug":"","by_prop_type":["home"]},"operationName":"ConsumerSearchMainQuery","callfrom":"SRP","nrQueryType":"MAIN_SRP","visitor_id":"eff16470-ceb5-4926-8c0b-6d1779772842","isClient":true,"seoPayload":{"asPath":"/realestateandhomes-search/%s/pg-1","pageType":{"silo":"search_result_page","status":"for_sale"},"county_needed_for_uniq":false}}' % (dict['postal_code'], offset, dict['city'], dict['city'])
    json_body = json.loads(body)

    # send request
    r = requests_retry_session().post(url=url, json=json_body, headers=headers, proxies=proxies)
    json_data = r.json()

    # recursive function to iterate through each page until all listing compiled into results
    try:
        if 'data' in json_data and 'home_search' in json_data['data']:
            home_search = json_data['data']['home_search']
            if 'results' in home_search and home_search['results'] is not None:
                results += home_search['results']
            total_listings = home_search['total']

            if offset + 200 >= total_listings:
                return results
            else:
                offset += 200
                results += scrape_zip(dict, offset=offset)
        else:
            print("No data found in the response")
        return results
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return results

# create dataframe from web-scraped results
def create_dataframe(results):
    feature_dict_list = []

    for entry in results:
        # print(entry)
        feature_dict = {
        "id": entry["property_id"],
        "list_date": entry['list_date'],
        "house_type": entry["description"]["type"],
        "price": entry["list_price"],
        "street": entry["location"]["address"]["line"],
        "postal_code": entry["location"]["address"]["postal_code"],
        "state": entry["location"]["address"]["state_code"],
        "city": entry["location"]["address"]["city"],
        "description": entry['description']['text'],
        "beds": entry["description"]["beds"],
        "baths": entry["description"]["baths"],
        "garage": entry["description"]["garage"],
        "stories": entry["description"]["stories"],
        "sqft": entry["description"]["sqft"],
        "lot_sqft": entry["description"]["lot_sqft"],
        "year_built": entry["description"]["year_built"],
        "tags": entry["tags"],
        "flags": entry['flags'],
        "primary_photo": entry['primary_photo'],
        "all_photos": entry['photos'],
        "virtual_tour": entry['virtual_tours']
        }
            
        if entry["location"]["address"]["coordinate"]:
            feature_dict.update({"lat": entry["location"]["address"]["coordinate"]["lat"]})
            feature_dict.update({"lon": entry["location"]["address"]["coordinate"]["lon"]})
        
        if entry["location"]["county"]:
            feature_dict.update({"county": entry["location"]["county"]["name"]})


        feature_dict_list.append(feature_dict)
        
    df = pd.DataFrame(feature_dict_list)

    return df

# extract links
def get_href_from_nested_lists(list_of_lists):
    hrefs = []
    for inner_list in list_of_lists:
        if inner_list is not None:
            for d in inner_list:
                if d is not None and 'href' in d:
                    hrefs.append(d['href'])
                else:
                    hrefs.append(None)
        else:
            hrefs.append(None)
    
    return hrefs

# impute status based on flags
def impute_status(entry):
    if entry['is_coming_soon']:
        return "Coming Soon"
    elif entry['is_pending']:
        return "Pending"
    else:
        return "For Sale"

# impute type
def impute_type(entry):
    if entry['house_type'] is None:
        return None
    elif entry['house_type'] == 'single family':
        return 'Single Family'
    elif entry['house_type'] == 'multi family':
        return 'Multi Family'
    elif entry['house_type'] == 'land':
        return 'Land'
    elif entry['house_type'] == 'mobile':
        return 'Mobile'
    elif 'condo' in entry['house_type']:
        return 'Condominium'
    elif 'townho' in entry['house_type']:
        return 'Townhome'
    elif 'coop' in entry['house_type']:
        return 'Co-op'
    elif entry['house_type'] == 'farm':
        return 'Farm'
    else:
        return 'Other'
        
    
# clean up data
def cleanup_dataframe(df):
    # clean fields
    df['list_date'] = [parser.parse(entry) for entry in df['list_date']]
    df['house_type'] = [entry.replace('_',' ') if entry is not None else None for entry in df['house_type']]
    df['house_type_imputed'] = df.apply(lambda entry : impute_type(entry), axis=1)
    df['address'] = df['street'] + ', ' + df['city'] + ', ' + df['state'] + ' ' + df['postal_code'].apply(lambda x: str(x))
    df['beds'] = df['beds'].fillna(-1).astype(int).replace(-1, None)
    df['baths'] = df['baths'].fillna(-1).astype(int).replace(-1, None)
    df['garage'] = df['garage'].fillna(-1).astype(int).replace(-1, None)
    df['sqft'] = df['sqft'].fillna(-1).astype(int).replace(-1, None)
    df['lot_sqft'] = df['lot_sqft'].fillna(-1).astype(int).replace(-1, None)
    df['stories'] = df['stories'].fillna(-1).astype(int).replace(-1, None)
    df['year_built'] = df['year_built'].fillna(-1).astype(int).replace(-1, None)
    df['primary_photo'] = [entry['href'] if entry is not None else None for entry in df['primary_photo']]
    df['all_photos'] = [",".join([photo['href'].replace('.jpg','-w480_h360_x2.webp?w=1080&q=75.jpg') for photo in entry]) if entry is not None else None for entry in df['all_photos']]
    df['all_photos_filenames'] = [",".join([os.path.basename(url) for url in entry.split(',')]) if entry is not None else None for entry in df['all_photos']]
    df['virtual_tour'] = get_href_from_nested_lists(df['virtual_tour'])
    df['tags'] = [",".join([tag.replace('_',' ').title() for tag in entry]) if entry is not None else None for entry in df['tags']]

    # impute status
    df['is_coming_soon'] = [entry['is_coming_soon'] for entry in df['flags']]
    df['is_pending'] = [entry['is_pending'] for entry in df['flags']]
    df['is_foreclosure'] = [entry['is_foreclosure'] for entry in df['flags']]
    df['is_contingent'] = [entry['is_contingent'] for entry in df['flags']]
    df['is_new_construction'] = [entry['is_new_construction'] for entry in df['flags']]
    df['is_new_listing'] = [entry['is_new_listing'] for entry in df['flags']]
    df['is_price_reduced'] = [entry['is_price_reduced'] for entry in df['flags']]
    df['is_plan'] = [entry['is_plan'] for entry in df['flags']]
    df['is_subdivision'] = [entry['is_subdivision'] for entry in df['flags']]
    df['status'] = df.apply(lambda entry : impute_status(entry), axis=1)
    df.drop(['flags'], axis=1, inplace=True)
    
    return df

# extract all properties from zipcodes depending on state
def extract_properties(day_of_month, states, allode_operating_states):
    
    # ignore warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    # set variables
    df = pd.DataFrame()
    zip_code_dict = extract_all_zip_codes(states)

    # extract data from all states on the first of each month
    if day_of_month == 40:
        for zip_code in tqdm(zip_code_dict):
            try:
                json_data = scrape_zip(zip_code)
                temp_df = create_dataframe(json_data)
                df = pd.concat([df, temp_df], ignore_index=True)
            except:
                print("ERROR: Did not extract {}".format(zip_code))
                time.sleep(10)

    # extract states where allode operates everyday
    else:
        allode_operating_zip_codes = [zip_code for zip_code in zip_code_dict if zip_code['county']=='King County'] #state'] in allode_operating_states]
        for zip_code in tqdm(allode_operating_zip_codes):
            json_data = scrape_zip(zip_code)
            temp_df = create_dataframe(json_data)
            df = pd.concat([df, temp_df], ignore_index=True)
    
    return df

# download images to local
def download_image(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")
        return False

# upload to sftp
def upload_to_sftp(local_file, remote_file, sftp):
    sftp.put(local_file, remote_file)

def compress_image(input_path, output_path):
    # Open the image
    img = Image.open(input_path)
    
    # Save the image using Pillow to ensure it is in JPEG format
    img.save(output_path, "JPEG")

    # Use jpegoptim for lossless compression
    subprocess.run(["jpegoptim", "--max=100", "--strip-all", "--quiet", output_path])

# single worker
def upload_worker(sftp_folder, temp_dir, url, sftp):
    basefilename = os.path.basename(url)
    local_filename = os.path.join(temp_dir, basefilename)
    if download_image(url, local_filename):
        remote_filename = os.path.join(sftp_folder, basefilename)
        # compress_image(local_filename, local_filename)
        upload_to_sftp(local_filename, remote_filename, sftp)
        
# filter for images
def is_image(filename):
    image_extensions = {'.jpg', '.jpeg', '.png'}
    return os.path.splitext(filename.lower())[1] in image_extensions

# get new photos and old photos to prepare for cleaning
def filter_photos(sftp, sftp_folder, all_photos):
    
    past_photo_files = set([f for f in sftp.listdir(sftp_folder) if is_image(f)])
    current_photo_files = set([os.path.basename(x) for x in all_photos])

    new_uploads = {url for url in set(all_photos) if url.split('/')[-1] not in past_photo_files}
    old_uploads = list(past_photo_files - current_photo_files)
            
    return new_uploads, old_uploads     

# remove old photos
def cleanup_sftp(sftp, sftp_folder, old_uploads):
    for photo in tqdm(old_uploads):
        try:
            sftp.remove(sftp_folder + '/' + photo)
        except:
            continue

print('Extracting property data...')
df = extract_main()

import argparse, sys
from argparse import RawTextHelpFormatter
import httpx, requests, shutil
import xmltodict
import json, os, glob
from bs4 import BeautifulSoup as bs
import re


weight = False
onsite = False

parser = argparse.ArgumentParser(description="Fetch upcoming CTFs from ctftime.org", formatter_class=RawTextHelpFormatter)
parser.add_argument('-w', '--weight',metavar='', help='removes 0 weighted CTFs if set to true\nformat = --weight [true|false]')
parser.add_argument('-o', '--onsite', metavar='', help='adds onsite CTFs if set to true\nformat = --onsite [true|false]')

args = parser.parse_args()

if (bool(args.weight)):
    if(args.weight.lower() == 'true'):
        weight = True
    elif args.weight.lower() == 'false':
        pass
    else:
        sys.stdout.write(f"{sys.argv[0]}: ValueError: -w/--weight true/false")
        sys.exit(1)


if (bool(args.onsite)):
    if(args.onsite.lower() == 'true'):
        onsite = True
    elif args.onsite.lower() == 'false':
        pass
    else:
        sys.stdout.write(f"{sys.argv[0]}: ValueError: -o/--onsite true/false")
        sys.exit(1)



temp = os.path.join(r'./assets', r'tmp')
files = glob.glob(os.path.join(temp, "*"))
for f in files:
    os.remove(f)
    
client = httpx.Client()

rssUrl = "https://ctftime.org/event/list/upcoming/rss/"
rssfile = 'uctfrss.json'
headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
}

data = xmltodict.parse(client.get(
    rssUrl, 
    follow_redirects=True,
    headers=headers
    ).content
)['rss']['channel']['item']


modified = list()

for instance in (data):

    storage = dict()

    if (weight == True and float(instance['weight']) == 0.0)\
        or (onsite == False and instance['location'] != None):
        continue

    storage = {
        'title': instance['title'],
        'main_url': instance['url'],
        'event_link': instance['link'],
        'organizer': json.loads(instance['organizers'])[0]['name'],
        'name': instance['ctf_name'],
        'difficulty': instance['weight'],
        'location': instance['location'],
        'start_date': f"{instance['start_date'][6:8]}-{instance['start_date'][4:6]}-{instance['start_date'][:4]}",
        'finish_date': f"{instance['finish_date'][6:8]}-{instance['finish_date'][4:6]}-{instance['finish_date'][:4]}"  
    }


    html = client.get(
        instance['link'],
        headers=headers
    ).content

    soup = bs(html, 'lxml')
    desc = soup.find('div', attrs={'id': 'id_description'})
    if desc != None:
        storage['description'] = re.compile(r'<[^>]+>').sub('', str(desc.find('p')))
    else:
        storage['description'] = f"{storage['title']} is a jeopardy-style CTF hosted by {storage['organizer']}"
    
    
    imgfile = os.path.join('./assets', "ctftime.jpg")
    logoURL = instance['logo_url']

    if logoURL != None:
        
        url = f"https://ctftime.org{logoURL}"
        res = requests.get(url, stream=True, headers=headers)
        if res.status_code == 200:
            imgfile = f"{os.path.join(temp, instance['ctf_name'])}.{logoURL.split('.')[1]}"
            with open(imgfile,'wb') as fptr:
                shutil.copyfileobj(res.raw, fptr)

    storage['logo_path'] = imgfile
    modified.append(storage)

with open(rssfile, 'w', encoding='utf-8') as file:
    json.dump(modified, file, ensure_ascii=False, indent=2)


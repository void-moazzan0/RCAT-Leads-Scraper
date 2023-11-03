from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup, SoupStrainer
import time
import argparse
import sys

def get_links(url):

    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            links.add(href)
    return links

def email_wrapper(url):
    try:
        home_page_links = get_links(url)

        # Find the contact page link
        contact_page_link = None
        for link in home_page_links:
            if 'contact' in link.lower():
                contact_page_link = link
                break

        # Scrape email addresses from the contact page, if it exists
        if contact_page_link:
            contact_page_url = f'{url}/{contact_page_link}'
            contact_page_emails = extract_emails(contact_page_url)
        else:
            contact_page_emails = None

        # Scrape email addresses from the rest of the domain
        domain_emails = set()
        home_email = extract_emails(url)
        # for link in tqdm(home_page_links, desc='Scraping pages'):
        #     link_url = urljoin(domain, link)
        #     if urlparse(link_url).netloc == urlparse(domain).netloc:
        #         link_emails = extract_emails(link_url)
        #         domain_emails.update(link_emails)

        if contact_page_emails is not None:
            return contact_page_emails
        elif home_email is not None:
            return home_email
        else:
            return "None"
    except:
        return "None"

def extract_emails(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        parse_only = SoupStrainer(['a', 'span', 'h1', 'h2', 'h3', 'p','div'])
        soup = BeautifulSoup(response.content, 'html.parser', parse_only=parse_only)

        EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        emails = []

        for element in soup.select('a, span, h1, h2, h3, p, div'):
            emails.extend(EMAIL_REGEX.findall(element.text))

        return emails[0] if emails else "None"
    except:
        return "None"
total=0

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--total", type=int)
args = parser.parse_args()
if args.total:
    total=args.total
else:
    total=50


driver = webdriver.Chrome()
driver.set_page_load_timeout(20)  # set timeout to 20 seconds


try:
    # Navigate to your desired webpage
    driver.get('https://web.rcat.net/rcat/results?Distance=500&Latitude=29.6814047&Longitude=-95.0494602')  # Update with your page's URL

except:
    pass
# Find all elements with class 'ListingResults_Level5_CONTAINER'
containers = driver.find_elements(By.CLASS_NAME,'ListingResults_Level5_CONTAINER')
data={'Name':[],'Address':[],'Phone':[],'Website':[],'Email':[]}
print("Total: ",len(containers))
index=0
for container in containers:
    if index>=total:
        break
    sys.stdout.write(f"\rEntry {index}")
    sys.stdout.flush()  # Make sure the output is written to the console
    time.sleep(1)  # Just to simulate some delay between iterations
    index=index+1
    try:
        # Extract text from the element with class 'ListingResults_All_ENTRYTITLELEFTBOX'
        entry_title = container.find_element(By.CLASS_NAME,'ListingResults_All_ENTRYTITLELEFTBOX').text

        #street-adress locality region postal-code



        # Extract content from class 'ListingResults_Level5_MAIN'
        main_content = container.find_element(By.CLASS_NAME,'ListingResults_Level5_MAIN').text
        Address=''.join(main_content.split('\n')[:3])
        Phone = container.find_element(By.CLASS_NAME, 'ListingResults_Level5_PHONE1').text


        # Extract link from an a tag inside this element & inside class 'ListingResults_Level5_VISITSITE'
        visit_site_link = container.find_element(By.CSS_SELECTOR,'.ListingResults_Level5_VISITSITE a').get_attribute('href')

        data['Name'].append(entry_title)
        data['Address'].append(Address)
        data['Phone'].append(Phone)
        data['Website'].append(visit_site_link)
        data['Email'].append(email_wrapper(visit_site_link))

    except:
        pass

for key in data:
    print(f"The length of {key}: {len(data[key])}")
df = pd.DataFrame(data)

df.to_csv('RCAT_Leads.csv', index=False, mode='w')
# Close the browser window
driver.quit()

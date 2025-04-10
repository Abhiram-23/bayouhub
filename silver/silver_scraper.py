from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, SecretStr
import sys
import os
import asyncio
import csv
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent, Controller, Browser, BrowserConfig

# API key
api_key = os.getenv("GEMINI_API_KEY")

# Output model
class Post(BaseModel):
    listing_title: str
    listing_address: str
    listing_email: str
    listing_short_description: str
    listing_long_description: str
    listing_url: str

class Posts(BaseModel):
    data: List[Post]

controller = Controller(output_model=Posts)

llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-lite',
    api_key=SecretStr(api_key)
)

browser = Browser(
    config=BrowserConfig(
        chrome_instance_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    )
)

# Function to scrape listing
async def scrape_listing(listing_title, listing_address):
    agent = Agent(
        task=f"""Listing Title: {listing_title}, Listing Address: {listing_address}. 
                Your task is to search the internet and return the best available URL (official website preferred, 
                or Facebook/Instagram/other social media if official site is unavailable), along with a short and long description of the business, and the business email ID.
                Try to get the email ID from any available source. If you find the business website, visit its "Contact Us" or "About" page and extract any listed email addresses. 
                If the email is not on the website, check social media profiles or third-party directories.
                Provide the output in the following list format:
                - Website: <one best link>  
                - Short Description: <1–2 lines summary>  
                - Long Description: <detailed paragraph about the business>  
                - Business EmailId: <emailid>  
                If no reliable information is found, use "N/A" for the missing fields.
            """,
        llm=llm,
        controller=controller,
    )
    result = await agent.run()
    return result.final_result()

# Main function
async def main(start_line=1):
    csv_output_file = 'silver_output.csv'
    csv_input_file = 'silver.csv'

    header = [
        'Listing Title', 'Listing Email', 'Listing URL', 'Listing Address',
        'Listing Short Description', 'Listing Long Description'
    ]

    file_exists = os.path.isfile(csv_output_file)
    op = []

    with open(csv_output_file, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        if not file_exists:
            writer.writerow(header)

        with open(csv_input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for count, row in enumerate(reader, start=1):
                if count < start_line:
                    continue

                listing_title = row['Listing Title']
                listing_address = row['Listing Address']
                existing_email = row.get('Listing Email', '').strip()
                existing_url = row.get('Listing URL', '').strip()
                existing_short_desc = row.get('Listing Short Description', '').strip()
                existing_long_desc = row.get('Listing Long Description', '').strip()

                needs_scraping = any(
                    not val or val.upper() == 'N/A'
                    for val in [existing_email, existing_url, existing_short_desc, existing_long_desc]
                )

                if needs_scraping:
                    print(f"Scraping for: {listing_title}")
                    result = await scrape_listing(listing_title, listing_address)
                    result = json.loads(result)

                    if isinstance(result, dict):
                        op_data = result.get('data', [])
                    else:
                        op_data = []

                    new_email = op_data[0].get('listing_email', 'N/A') if op_data else 'N/A'
                    new_url = op_data[0].get('listing_url', 'N/A') if op_data else 'N/A'
                    new_short_desc = op_data[0].get('listing_short_description', 'N/A') if op_data else 'N/A'
                    new_long_desc = op_data[0].get('listing_long_description', 'N/A') if op_data else 'N/A'

                    listing_email = new_email if not existing_email or existing_email.upper() == 'N/A' else existing_email
                    listing_url = new_url if not existing_url or existing_url.upper() == 'N/A' else existing_url
                    listing_short_description = new_short_desc if not existing_short_desc or existing_short_desc.upper() == 'N/A' else existing_short_desc
                    listing_long_description = new_long_desc if not existing_long_desc or existing_long_desc.upper() == 'N/A' else existing_long_desc

                else:
                    print(f"Skipping (data exists): {listing_title}")
                    listing_email = existing_email
                    listing_url = existing_url
                    listing_short_description = existing_short_desc
                    listing_long_description = existing_long_desc

                # Write row
                writer.writerow([
                    listing_title, listing_email, listing_url, listing_address,
                    listing_short_description, listing_long_description
                ])

                print(f"✅ Saved: {listing_title}\n")

              #  Optional: Limit scrape for testing
                if count % 50 == 0:
                   break

        print("🎉 Scraping complete.")

# Entry point
if __name__ == "__main__":
    starting_line = int(input("Enter starting line: "))
    asyncio.run(main(starting_line))

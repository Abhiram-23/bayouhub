from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, SecretStr
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser_use import Agent, Controller,Browser, BrowserConfig
from dotenv import load_dotenv
load_dotenv()
import asyncio
import csv
import json


api_key = os.getenv("GEMINI_API_KEY")

class Post(BaseModel):
    listing_title: str
    listing_address: str
    listing_email:str
    listing_short_description: str
    listing_long_description: str
    listing_url: str


class Posts(BaseModel):
    data: List[Post]

controller = Controller(output_model=Posts)

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', api_key=SecretStr(os.getenv('GEMINI_API_KEY')))
browser = Browser(
    config=BrowserConfig(
        chrome_instance_path='C:\Program Files\Google\Chrome\Application\chrome.exe',  # macOS path
    )
)

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
        # initial_actions=initial_actions
    )
    result = await agent.run()
    return result.final_result()

async def main(start_line=1):
    csv_output_file = 'output.csv'
    csv_input_file = 'nightlife.csv'

    header = ['Listing Title', 'Listing Email', 'Listing URL', 'Listing Address', 'Listing Short Description', 'Listing Long Description']
    file_exists = os.path.isfile(csv_output_file)

    op = []
    data = []

    with open(csv_output_file, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        if not file_exists:
            writer.writerow(header)

        with open(csv_input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for count, row in enumerate(reader, start=1):
                if count < start_line:
                    continue  # skip until we reach the start line

                listing_title = row['Listing Title']
                listing_address = row['Listing Address']

                # Scrape listing info
                result = await scrape_listing(listing_title, listing_address)
                result = json.loads(result)

                if isinstance(result, dict):
                    op_data = result.get('data', [])
                else:
                    op_data = []

                op.append(result)
                print(f"Listing Title: {listing_title}, Result: {result}")

                listing_email = op_data[0].get('listing_email', 'N/A') if op_data else 'N/A'
                listing_url = op_data[0].get('listing_url', 'N/A') if op_data else 'N/A'
                listing_short_description = op_data[0].get('listing_short_description', 'N/A') if op_data else 'N/A'
                listing_long_description = op_data[0].get('listing_long_description', 'N/A') if op_data else 'N/A'

                data.append([
                    listing_title, listing_email, listing_url, listing_address,
                    listing_short_description, listing_long_description
                ])

                # Write every row immediately
                print(data, "data is appended=================================" * 5)
                writer.writerows(data)
                print(writer)
                data = []
                if count%200==0:
                    break

        print(op)


if __name__ == "__main__":
    starting_line = int(input("enter starting_line: "))
    asyncio.run(main(starting_line))

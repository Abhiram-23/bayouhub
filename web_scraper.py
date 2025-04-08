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

api_key = os.getenv("GEMINI_API_KEY")

class Post(BaseModel):
    listing_title: str
    listing_address: str
    listing_email:str
    listing_short_description: str
    listing_long_description: str
    listing_url: str


class Posts(BaseModel):
    posts: List[Post]

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

async def main():
    # Read the CSV file
    csv_file = 'nightlife.csv'
    op = []
    with open(csv_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        count = 0
        for row in reader:
            if count >= 10:
                break
            count += 1

            listing_title = row['Listing Title']
            listing_address = row['Listing Address']

            # Scrape listing info
            result = await scrape_listing(listing_title, listing_address)
            op.append(result)
            print(f"Listing Title: {listing_title}, Result: {result}")
        print(op)
if __name__ == "__main__":
    asyncio.run(main())

import time
import json
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse

# Base URL for Graduate Program
BASE_URL = "https://cs.unc.edu/graduate/"
visited_links = set()
data = []
unique_content = set()  # Track unique text to prevent duplicates

def setup_driver():
    """Sets up Selenium WebDriver"""
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_all_links(url, soup):
    """Extracts all internal links under /graduate/ only"""
    links = set()
    for a_tag in soup.find_all("a", href=True):
        full_url = urljoin(url, a_tag["href"])  # Convert relative to absolute URL
        if full_url.startswith(BASE_URL) and full_url not in visited_links:
            links.add(full_url)
    return links

def format_table_as_text(table):
    """Converts a Pandas DataFrame table into a readable string format"""
    formatted_table = []
    
    # Convert headers to strings
    headers = [str(h) for h in table.columns.tolist()]
    formatted_table.append(" | ".join(headers))  # Header row
    formatted_table.append("-" * len(" | ".join(headers)))  # Separator line
    
    # Convert each row to a string and append
    for _, row in table.iterrows():
        formatted_row = " | ".join(map(str, row.tolist()))  # Convert each row to a string
        formatted_table.append(formatted_row)
    
    return "\n".join(formatted_table)  # Convert list to a single formatted string

def scrape_page(url, driver):
    """Scrapes headings, text, lists, and tables from a given page URL"""
    if url in visited_links:
        return

    print(f"\n🔹 Scraping: {url}")
    visited_links.add(url)

    driver.get(url)
    time.sleep(5)  # Allow JavaScript to load fully

    soup = BeautifulSoup(driver.page_source, "html.parser")

    page_title = soup.title.text.strip() if soup.title else "No Title"

    # Extract headings and content properly
    page_content = []
    all_elements = soup.find_all(["h1", "h2", "h3", "p", "ul", "ol", "div", "table"])

    current_section = None
    for index, element in enumerate(all_elements):
        if element.name in ["h1", "h2", "h3"]:  # New heading found
            if current_section and current_section["content"]:  # Save only if content exists
                page_content.append(current_section)
            current_section = {"heading": element.text.strip(), "content": []}
        
        elif current_section and element.name in ["p", "ul", "ol", "div"]:  # Ensure content is collected correctly
            text = element.get_text(separator=" ").strip()
            if text and text not in unique_content:  
                current_section["content"].append(text)
                unique_content.add(text)

        elif current_section and element.name == "table":  # Table found
            try:
                df = pd.read_html(str(element))[0]  # Convert table to DataFrame
                table_text = format_table_as_text(df)  # Convert to readable text
                current_section["content"].append("\nTable:\n" + table_text)  # Append table under the current heading
            except ValueError:
                continue  # Skip if the table cannot be read properly

        # Stop collecting content when reaching another heading
        if index + 1 < len(all_elements) and all_elements[index + 1].name in ["h1", "h2", "h3"]:
            if current_section and current_section["content"]:  # Ensure content isn't empty
                page_content.append(current_section)
            current_section = None  # Stop collecting

    if current_section and current_section["content"]:  # Save last section if not empty
        page_content.append(current_section)

    # Extract links for further crawling
    page_links = get_all_links(url, soup)

    # Save extracted data
    data.append({
        "url": url,
        "title": page_title,
        "content": page_content  # No "links" field anymore
    })

    return page_links

def crawl_and_scrape(start_url):
    """Crawls only pages under /graduate/ and scrapes data"""
    driver = setup_driver()
    to_visit = {start_url}

    while to_visit:
        url = to_visit.pop()
        new_links = scrape_page(url, driver)
        to_visit.update(new_links - visited_links)  # Add new links only from /graduate/

    driver.quit()

    # 🔹 Remove entries with empty content
    cleaned_data = [page for page in data if any(section["content"] for section in page["content"])]

    # Save final cleaned data **without links**
    with open("unc_graduate_program_cleaned.json", "w", encoding="utf-8") as json_file:
        json.dump(cleaned_data, json_file, indent=4, ensure_ascii=False)

    print("\n✅ Finished scraping all graduate pages! Data saved to 'unc_graduate_program_cleaned.json'.")

# Start crawling at graduate program page
crawl_and_scrape(BASE_URL)

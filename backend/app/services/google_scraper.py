import asyncio
import random
from typing import List, Dict, Any, Optional
from googlesearch import search
from bs4 import BeautifulSoup
import httpx
from app.services.classifier import normalize_company

TIMEOUT = 30


async def search_google_for_companies(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    results = []
    
    try:
        for url in search(query, num_results=num_results, lang="pt"):
            if url:
                results.append({
                    "url": url,
                    "source": "google"
                })
    except Exception as e:
        pass
    
    return results


async def scrape_company_info(url: str) -> Optional[Dict[str, Any]]:
    await asyncio.sleep(random.uniform(1, 3))
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            
            title = soup.find("title")
            title_text = title.get_text().strip() if title else ""
            
            contact_info = {}
            
            email_patterns = [
                "mailto:", "@"
            ]
            
            for pattern in email_patterns:
                emails = soup.find_all("a", href=lambda x: x and pattern in x if x else False)
                for a in emails:
                    href = a.get("href", "")
                    if "@" in href and "mailto" in href:
                        email = href.split("mailto:")[-1].split("?")[0]
                        contact_info["email"] = email
                        break
            
            phone_patterns = [
                r"\+55\s*\d{2}\s*\d{4,5}-\d{4}",
                r"\(\d{2}\)\s*\d{4,5}-\d{4}",
                r"\d{2}\s*\d{4,5}-\d{4}"
            ]
            
            import re
            page_text = soup.get_text()
            for pattern in phone_patterns:
                match = re.search(pattern, page_text)
                if match:
                    contact_info["phone"] = match.group()
                    break
            
            return {
                "url": url,
                "title": title_text,
                "email": contact_info.get("email"),
                "phone": contact_info.get("phone"),
                "source": "google"
            }
    except Exception as e:
        return None


async def scrape_company_contacts(company_name: str, location: str = None) -> List[Dict[str, Any]]:
    query = company_name
    if location:
        query += f" {location}"
    query += " site:contato OR site:sobre OR site:email"
    
    search_results = await search_google_for_companies(query, num_results=5)
    
    contacts = []
    for result in search_results:
        company_info = await scrape_company_info(result["url"])
        if company_info:
            company_info["company"] = company_name
            contacts.append(company_info)
    
    return contacts


def get_corporate_email(name: str, domain: str = None) -> Optional[str]:
    if not domain:
        return None
    
    name_parts = name.lower().split()
    if len(name_parts) >= 2:
        email = f"{name_parts[0]}.{name_parts[-1]}@{domain}"
    elif len(name_parts) == 1:
        email = f"{name_parts[0]}@{domain}"
    else:
        return None
    
    return email
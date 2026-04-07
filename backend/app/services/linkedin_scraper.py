import asyncio
import random
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from app.core.settings import get_settings
from app.services.classifier import normalize_name

settings = get_settings()


async def create_stealth_browser():
    from playwright_stealth import stealth_async
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    
    await stealth_async(context)
    
    if settings.LINKEDIN_COOKIE_LI_AT:
        await context.add_cookies([
            {
                "name": "li_at",
                "value": settings.LINKEDIN_COOKIE_LI_AT,
                "domain": ".linkedin.com",
                "path": "/"
            }
        ])
    
    return playwright, browser


async def search_linkedin_profiles(query: str, target_role: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    if not settings.LINKEDIN_COOKIE_LI_AT:
        return []
    
    results = []
    
    try:
        playwright, browser = await create_stealth_browser()
        page = await browser.new_page()
        
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={query}"
        if target_role:
            search_url += f"%20{target_role}"
        
        await page.goto(search_url)
        await asyncio.sleep(random.uniform(3, 5))
        
        await page.wait_for_selector("ul.reusable-search__entity-list")
        
        for _ in range(min(limit, 5)):
            await page.mouse.wheel(0, 300)
            await asyncio.sleep(random.uniform(1, 2))
        
        profile_elements = await page.query_selector_all("li.reusable-search__result-container")
        
        for elem in profile_elements[:limit]:
            try:
                name_elem = await elem.query_selector("span.actor-name")
                name = await name_elem.inner_text() if name_elem else None
                
                role_elem = await elem.query_selector("div.entity-result__primary-subtitle")
                role = await role_elem.inner_text() if role_elem else None
                
                company_elem = await elem.query_selector("div.entity-result__secondary-subtitle")
                company = await company_elem.inner_text() if company_elem else None
                
                profile_link_elem = await elem.query_selector("a.app-aware-link")
                profile_url = await profile_link_elem.get_attribute("href") if profile_link_elem else None
                
                if name and profile_url:
                    profile_url = profile_url.split("?")[0]
                    
                    results.append({
                        "name": name,
                        "role": role,
                        "company": company,
                        "linkedin_url": profile_url,
                        "source": "linkedin"
                    })
            except Exception:
                continue
        
        await browser.close()
        await playwright.stop()
        
    except Exception as e:
        pass
    
    return results


async def get_linkedin_profile_details(profile_url: str) -> Optional[Dict[str, Any]]:
    if not settings.LINKEDIN_COOKIE_LI_AT:
        return None
    
    try:
        playwright, browser = await create_stealth_browser()
        page = await browser.new_page()
        
        await page.goto(profile_url)
        await asyncio.sleep(random.uniform(3, 5))
        
        about_elem = await page.query_selector("#about ~ div")
        about = await about_elem.inner_text() if about_elem else None
        
        experience_section = await page.query_selector("#experience ~ div")
        
        await browser.close()
        await playwright.stop()
        
        return {
            "about": about,
            "experience": experience_section is not None,
            "source": "linkedin"
        }
    except Exception:
        return None


def filter_by_role(profiles: List[Dict[str, Any]], target_role: str) -> List[Dict[str, Any]]:
    if not target_role:
        return profiles
    
    target_normalized = normalize_name(target_role)
    filtered = []
    
    for profile in profiles:
        role = profile.get("role", "")
        if role:
            role_normalized = normalize_name(role)
            if target_normalized in role_normalized or role_normalized in target_normalized:
                filtered.append(profile)
        else:
            filtered.append(profile)
    
    return filtered
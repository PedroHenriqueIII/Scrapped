import asyncio
import json
import uuid
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.settings import get_settings
from app.models.models import Search, DecisionMaker, SearchStatus
from app.services.classifier import classify_query
from app.services.receita_federal import search_by_cnpj, search_by_company_name, search_by_partner_name
from app.services.google_scraper import scrape_company_contacts, search_google_for_companies
from app.services.linkedin_scraper import search_linkedin_profiles, filter_by_role
from app.services.merger import merge_decision_makers

settings = get_settings()


async def scrape_rf_source(query: str, search_type: str) -> List[dict]:
    results = []
    
    if search_type == "company":
        if is_cnpj_format(query):
            rf_result = search_by_cnpj(query)
            if rf_result:
                results.append(rf_result)
        else:
            rf_results = search_by_company_name(query)
            results.extend(rf_results)
    
    elif search_type == "person":
        partners = search_by_partner_name(query)
        for p in partners:
            results.append({
                "name": query,
                "company": p.get("company_name"),
                "role": p.get("role"),
                "source": "rf"
            })
    
    return results


async def scrape_google_source(query: str, search_type: str) -> List[dict]:
    results = []
    
    if search_type == "company":
        companies = await search_google_for_companies(query, num_results=5)
        for company in companies:
            contacts = await scrape_company_contacts(query)
            for contact in contacts:
                results.append({
                    "company": query,
                    "email": contact.get("email"),
                    "phone": contact.get("phone"),
                    "source": "google"
                })
    
    elif search_type == "person":
        search_results = await search_google_for_companies(f'"{query}" LinkedIn', num_results=5)
        for result in search_results:
            results.append({
                "name": query,
                "linkedin_url": result.get("url"),
                "source": "google"
            })
    
    elif search_type == "vague":
        companies = await search_google_for_companies(query, num_results=10)
        for company in companies:
            results.append({
                "company": company.get("url"),
                "source": "google"
            })
    
    return results


async def scrape_linkedin_source(query: str, search_type: str, target_role: str = None) -> List[dict]:
    results = []
    
    if search_type in ["company", "person"]:
        profiles = await search_linkedin_profiles(query, target_role=target_role, limit=10)
        
        if target_role:
            profiles = filter_by_role(profiles, target_role)
        
        results.extend(profiles)
    
    return results


async def run_parallel_scraping(search_id: str, query: str, search_type: str, target_role: str = None):
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            result = await db.execute(select(Search).filter(Search.id == uuid.UUID(search_id)))
            search = result.scalar_one_or_none()
            if not search:
                return
            
            search.status = SearchStatus.PROCESSING
            await db.commit()
            
            if search_type == "vague":
                google_results = await search_google_for_companies(query, num_results=10)
                companies = [r.get("url", "").split("//")[-1].split("/")[0] for r in google_results if r.get("url")]
                
                all_results = []
                for company in companies[:5]:
                    company_results = await scrape_rf_source(company, "company")
                    all_results.extend(company_results)
                    
                    linkedin_results = await scrape_linkedin_source(company, "company", target_role)
                    all_results.extend(linkedin_results)
                
                results = all_results
            else:
                rf_task = scrape_rf_source(query, search_type)
                google_task = scrape_google_source(query, search_type)
                linkedin_task = scrape_linkedin_source(query, search_type, target_role)
                
                rf_results, google_results, linkedin_results = await asyncio.gather(
                    rf_task, google_task, linkedin_task
                )
                
                results = rf_results + google_results + linkedin_results
            
            for result_data in results:
                dm = DecisionMaker(
                    search_id=uuid.UUID(search_id),
                    name=result_data.get("name", ""),
                    role=result_data.get("role"),
                    company=result_data.get("company"),
                    email=result_data.get("email"),
                    phone=result_data.get("phone"),
                    linkedin_url=result_data.get("linkedin_url"),
                    sources=json.dumps(result_data.get("sources", [])),
                    confidence_score=result_data.get("confidence_score", 0.0)
                )
                db.add(dm)
            
            search.status = SearchStatus.COMPLETED
            search.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            try:
                result = await db.execute(select(Search).filter(Search.id == uuid.UUID(search_id)))
                search = result.scalar_one_or_none()
                if search:
                    search.status = SearchStatus.FAILED
                    await db.commit()
            except:
                pass
        finally:
            await db.close()


def is_cnpj_format(query: str) -> bool:
    import re
    cnpj_pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$'
    return bool(re.match(cnpj_pattern, query.strip()))


def process_search_task(search_id: str):
    asyncio.run(run_parallel_scraping_task(search_id))

async def run_parallel_scraping_task(search_id: str):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                __import__('sqlalchemy').select(Search).filter(Search.id == uuid.UUID(search_id))
            )
            search = result.scalar_one_or_none()
            if not search:
                return
            
            query = search.query
            search_type = search.search_type.value if search.search_type else "company"
            target_role = search.target_role
            
            await run_parallel_scraping(search_id, query, search_type, target_role)
            
        finally:
            await db.close()


from celery import Celery

celery_app = Celery(
    "scrapped",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.task(name="app.tasks.scraper.process_search_task")(process_search_task)
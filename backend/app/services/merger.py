from typing import List, Dict, Any
from rapidfuzz import fuzz
import json


def merge_decision_makers(results: List[Dict[str, Any]], target_role: str = None) -> List[Dict[str, Any]]:
    if not results:
        return []
    
    normalized_groups = group_by_similarity(results)
    
    merged = []
    for group in normalized_groups:
        merged_result = merge_group(group, target_role)
        if merged_result:
            merged.append(merged_result)
    
    merged.sort(key=lambda x: x["confidence_score"], reverse=True)
    return merged


def group_by_similarity(results: List[Dict[str, Any]], threshold: float = 85.0) -> List[List[Dict[str, Any]]]:
    from app.services.classifier import normalize_name, normalize_company
    
    groups = []
    used_indices = set()
    
    for i, result in enumerate(results):
        if i in used_indices:
            continue
        
        norm_name = normalize_name(result.get("name", ""))
        norm_company = normalize_company(result.get("company", ""))
        
        group = [result]
        used_indices.add(i)
        
        for j, other in enumerate(results):
            if j in used_indices:
                continue
            
            other_norm_name = normalize_name(other.get("name", ""))
            other_norm_company = normalize_company(other.get("company", ""))
            
            name_similarity = fuzz.ratio(norm_name, other_norm_name)
            company_similarity = fuzz.ratio(norm_company, other_norm_company) if norm_company and other_norm_company else 0
            
            if name_similarity >= threshold and company_similarity >= threshold:
                group.append(other)
                used_indices.add(j)
        
        groups.append(group)
    
    return groups


def merge_group(group: List[Dict[str, Any]], target_role: str = None) -> Dict[str, Any]:
    if not group:
        return None
    
    name = group[0].get("name")
    company = group[0].get("company")
    
    roles = [r.get("role") for r in group if r.get("role")]
    role = max(roles, key=lambda x: len(x)) if roles else None
    
    emails = [r.get("email") for r in group if r.get("email")]
    email = emails[0] if emails else None
    
    phones = [r.get("phone") for r in group if r.get("phone")]
    phone = phones[0] if phones else None
    
    linkedin_urls = [r.get("linkedin_url") for r in group if r.get("linkedin_url")]
    linkedin_url = linkedin_urls[0] if linkedin_urls else None
    
    sources = set()
    for r in group:
        src = r.get("sources", [])
        if isinstance(src, str):
            src = json.loads(src) if src else []
        sources.update(src)
    
    source_count = len(sources)
    confidence_score = source_count
    
    if target_role and role:
        target_normalized = target_role.lower().strip()
        role_normalized = role.lower().strip()
        if target_normalized in role_normalized or role_normalized in target_normalized:
            confidence_score += 0.5
    
    confidence_score = min(confidence_score, 3.5)
    
    return {
        "name": name,
        "role": role,
        "company": company,
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "sources": list(sources),
        "confidence_score": round(confidence_score, 2)
    }


def validate_cross_reference(group: List[Dict[str, Any]]) -> bool:
    companies = [r.get("company", "").lower() for r in group if r.get("company")]
    locations = [r.get("location", "").lower() for r in group if r.get("location")]
    
    if companies:
        return len(set(companies)) == 1
    
    if locations:
        return len(set(locations)) == 1
    
    return True
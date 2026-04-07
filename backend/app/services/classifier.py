import spacy
from langdetect import detect, LangDetectException

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("pt_core_news_lg")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "pt_core_news_lg"])
            _nlp = spacy.load("pt_core_news_lg")
    return _nlp


def classify_query(query: str) -> str:
    query_lower = query.strip().lower()
    
    if is_cnpj(query):
        return "company"
    
    try:
        lang = detect(query)
    except LangDetectException:
        lang = "pt"
    
    nlp = get_nlp()
    doc = nlp(query)
    
    has_person = any(ent.label_ == "PER" for ent in doc.ents)
    has_org = any(ent.label_ == "ORG" for ent in doc.ents)
    has_loc = any(ent.label_ in ["LOC", "GPE"] for ent in doc.ents)
    
    if has_person and not has_org:
        return "person"
    
    if has_org:
        return "company"
    
    if has_loc:
        return "location"
    
    if is_vague_query(query_lower):
        return "vague"
    
    return "company"


def is_cnpj(query: str) -> bool:
    import re
    cnpj_pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$'
    return bool(re.match(cnpj_pattern, query.strip()))


def is_vague_query(query: str) -> bool:
    vague_indicators = [
        "eventos", "restaurantes", "lojas", "advogados", "médicos",
        "dentistas", "academia", "escola", "hospital", "clínica",
        "empresa", "negócio", "comprar", "alugar", "serviços"
    ]
    return any(indicator in query for indicator in vague_indicators)


def normalize_name(name: str) -> str:
    from unidecode import unidecode
    name = name.lower().strip()
    name = unidecode(name)
    
    titles = ["dr.", "dr", "dra.", "dra", "sr.", "sr", "sra.", "sra", "prof.", "prof"]
    for title in titles:
        name = name.replace(f" {title}", " ").replace(f"{title} ", " ")
    
    return name.strip()


def normalize_company(company: str) -> str:
    from unidecode import unidecode
    company = company.lower().strip()
    company = unidecode(company)
    
    suffixes = ["ltda", "me", "ei", "eireli", "s.a.", "sa", "ltda."]
    for suffix in suffixes:
        company = company.replace(suffix, "").replace(f" {suffix}", "")
    
    return company.strip()
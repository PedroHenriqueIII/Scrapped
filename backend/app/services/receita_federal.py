import os
import sqlite3
from typing import Optional, List, Dict, Any
from app.core.settings import get_settings

settings = get_settings()


def get_cnpj_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.CNPJ_DB_PATH)
    if not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path)


def search_by_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    conn = get_cnpj_db_connection()
    if not conn:
        return None
    
    cnpj_clean = cnpj.replace(".", "").replace("-", "").replace("/", "")
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome, fantasia, municipio, uf, logradouro, numero, complemento, cep, telefone, email FROM empresas WHERE cnpj = ?",
            (cnpj_clean,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "name": row[0],
                "trade_name": row[1],
                "city": row[2],
                "state": row[3],
                "address": f"{row[4]}, {row[5]} {row[6] or ''}".strip(),
                "zip_code": row[7],
                "phone": row[8],
                "email": row[9],
                "source": "rf"
            }
    finally:
        conn.close()
    
    return None


def search_by_company_name(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_cnpj_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        search_term = f"%{name}%"
        
        cursor.execute(
            """SELECT cnpj, nome, fantasia, municipio, uf, logradouro, numero, telefone 
               FROM empresas WHERE nome LIKE ? OR fantasia LIKE ? LIMIT ?""",
            (search_term, search_term, limit)
        )
        
        results = []
        for row in cursor.fetchall():
            cnpj = row[0]
            cnpj_formatted = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
            
            results.append({
                "cnpj": cnpj_formatted,
                "name": row[1],
                "trade_name": row[2],
                "city": row[3],
                "state": row[4],
                "address": f"{row[5]}, {row[6]}" if row[6] else row[5],
                "phone": row[7],
                "source": "rf"
            })
    finally:
        conn.close()
    
    return results


def get_partners(cnpj: str) -> List[Dict[str, Any]]:
    conn = get_cnpj_db_connection()
    if not conn:
        return []
    
    cnpj_clean = cnpj.replace(".", "").replace("-", "").replace("/", "")
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome_socio, qualificacao FROM socios WHERE cnpj = ?",
            (cnpj_clean,)
        )
        
        partners = []
        for row in cursor.fetchall():
            partners.append({
                "name": row[0],
                "qualification": row[1],
                "source": "rf"
            })
    finally:
        conn.close()
    
    return partners


def search_by_partner_name(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_cnpj_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        search_term = f"%{name}%"
        
        cursor.execute(
            """SELECT e.cnpj, e.nome, e.fantasia, e.municipio, e.uf, s.qualificacao
               FROM socios s
               JOIN empresas e ON s.cnpj = e.cnpj
               WHERE s.nome_socio LIKE ?
               LIMIT ?""",
            (search_term, limit)
        )
        
        results = []
        for row in cursor.fetchall():
            cnpj = row[0]
            cnpj_formatted = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
            
            results.append({
                "cnpj": cnpj_formatted,
                "company_name": row[1],
                "trade_name": row[2],
                "city": row[3],
                "state": row[4],
                "role": row[5],
                "source": "rf"
            })
    finally:
        conn.close()
    
    return results
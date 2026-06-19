"""
utils/parser.py — Estrazione voci grezze da Excel
"""
import pandas as pd
import re
from io import BytesIOfrom typing import Optional

def _is_numeric(val):
    if val is None: return False
    if isinstance(val,(int,float)): return True
    if isinstance(val,str):
        val=val.replace(".","").replace(",",".").replace(" ","").replace("(","-").replace(")","")
        try: float(val); return True
        except: return False
    return False

def _to_float(val):
    if val is None: return None
    if isinstance(val,(int,float)): return float(val)
    if isinstance(val,str):
        val=val.strip(); neg=val.startswith("(") and val.endswith(")")
        val=val.replace("(","").replace(")","")
        if "," in val: val=val.replace(".","").replace(",",".")
        else: val=val.replace(",","")
        try: n=float(val); return -n if neg else n
        except: return None
    return None

def get_sheet_names(file_bytes):
    return pd.ExcelFile(BytesIO(file_bytes)).sheet_names

def parse_excel(file_bytes, sheet_name=None):
    buf = BytesIO(file_bytes)
    try: xl = pd.ExcelFile(buf)
    except Exception as e: raise ValueError(f"Impossibile leggere Excel: {e}")
    sheets = xl.sheet_names
    tgt = sheet_name or _select_sheet(sheets)
    df = xl.parse(tgt,header=None,dtype=str).fillna("")
    lines = _extract(df)
    if not lines:
        for s in sheets:
            if s == tgt: continue
            lines = _extract(xl.parse(s,header=None,dtype=str).fillna(""))
            if lines: break
    return lines

def _select_sheet(names):
    for n in names:
        nl = n.lower()
        if any(k in nl for k in ["bilancio","conto","stato","ce","sp","risult"]): return n
    return names[0]

def _extract(df):
    lines=[]; nc=df.shape[1]
    if nc<2: return lines
    cnts=sorted([(i,sum(1 for v in df.iloc[:,i] if _is_numeric(v) and v!="")) for i in range(nc)],key=lambda x:-x[1])
    vcols=[c[0] for c in cnts[:2] if c[1]>2]
    if not vcols: return lines
    vc=vcols[0]; dc=None
    for i in range(vc-1,-1,-1):
        if sum(1 for v in df.iloc[:,i] if isinstance(v,str) and len(v.strip())>2 and not _is_numeric(v))>3: dc=i; break
    if dc is None: dc=0
    cc=None
    if dc>0:
        for i in range(dc):
            if sum(1 for v in df.iloc[:,i] if isinstance(v,str) and re.match(r'^[A-Z0-9\.\/\-]{1,15}$',v.strip()))>3: cc=i; break
    cs=""
    for ri in range(df.shape[0]):
        dv=str(df.iloc[ri,dc]).strip(); nvr=str(df.iloc[ri,vc]).strip(); cv=str(df.iloc[ri,cc]).strip() if cc is not None else ""
        if not dv or dv="nan": continue
        du=dv.upper()
        if any(k in du for k in ["CONTO ECONOMICO","STATO PATRIMONIALE"]): cs="CE" if "CONTO" in du else "SP"; continue
        nv=_to_float(nvr)
        if nv is None: continue
        if nv==0 and len(dv)<5: continue
        lines.append({"raw_code":cv,"raw_description":dv,"raw_value":nv,"section_hint":cs})
    return lines

def parse_pdf(file_bytes):
    import pdfplumber; lines=[]
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row: continue
                    tc=[c for c in row if c and not _is_numeric(c)]; nc=[c for c in row if c and _is_numeric(c)]
                    if tc and nc: lines.append({"raw_code":"","raw_description":tc[0].strip(),"raw_value":_to_float(nc[-1]),"section_hint":""})
    return lines

import re

def get_year_str(year_abs):
    if year_abs < 1000: return f"{year_abs}.M41"
    else: return f"{year_abs - 1000:03d}.M42"

def parse_year(date_str):
    s = str(date_str).strip()
    if not s or s.lower() in ["alive", "dead", "nan", ""]: return None
    try:
        parts = s.split('.')
        y = int(parts[0])
        if len(parts) > 1 and "M42" in parts[1]: return 1000 + y
        return y
    except: return None

def get_ordinal(n):
    if 11 <= (n % 100) <= 13: suffix = 'th'
    else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def to_roman(n):
    if n <= 0: return ""
    num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
               (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    roman = ''
    for i, r in num_map:
        while n >= i:
            roman += r
            n -= i
    return roman
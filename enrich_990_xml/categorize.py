# categorize.py — deterministic 990 Part IX label -> ERA category (healthcare-extended).
# Ports enrich-990 v1 (TAG_MAP + KW + EXCLUDE) with:
#   RECONCILE : Occupancy + Conferences -> excluded; investment-mgmt + lobbying excluded
#               (eraLineItems wins); income/UBTI/excise tax excluded but property/sales tax -> 4.
#   HEALTHCARE: specific medical rules (pharmacy 33, medical-supply 31, transport 28) BEFORE
#               the broad clinical rule (32). 9 IDs verified vs spend_categories.
#   GRANULARITY: energy/electric -> 23 (not 22); merchant/credit-card -> 2 (not 3);
#               golf-course/greens -> 20 (Grounds).
# Deterministic + testable; no AI, no drift. categorize() -> (id, name) or None (excluded/unmapped).
import re

def normalize_label(raw):
    if not raw: return ''
    s = str(raw).lower().strip()
    s = re.sub(r'\s*\((?:line\s*)?\d+[a-z]?\)\s*$', '', s)
    s = re.sub(r'^fees for services\s*\(non-?employees\)\s*[-–:]\s*', '', s)
    s = re.sub(r'^fees for services\s*[-–:]\s*', '', s)
    s = re.sub(r'^other expenses\s*[-–:]\s*', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

EXCLUDED_EXACT = {'occupancy','royalties','bad debt expense','investment management fees','lobbying',
    'payments to affiliates','benefits paid to or for members','member relations'}
EXCLUDED_PREFIXES = ['salaries and wages','other salaries and wages','payroll taxes','employee benefits',
    'other employee benefits','pension plan accruals','compensation of current officers',
    'compensation not included above','depreciation, depletion','depreciation and amortization','interest',
    'grants and other assistance','payments of travel or entertainment expenses','investment management',
    'bad debt','provision for credit loss','credit loss','conferences, conventions','all other expenses','miscellaneous']
KW_EXCLUDE = re.compile(r'interest|deprecia|payroll|wage|salar|benefit|pension|scholar|grant|charit|donat|bad debt|cost of goods|inventory|amortiz|licenses? and permit', re.I)
INCOME_TAX  = re.compile(r'income tax|unrelated business.*tax|\bubti\b|excise tax|franchise tax', re.I)

def is_excluded(norm):
    if not norm: return False
    if norm in EXCLUDED_EXACT: return True
    if any(norm.startswith(p) for p in EXCLUDED_PREFIXES): return True
    if KW_EXCLUDE.search(norm): return True
    if INCOME_TAX.search(norm): return True
    return False

# healthcare — specific first (medical-supply/pharmacy/transport), broad clinical last.
# medical-supply BEFORE pharmacy: "drug & medical supplies" -> Supply(31), but bare
# "drug supplies"/"pharmaceuticals" (no "medical suppl") fall through to Pharmacy(33).
HEALTH = [
    (re.compile(r'medical suppl|med suppl|surgical suppl|clinical suppl|healthcare suppl|health care suppl|consumable|drug (and|&) medical|medical.*supplement|supplements', re.I), (31,'Medical Supply')),
    (re.compile(r'pharmac|\bdrug|vaccine|immuniz|\b340b\b|dispensing', re.I), (33,'Pharmacy')),
    (re.compile(r'transport|\bvehicle|\bfleet\b|mileage', re.I), (28,'Fleet Management')),
    (re.compile(r'medical|clinical|\bpatient|therap|nursing|diagnostic|health ?care service|purchased.*(medical|clinical|patient)|recovery cost|consultation and eval|examination', re.I), (32,'Medical Services')),
]
# granularity splits (before generic utilities/banking/golf)
GRAN = [
    (re.compile(r'energy|electric', re.I),        (23,'Energy / Electricity')),
    (re.compile(r'merchant|credit ?card', re.I),  (2, 'Merchant Card Services')),
    (re.compile(r'golf course|greens|ground|landscap|turf', re.I), (20,'Grounds/Landscaping')),
]
# standard Part IX groups
STD = [
    (re.compile(r'^insurance|risk management', re.I),                 (1, 'Insurance')),
    (re.compile(r'^office (expense|supplies)', re.I),                 (5, 'Office Supplies')),
    (re.compile(r'information technology|^it\b', re.I),               (14,'IT Hardware/Services')),
    (re.compile(r'advertis|marketing|promot', re.I),                  (10,'Marketing Services')),
    (re.compile(r'^travel', re.I),                                    (12,'Travel')),
]
# free-text KW (conference|meeting|dues removed from Travel; energy/merchant/golf handled above)
KW = [
    (re.compile(r'repair|mainten', re.I),                            (19,'Maintenance')),
    (re.compile(r'food|dining|kitchen|restaurant|cater|beverage|banquet|\bbar\b|f&b|dietar|hospitality|\bevent', re.I),(13,'Food Services')),
    (re.compile(r'insurance', re.I),                                 (1, 'Insurance')),
    (re.compile(r'telecom|telephone|communicat|internet|cable|answering service', re.I),(15,'Telecom')),
    (re.compile(r'utilit|\bgas\b|water|sewer|\bpower\b', re.I),      (22,'Utilities')),
    (re.compile(r'clean|janitor|housekeep|laundry', re.I),           (18,'Cleaning Services')),
    (re.compile(r'waste|trash|refuse|garbage|recycl|disposal|environmental control', re.I),(21,'Waste Management')),
    (re.compile(r'uniform|linen', re.I),                             (39,'Uniforms')),
    (re.compile(r'security|guard', re.I),                            (24,'Security Services')),
    (re.compile(r'pest|exterminat', re.I),                           (25,'Pest Control')),
    (re.compile(r'freight|shipping|deliver|cartage', re.I),          (26,'Freight (LTL/FTL)')),
    (re.compile(r'postage|mailing', re.I),                           (7, 'Mail Services')),
    (re.compile(r'print|reprograph', re.I),                          (6, 'Printing')),
    (re.compile(r'bank|processing fee|payment process', re.I),       (3, 'Banking Fees')),
    (re.compile(r'\btax', re.I),                                     (4, 'Taxes (Property/Sales)')),  # income/UBTI already excluded; before licens->SaaS
    (re.compile(r'software|licens|saas|subscription', re.I),         (16,'SaaS / Software')),
    (re.compile(r'chemical|fertilizer', re.I),                       (35,'Industrial Chemicals')),
    (re.compile(r'recruit|background', re.I),                        (41,'Background Checks')),
    (re.compile(r'golf|pro ?shop|tennis|pool|racquet|recreation', re.I),(34,'Operating Supply')),
    (re.compile(r'travel|lodging', re.I),                            (12,'Travel')),
    (re.compile(r'suppl(y|ies)|operating|equipment|\bmro\b', re.I),  (34,'Operating Supply')),
    (re.compile(r'office', re.I),                                    (5, 'Office Supplies')),
]
# fees-for-services family (checked on the RAW label before the normalize strip drops the
# phrase). NOT keyed on "11g" alone — that provenance token also appears in Schedule-O
# therapy detail lines, which must reach the clinical rule (32), not Professional(11).
FEES = re.compile(r'fees for services|professional fee|other fees for services|contracted service|consult|professional service|accounting|\baudit\b|\blegal\b|scientific advisory', re.I)
# freight beats fleet-transport when a shipping term is present ("shipping & transportation" -> Freight)
FREIGHT = re.compile(r'freight|shipping|cartage', re.I)

def categorize(label):
    n = normalize_label(label)
    if is_excluded(n): return None
    rawl = str(label or '').lower()
    if FEES.search(rawl): return (11, 'Professional Services')
    if FREIGHT.search(n): return (26, 'Freight (LTL/FTL)')
    for rx,cat in HEALTH:
        if rx.search(n): return cat
    for rx,cat in GRAN:
        if rx.search(n): return cat
    for rx,cat in STD:
        if rx.search(n): return cat
    for rx,cat in KW:
        if rx.search(n): return cat
    return None

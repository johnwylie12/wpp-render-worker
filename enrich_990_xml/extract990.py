# extract990.py — pure 990 Part IX extractor.
# Fetches an IRS 990 e-file XML from the GivingTuesday 990 Data Lake (a live mirror of the
# IRS e-file corpus, keyed by object_id — the frozen AWS irs-form-990 bucket is dead), parses
# Part IX (Statement of Functional Expenses) + headline revenue/expenses, and maps each object-
# expense line to an ERA spend category via the validated categorize.py mapper. No DB, no I/O
# beyond the XML fetch. Reproduces Carmel CC to the dollar (addressable $5,383,682).
import urllib.request
import xml.etree.ElementTree as ET
from categorize import categorize  # same directory

GT_XML = "https://gt990datalake-rawdata.s3.amazonaws.com/EfileData/XmlFiles/{}_public.xml"

def _local(tag):
    return tag.split("}", 1)[-1]

# Part IX standard object-expense groups -> readable IRS label (fed to categorize()).
PARTIX_GROUPS = {
    "CompCurrentOfcrDirectorsGrp": "Compensation of current officers, directors, trustees, and key employees",
    "CompDisqualPersonsGrp": "Compensation of disqualified persons",
    "OtherSalariesAndWagesGrp": "Other salaries and wages",
    "PensionPlanContriGrp": "Pension plan accruals and contributions",
    "OtherEmployeeBenefitsGrp": "Other employee benefits",
    "PayrollTaxesGrp": "Payroll taxes",
    "FeesForServicesManagementGrp": "Fees for services (non-employees) - management",
    "FeesForServicesLegalGrp": "Fees for services - legal",
    "FeesForServicesAccountingGrp": "Fees for services - accounting",
    "FeesForServicesLobbyingGrp": "Fees for services - lobbying",
    "FeesForSrvcInvstMgmntFeesGrp": "Investment management fees",
    "FeesForServicesInvstMgmntFees": "Investment management fees",
    "FeesForServicesOtherGrp": "Fees for services (non-employees) - other (line 11g)",
    "AdvertisingGrp": "Advertising and promotion",
    "OfficeExpensesGrp": "Office expenses",
    "InformationTechnologyGrp": "Information technology",
    "RoyaltiesGrp": "Royalties",
    "OccupancyGrp": "Occupancy",
    "TravelGrp": "Travel",
    "PymtTravelEntrtnmntPublicOfclGrp": "Payments of travel or entertainment expenses for public officials",
    "ConferencesMeetingsGrp": "Conferences, conventions, and meetings",
    "InterestGrp": "Interest",
    "PaymentsToAffiliatesGrp": "Payments to affiliates",
    "DepreciationDepletionGrp": "Depreciation, depletion, and amortization",
    "InsuranceGrp": "Insurance",
    "AllOtherExpensesGrp": "All other expenses",
}

def _amt(grp):
    for c in grp:
        if _local(c.tag) == "TotalAmt":
            try:
                return int(c.text)
            except (TypeError, ValueError):
                return 0
    return 0

def fetch_xml(object_id, timeout=40):
    with urllib.request.urlopen(GT_XML.format(object_id), timeout=timeout) as r:
        return r.read()

def parse_partix(xml_bytes):
    """Return {total_revenue, total_expenses, items:[(label, amount)]} or None if no IRS990."""
    root = ET.fromstring(xml_bytes)
    irs990 = None
    for el in root.iter():
        if _local(el.tag) == "IRS990":
            irs990 = el
            break
    if irs990 is None:
        return None

    def find_text(name):
        for el in irs990.iter():
            if _local(el.tag) == name and el.text:
                return el.text
        return None

    tot_rev = find_text("CYTotalRevenueAmt")
    tot_exp = find_text("CYTotalExpensesAmt")
    items = []
    for child in irs990:
        lt = _local(child.tag)
        if lt in PARTIX_GROUPS:
            a = _amt(child)
            if a:
                items.append((PARTIX_GROUPS[lt], a))
        elif lt == "FeesForServicesProfFundraising":
            a = _amt(child)
            if a:
                items.append(("Fees for services - professional fundraising", a))
        elif lt == "OtherExpensesGrp":
            desc, a = None, 0
            for gc in child:
                gl = _local(gc.tag)
                if gl == "Desc" and gc.text:
                    desc = gc.text.strip()
                elif gl == "TotalAmt":
                    try:
                        a = int(gc.text)
                    except (TypeError, ValueError):
                        a = 0
            if desc and a:
                items.append(("Other expenses - " + desc, a))
    return {"total_revenue": int(tot_rev) if tot_rev else None,
            "total_expenses": int(tot_exp) if tot_exp else None,
            "items": items}

def categorize_lines(items):
    """items -> (line_items[], addressable). line_items carry era_category_id/name (or null)."""
    line_items = []
    addressable = 0
    for label, amt in items:
        cat = categorize(label)
        if cat:
            addressable += amt
            line_items.append({"label": label, "amount": amt, "era_category_id": cat[0],
                               "era_category_name": cat[1], "note": "Part IX mapped", "estimated": False})
        else:
            line_items.append({"label": label, "amount": amt, "era_category_id": None,
                               "era_category_name": None, "note": "excluded/unmapped", "estimated": False})
    return line_items, addressable

def opportunity(line_items, rates):
    """rates: {category_id: (low_pct, high_pct)}. Returns (low, high) dollars."""
    low = high = 0.0
    for li in line_items:
        cid = li.get("era_category_id")
        if cid is not None and cid in rates:
            lo, hi = rates[cid]
            low += li["amount"] * lo / 100.0
            high += li["amount"] * hi / 100.0
    return round(low), round(high)

def extract(object_id, rates, timeout=40):
    """Full extract for one filing. Returns a result dict (never raises on fetch/parse)."""
    out = {"object_id": object_id, "ok": False, "reason": None,
           "total_revenue": None, "total_expenses": None, "addressable": 0,
           "opportunity_low": 0, "opportunity_high": 0, "line_items": []}
    try:
        xml_bytes = fetch_xml(object_id, timeout=timeout)
    except Exception as e:
        out["reason"] = "xml_fetch_%s" % type(e).__name__
        return out
    try:
        p = parse_partix(xml_bytes)
    except Exception as e:
        out["reason"] = "parse_%s" % type(e).__name__
        return out
    if not p:
        out["reason"] = "no_irs990"
        return out
    line_items, addressable = categorize_lines(p["items"])
    out["total_revenue"] = p["total_revenue"]
    out["total_expenses"] = p["total_expenses"]
    out["line_items"] = line_items
    out["addressable"] = addressable
    if addressable == 0:
        out["reason"] = "no_mappable_partix"
        return out
    out["opportunity_low"], out["opportunity_high"] = opportunity(line_items, rates)
    out["ok"] = True
    return out

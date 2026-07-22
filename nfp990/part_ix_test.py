#!/usr/bin/env python3
"""Offline checks for the Part IX -> ERA categorizer. Run: python nfp990/part_ix_test.py

Dependency-free (no pytest): asserts + a __main__ that exits non-zero on failure,
so it runs in the worker image and in CI without extra packages.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from part_ix import extract_part_ix, category_rollups, map_free_text  # noqa: E402

# Synthetic IRS 990 XML: efile default namespace, tags unprefixed (as real filings
# are), covering a standard Part IX line, an excluded personnel line, two line-24
# free-text lines (one mapped, one unmapped), and Part VII people + signer.
SAMPLE = """<Return xmlns="http://www.irs.gov/efile">
 <ReturnHeader>
  <TaxYr>2023</TaxYr>
  <Filer><EIN>250965460</EIN></Filer>
  <BusinessOfficerGrp><PersonNm>Jane Smith</PersonNm><PersonTitleTxt>Chief Financial Officer</PersonTitleTxt><SignatureDt>2024-05-15</SignatureDt></BusinessOfficerGrp>
 </ReturnHeader>
 <ReturnData>
  <IRS990>
   <CYTotalRevenueAmt>79446966</CYTotalRevenueAmt>
   <CYTotalExpensesAmt>78000000</CYTotalExpensesAmt>
   <CompensationOfCurrentOfficersGrp><TotalAmt>1306483</TotalAmt></CompensationOfCurrentOfficersGrp>
   <InsuranceGrp><TotalAmt>2905000</TotalAmt></InsuranceGrp>
   <OccupancyGrp><TotalAmt>4000000</TotalAmt></OccupancyGrp>
   <FeesForServicesManagementGrp><TotalAmt>1500000</TotalAmt></FeesForServicesManagementGrp>
   <OtherExpensesGrp><Desc>Utilities and electric</Desc><TotalAmt>1200000</TotalAmt></OtherExpensesGrp>
   <OtherExpensesGrp><Desc>Miscellaneous other</Desc><TotalAmt>500000</TotalAmt></OtherExpensesGrp>
   <Form990PartVIISectionAGrp><PersonNm>John Doe</PersonNm><TitleTxt>President and CEO</TitleTxt></Form990PartVIISectionAGrp>
   <Form990PartVIISectionAGrp><PersonNm>Jane Smith</PersonNm><TitleTxt>CFO</TitleTxt></Form990PartVIISectionAGrp>
  </IRS990>
 </ReturnData>
</Return>"""

FAILS: list[str] = []
def check(cond, msg):
    if not cond:
        FAILS.append(msg)

r = extract_part_ix(SAMPLE)

# Header / filed totals
check(r["ein"] == "250965460", f"ein {r['ein']}")
check(r["tax_year"] == 2023, f"tax_year {r['tax_year']}")
check(r["total_revenue"] == 79446966, f"total_revenue {r['total_revenue']}")
check(r["total_expenses"] == 78000000, f"total_expenses {r['total_expenses']}")

# Line items by category id
by_cat: dict = {}
for it in r["line_items"]:
    by_cat.setdefault(it["era_category_id"], []).append(it)
check(any(i["amount"] == 2905000 for i in by_cat.get(1, [])), "Insurance 2,905,000 -> cat 1")
check(any(i["amount"] == 1500000 for i in by_cat.get(11, [])), "FeesForServicesManagement -> Professional Services 11")
check(any(i["amount"] == 4000000 for i in by_cat.get(22, [])), "Occupancy -> Utilities 22")
check(any(i["amount"] == 1200000 for i in by_cat.get(22, [])), "Other 'Utilities and electric' -> Utilities 22")
# Excluded personnel line present but uncategorized
check(any(i["amount"] == 1306483 and i["era_category_id"] is None for i in by_cat.get(None, [])), "officer comp excluded (null cat)")
# Unmapped free text present but uncategorized
check(any(i["amount"] == 500000 and i["era_category_id"] is None for i in by_cat.get(None, [])), "'Miscellaneous other' unmapped (null cat)")

# Addressable = sum of mapped only: 2.905M + 4M + 1.5M + 1.2M = 9.605M
check(r["addressable_spend"] == 9605000, f"addressable_spend {r['addressable_spend']} (want 9,605,000)")

# Rollups: Utilities(22) aggregates Occupancy + free-text = 5.2M and ranks first
rolls = category_rollups(r["line_items"])
top = rolls[0]
check(top["spend_category_id"] == 22 and top["spend_amount"] == 5200000, f"top rollup {top}")
check({rr["spend_category_id"] for rr in rolls} == {1, 11, 22}, f"rollup cats {[rr['spend_category_id'] for rr in rolls]}")

# Part VII officers + signer (buyer cross-check)
names = {o["name"] for o in r["officers"]}
check("John Doe" in names and "Jane Smith" in names, f"officers {r['officers']}")
check(r["signing_officer"] and r["signing_officer"]["name"] == "Jane Smith", f"signer {r['signing_officer']}")

# map_free_text guardrails
check(map_free_text("Interest on bonds")[0] is None, "interest excluded")
check(map_free_text("Janitorial cleaning")[0] == 18, "cleaning -> 18")

if FAILS:
    print("FAIL:")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print(f"OK - part_ix: {len(r['line_items'])} line items, addressable ${r['addressable_spend']:,}, "
      f"{len(rolls)} categories, {len(r['officers'])} officers, signer={r['signing_officer']['name']}")

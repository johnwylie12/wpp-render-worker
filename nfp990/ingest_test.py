#!/usr/bin/env python3
"""Offline checks for the ingestion parse + ERA categorize bridge.
Run: python nfp990/ingest_test.py   (needs lxml; no DB, no network)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingest import parse_part_ix, era_categorize, PARTIX_ELEMENTS, KEY_TO_TAG  # noqa: E402
from part_ix import TAG_MAP, category_rollups  # noqa: E402

SAMPLE = b"""<Return xmlns="http://www.irs.gov/efile">
 <ReturnHeader>
  <TaxYr>2023</TaxYr>
  <ReturnTypeCd>990</ReturnTypeCd>
  <Filer><EIN>23-7825575</EIN></Filer>
  <BusinessOfficerGrp><PersonNm>Alex Chen</PersonNm><PersonTitleTxt>CFO</PersonTitleTxt></BusinessOfficerGrp>
 </ReturnHeader>
 <ReturnData>
  <IRS990>
   <CYTotalRevenueAmt>500000000</CYTotalRevenueAmt>
   <CYTotalExpensesAmt>480000000</CYTotalExpensesAmt>
   <CompCurrentOfcrDirectorsGrp><TotalAmt>2000000</TotalAmt></CompCurrentOfcrDirectorsGrp>
   <InsuranceGrp><TotalAmt>3000000</TotalAmt></InsuranceGrp>
   <OccupancyGrp><TotalAmt>5000000</TotalAmt></OccupancyGrp>
   <FeesForServicesManagementGrp><TotalAmt>1500000</TotalAmt></FeesForServicesManagementGrp>
   <OtherExpensesGrp><Desc>Software licenses and subscriptions</Desc><TotalAmt>900000</TotalAmt></OtherExpensesGrp>
   <OtherExpensesGrp><Desc>Miscellaneous program costs</Desc><TotalAmt>400000</TotalAmt></OtherExpensesGrp>
   <TotalFunctionalExpensesGrp><TotalAmt>480000000</TotalAmt></TotalFunctionalExpensesGrp>
   <Form990PartVIISectionAGrp><PersonNm>Dana Lee</PersonNm><TitleTxt>Chair</TitleTxt></Form990PartVIISectionAGrp>
  </IRS990>
 </ReturnData>
</Return>"""

FAILS: list[str] = []
def check(c, m):
    if not c:
        FAILS.append(m)

# 0) every part_ix.TAG_MAP tag is reachable from the lxml element set (categorizer reuse is complete)
for tag in TAG_MAP:
    check(tag in PARTIX_ELEMENTS, f"TAG_MAP tag {tag} not parsed by lxml element set")

# 1) parse
p = parse_part_ix(SAMPLE)
check(p["ein"] == "237825575", f"ein zfilled from dashed: {p['ein']}")
check(p["tax_year"] == "2023", f"tax_year {p['tax_year']}")
check(p["return_type"] == "990", f"return_type {p['return_type']}")
check(p["total_revenue"] == 500000000, f"total_revenue {p['total_revenue']}")
check(p["line_items"].get("insurance") == 3000000, f"insurance raw {p['line_items'].get('insurance')}")
check(p["line_items"].get("occupancy") == 5000000, f"occupancy raw {p['line_items'].get('occupancy')}")
check(p["line_items"].get("comp_officers") == 2000000, f"comp raw {p['line_items'].get('comp_officers')}")
check(len(p["other_expenses"]) == 2, f"other_expenses {p['other_expenses']}")

# 2) era_categorize — reuse the categorizer rules
items = era_categorize(p["line_items"], p["other_expenses"])
by_cat: dict = {}
for it in items:
    by_cat.setdefault(it["era_category_id"], []).append(it)
check(any(i["amount"] == 3000000 for i in by_cat.get(1, [])), "insurance -> cat 1")
check(any(i["amount"] == 5000000 for i in by_cat.get(22, [])), "occupancy -> Utilities 22")
check(any(i["amount"] == 1500000 for i in by_cat.get(11, [])), "fees_management -> Professional Services 11")
check(any(i["amount"] == 900000 for i in by_cat.get(16, [])), "Other 'Software licenses' -> SaaS/Software 16")
check(any(i["amount"] == 2000000 and i["era_category_id"] is None for i in by_cat.get(None, [])), "officer comp excluded")
check(any(i["amount"] == 400000 and i["era_category_id"] is None for i in by_cat.get(None, [])), "misc unmapped")

addressable = sum(i["amount"] for i in items if i["era_category_id"])
check(addressable == 3000000 + 5000000 + 1500000 + 900000, f"addressable {addressable}")

rolls = category_rollups(items)
check({r["spend_category_id"] for r in rolls} == {1, 22, 11, 16}, f"rollup cats {[r['spend_category_id'] for r in rolls]}")
check(rolls[0]["spend_category_id"] == 22, f"top rollup should be Utilities: {rolls[0]}")

if FAILS:
    print("FAIL:")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print(f"OK - ingest: parsed {len(p['line_items'])} Part IX lines, categorized to {len(rolls)} ERA categories, "
      f"addressable ${addressable:,}")

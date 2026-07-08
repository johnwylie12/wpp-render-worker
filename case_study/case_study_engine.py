#!/usr/bin/env python3
"""
Case Study one-pager engine (portrait, WPP package house style).

Reusable: mirrors the worker's cover_page_engine pattern. To add a study,
append a dict to STUDIES (or call render_one(data, out_pdf) directly).

Data schema per study:
  slug, title, client, challenge, solution, result,
  total_label, total,
  categories: [ {name, amount, pct?} ]      # OR
  category_list: [ "Cat A", "Cat B", ... ]  # when no per-category $ is disclosed
  quote, attrib

Fonts (Lora + Poppins) and the ERA blue lockup are base64-embedded from ./assets
so the container needs no system fonts (same reason the cover embeds them).
"""
import base64, os, sys
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONTS = os.path.join(ASSETS, "fonts")

def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

_TPL = Template(open(os.path.join(HERE, "case_study_template.html")).read())
_ENV = {
    "lora_b64":  _b64(os.path.join(FONTS, "Lora.ttf")),
    "pop_r_b64": _b64(os.path.join(FONTS, "Poppins-Regular.ttf")),
    "pop_sb_b64":_b64(os.path.join(FONTS, "Poppins-SemiBold.ttf")),
    "pop_b_b64": _b64(os.path.join(FONTS, "Poppins-Bold.ttf")),
    "logo_b64":  _b64(os.path.join(ASSETS, "era_logo.png")),
}

def render_one(data, out_pdf):
    html = _TPL.render(**_ENV, **data)
    HTML(string=html).write_pdf(out_pdf)
    return out_pdf

# --------------------------------------------------------------------------
STUDIES = [
 {"slug":"one_community_health",
  "title":"ERA optimizes One Community Health\u2019s costs as they continue providing optimal care",
  "client":"One Community Health, in Sacramento, California, with a primary focus on serving people with HIV/AIDS.",
  "challenge":"When the clinic underwent a leadership change, one of the new CEO\u2019s priorities was to improve operational efficiency. Having experienced ERA\u2019s services as a senior executive at another health center, the CEO knew the cost savings and added value ERA brings could be substantial.",
  "solution":"After analyzing 11 cost categories, ERA specialists found seven where savings could be realized \u2014 uncovering $645,583 in annual savings, while the remaining four were validated as already running optimally. Re-negotiating bundled services with the reference lab provider saves over $102,000 annually, and the review surfaced an additional $65,000 in billing credits. Shifting same-day prescription delivery from the national incumbent to a qualified local courier improved service and saved over $110,000 a year.",
  "result":"With the realized savings and continuity of leadership, One Community Health can redeploy funds to further its mission and provide essential care to underserved members of the Sacramento community.",
  "total_label":"Total annual savings realized","total":"$645,583",
  "categories":[{"name":"Reference lab services","amount":"$187,160"},
                {"name":"Language translation","amount":"$158,226"},
                {"name":"Small parcel delivery","amount":"$120,253"},
                {"name":"Medical supplies","amount":"$83,215"},
                {"name":"Office & janitorial supplies","amount":"$38,050"},
                {"name":"Waste management","amount":"$36,367"},
                {"name":"Telecommunications","amount":"$11,726"},
                {"name":"Staff services","amount":"$6,800"},
                {"name":"Dental supplies","amount":"$3,786"}],
  "quote":"Our work with ERA has allowed us to ensure we get the maximum value possible with every dollar spent. The savings we\u2019ve enjoyed have helped offset the cost of a recent organization-wide wage adjustment keeping us competitive in a challenging labor market.",
  "attrib":"Michelle Monroe, CEO, One Community Health"},

 {"slug":"north_texas_food_bank",
  "title":"North Texas Food Bank saves more than $200K",
  "client":"The North Texas Food Bank (NTFB) is a nonprofit serving the hungry across 13 counties in North Texas, through initiatives including The Community Kitchen and Food 4 Kids.",
  "challenge":"To sustain and expand its programs, NTFB needed to reduce operational costs \u2014 particularly in food services and packaging \u2014 without compromising quality or availability, uncovering hidden savings that could be redirected toward feeding more people in need.",
  "solution":"ERA conducted a comprehensive review of NTFB\u2019s food and packaging spend. For food services, category specialists built a detailed \u201cmarket basket\u201d RFP covering meat and seafood, dry groceries, frozen goods, produce, and refrigerated dairy \u2014 structured for competitive bidding and tying supplier pricing to raw-material costs to protect NTFB from price swings. In packaging, a thorough RFP drove improved pricing, better inventory management, and enhanced service, with suppliers evaluated on service and operational fit, not cost alone.",
  "result":"ERA helped NTFB achieve over $200,000 in annual savings \u2014 more than $15,000 per hour in food and $13,000 per hour in packaging in identified hidden savings \u2014 enabling NTFB to reinvest in its mission of delivering more meals across pantries, shelters, senior centers, and after-school programs.",
  "total_label":"Total annual savings realized","total":"$200,500",
  "categories":[{"name":"Food services","amount":"$120,500","pct":"12.5%"},
                {"name":"Packaging","amount":"$80,000","pct":"38%"}],
  "quote":"ERA\u2019s savings were huge.",
  "attrib":"Ann Dunlap, Child Programs Coordinator, North Texas Food Bank"},

 {"slug":"methodist_retirement_communities",
  "title":"ERA Group helps senior retirement community save nearly $300K annually",
  "client":"Methodist Retirement Communities (MRC) is a nonprofit, faith-based senior living provider operating in Texas, with six established locations and recent expansion into Corpus Christi and Fort Worth.",
  "challenge":"Despite strong internal expense management, MRC needed external expertise to keep operations best-in-class during a period of rapid growth, with limited time and resources to identify cost-saving opportunities.",
  "solution":"ERA conducted a comprehensive analysis of MRC\u2019s spending \u2014 even in areas already reduced \u2014 finding savings across multiple categories and improving operational efficiency. Although MRC already leveraged a Group Purchasing Organization (GPO), ERA further improved the terms and conditions of that relationship, delivering unexpected value without disrupting existing vendor ties.",
  "result":"In its first year working with ERA, MRC uncovered nearly $300,000 in annualized savings across six key spend categories, allowing leaders to reinvest dollars into patient care programs.",
  "total_label":"Total annual savings realized","total":"$285,250",
  "categories":[{"name":"Pharmaceuticals","amount":"$112,000","pct":"21%"},
                {"name":"Medical supplies","amount":"$76,000","pct":"13%"},
                {"name":"Cleaning supplies","amount":"$34,000","pct":"15.1%"},
                {"name":"Linen rentals","amount":"$33,000","pct":"18.5%"},
                {"name":"Food","amount":"$22,000","pct":"4%"},
                {"name":"Office supplies","amount":"$8,250","pct":"10.8%"}],
  "quote":"We manage expenses well, so I thought ERA would be wasting their time and quite possibly mine. Honestly, I was surprised and pleased by the amount of additional cash that has fallen to our bottom line beyond what we had found ourselves.",
  "attrib":"Don Stephens, CFO, Methodist Retirement Communities"},

 {"slug":"delaware_hospice",
  "title":"$3.5 Million saved for Delaware Hospice",
  "client":"Delaware Hospice is the largest nonprofit provider of hospice, palliative, and transitional care to patients throughout Delaware and parts of southeastern Pennsylvania.",
  "challenge":"Though fiscally responsible, leadership wanted to ensure they were receiving the greatest possible value from contracted providers. Rising costs across medical supplies, pharmaceuticals, administrative services, and telecommunications pressured resources that could otherwise go to patient care \u2014 a pressing example being an answering service that struggled with accuracy and was set to raise prices.",
  "solution":"ERA experts conducted a comprehensive review of Delaware Hospice\u2019s expense base, working closely with financial and clinical staff across medical supplies, ambulance services, durable medical equipment, IV therapy, pharmaceuticals, payroll/HR administration, landscaping, snow removal, and telecommunications. For the answering service specifically, ERA identified a higher-quality provider at a lower cost, and Delaware Hospice transitioned to one that better met its needs.",
  "result":"ERA delivered $3.5 million in total savings \u2014 captured across both large-scale and niche expense areas \u2014 providing significant additional cash flow to reinvest in patient care and expand its impact in the community.",
  "total_label":"Total annual savings realized","total":"$3,500,000",
  "category_list":["Medical Supplies","Ambulance Svc & Durable Med Equipment",
                   "IV Therapy & Pharmacy Benefit Management","Landscaping, Snow Removal & Payroll",
                   "HR Administration","Answering Services"],
  "quote":"ERA has assisted us in saving over $3M in reviewing over a dozen expense categories. They provide expertise in all these areas & assist us in operational areas beyond cost savings. The relationship has been outstanding. I would highly recommend other organizations that struggle with cost control, taking advantage of their services.",
  "attrib":"Michelle Burris, CFO (2016\u20132021), Delaware Hospice"},

 {"slug":"catholic_charities_denver",
  "title":"ERA\u2019s hybrid savings model helps Catholic Charities of Denver put millions toward its mission",
  "client":"Catholic Charities \u2013 Archdiocese of Denver (\u201cCCD\u201d) turned to ERA to challenge and revamp its housing and ministry facilities management \u2014 centralizing processes and buying power across the agency. With ERA\u2019s guidance, CCD is employing a novel hybrid service model estimated to yield roughly 30% per-annum savings over the next decade.",
  "challenge":"A lack of centralized internal labor and external procurement practices kept CCD from scaling services, consolidating vendors, increasing efficiency \u2014 and saving money.",
  "solution":"ERA created a hybrid internal facilities-management model to oversee vendors and internal labor while maintaining strict service standards.",
  "result":"CCD is positioned to realize maximum efficiencies and 30%+ per-annum savings in its housing ministry alone \u2014 spurring it to ask ERA to expand its footprint across the organization.",
  "total_label":"Total annual savings realized","total":"$1,116,000",
  "categories":[{"name":"IFM","amount":"$620,000"},
                {"name":"Maintenance / repairs","amount":"$116,000"},
                {"name":"Food services","amount":"$103,600"},
                {"name":"Telecomm","amount":"$93,600"},
                {"name":"Waste management","amount":"$56,700"},
                {"name":"Office & janitorial supplies","amount":"$54,000"},
                {"name":"Energy / utilities","amount":"$30,700"},
                {"name":"Information technology","amount":"$30,000"},
                {"name":"Print & promotional","amount":"$11,400"}],
  "quote":"ERA provided us a huge opportunity to further our mission by taking the resources we have been given and allowing us to redeploy savings into additional high-impact programming.",
  "attrib":"Phil Vottiero, CFO of CCD"},

 {"slug":"bethesda_health_group",
  "title":"Bethesda Health Group saves $128K annually by partnering with ERA Group",
  "client":"Bethesda Health Group is a premier nonprofit senior care provider based in St. Louis, operating nine facilities across independent and assisted living, skilled nursing and memory care, rehabilitation, therapy, hospice, and home healthcare.",
  "challenge":"Bethesda sought a partner to deliver meaningful, sustainable funding by reducing overhead \u2014 and to bring best practices in vendor selection and management tailored to its unique expenses.",
  "solution":"ERA Group (formerly Expense Reduction Analysts) analyzed diverse overhead categories and applied category-specific expertise, delivering sustainable savings, trusted-advisor guidance, and simplified, standardized supplier-management processes.",
  "result":"Bethesda achieved sustained improvements in pricing and vendor service while saving over $128,860 annually across four key spend categories. Beyond financial savings, ERA\u2019s support enhanced efficiency, vendor relationships, and operational effectiveness.",
  "total_label":"Total annual savings realized","total":"$128,860",
  "categories":[{"name":"Hospice pharmaceuticals","amount":"$52,160","pct":"32%"},
                {"name":"Food services","amount":"$34,700","pct":"27%"},
                {"name":"Payroll","amount":"$26,500","pct":"17%"},
                {"name":"Office supplies","amount":"$15,500","pct":"18%"}],
  "quote":"Saving time, saving money, better service from vendors; ERA was instrumental in helping us achieve the trifecta! What company would not appreciate that?",
  "attrib":"Bethesda Health Group Leadership"},
]

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    for s in STUDIES:
        p = os.path.join(out_dir, f"CaseStudy_{s['slug']}.pdf")
        render_one(s, p)
        print("wrote", p)

# ---------------------------------------------------------------------------
# TAGGING — which prospect "vertical" each study supports, so the package
# builder can auto-include the right study(ies). Vertical keys match the cover
# hero / coverVertical() keys, so ONE vertical resolution drives hero + case study.
SUPPORTS = {
    "one_community_health":            ["community_health"],
    "north_texas_food_bank":           ["food_bank", "human_services"],
    "methodist_retirement_communities":["senior_living"],
    "delaware_hospice":                ["hospice_living", "health_system"],
    "catholic_charities_denver":       ["human_services"],
    "bethesda_health_group":           ["senior_living", "hospice_living"],
}
# Realized-savings headline per study (proof, not estimate).
REALIZED = {s["slug"]: s["total"] for s in STUDIES}

# accounts.sub_industry  ->  package vertical (same keys as the cover heroes)
DB_SUBINDUSTRY_TO_VERTICAL = {
    "FQHC / Community Health Center":            "community_health",
    "Community Health Center":                   "community_health",
    "Medical & Surgical Hospitals":              "health_system",
    "Elderly Care Services":                     "senior_living",
    "Mental Health & Rehabilitation Facilities": "human_services",
    "Developmental Disability Services":          "human_services",
    "Child & Family Services":                    "human_services",
    "Vocational Rehabilitation Services":         "human_services",
}

def studies_for(vertical):
    """Study slugs whose SUPPORTS include this package vertical (primary first)."""
    return [slug for slug in (s["slug"] for s in STUDIES) if vertical in SUPPORTS.get(slug, [])]

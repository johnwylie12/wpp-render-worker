"""Every figure below came from a query run against ouzrrkskrfcvtnmhlycd on
2026-09-07. The query that produced each block is quoted above it, so a future
session can re-run it rather than trust it. Nothing here is hand-typed from the
build brief — two of the brief's own vendor figures did not survive that check.
"""
SUBJECT_ID = 23895
SUBJECT = dict(
    account_id=23895, name="Goodwill Industries of South Florida Inc",
    short="Goodwill South Florida", state="FL", revenue=196096296,
    recipient="Raisa Ciobanu", recipient_title="Chief Financial Officer",
    addr1="2121 NW 21st St", addr2="Miami, FL 33142-7317",
    portal="goodwillsouthflorida-benchmark", date="September 7, 2026",
)

# select ... from v_build_queue b where b.name ilike '%goodwill%'
#   and b.canonical_blocker='buildable' and b.revenue_usd>0  -- + Operating Supply
AFFILIATES = [
 (26570,"Goodwill Industries of Southwestern Michigan Inc","Southwestern Michigan","MI",13250042,20.21),
 (23895,"Goodwill Industries of South Florida Inc","Goodwill South Florida","FL",196096296,19.36),
 (25890,"Gulfstream Goodwill Industries Inc","Gulfstream","FL",17807529,17.21),
 (24355,"Goodwill of Western and Northern Connecticut Inc","W & N Connecticut","CT",57351173,6.15),
 (24364,"Goodwill Industries of the Inland Northwest","Inland Northwest","WA",56874255,4.76),
 (18357,"Goodwill Industries of Western NY","Western NY","NY",26782991,4.67),
 (15844,"Goodwill Industries of the Valley Works","Valley Works","VA",104197127,4.50),
 (24912,"Goodwill Industries of the Gulf Coast Inc","Gulf Coast","AL",32346532,4.18),
 (24513,"Goodwill Central Coast","Central Coast","CA",47424830,4.08),
 (25211,"Heart of Texas Goodwill Industries","Heart of Texas","TX",26205578,3.95),
 (24089,"Goodwill Keystone Area","Keystone Area","PA",97096239,3.84),
 (25657,"Goodwill Industries of South Central California","South Central California","CA",20067335,3.63),
 (24514,"Goodwill Industries of Middle Georgia Inc","Middle Georgia","GA",47414283,3.49),
 (26435,"Goodwill Industries of Lubbock Inc","Lubbock","TX",13945956,2.91),
 (25597,"Evansville Goodwill Industries Inc","Evansville","IN",22187893,2.68),
 (24349,"Goodwill Industries of Southwest Florida Inc","Southwest Florida","FL",58002127,2.66),
 (24552,"Goodwill Industries of the Southern Rivers Inc","Southern Rivers","GA",45317200,2.63),
 (27203,"Goodwill Industries of South Mississippi Inc","South Mississippi","MS",10562372,2.57),
 (24645,"Morgan Memorial Goodwill Industries Inc","Morgan Memorial","MA",41467625,2.54),
 (25751,"Goodwill Industries of Northwest Ohio Inc","Northwest Ohio","OH",19212542,2.50),
 (24275,"Goodwill of Central and Coastal Virginia Inc","Central & Coastal Virginia","VA",67197242,2.37),
 (26541,"Goodwill Industries of South Central Ohio","South Central Ohio","OH",13385424,2.35),
 (23965,"Goodwill Industries of Kentucky Inc","Kentucky","KY",138259072,2.21),
 (23876,"Goodwill Industries of the Columbia Willamette","Columbia Willamette","OR",215516137,2.18),
 (26560,"Goodwill Industries of North Louisiana Inc","North Louisiana","LA",13286272,2.13),
 (24757,"Goodwill Industries of Mid-Michigan Inc","Mid-Michigan","MI",37194858,2.09),
 (24593,"Goodwill of the Coastal Empire Inc","Coastal Empire","GA",43813912,1.91),
 (24477,"Goodwill Industries of Lane County","Lane County","OR",50042331,1.86),
 (25377,"Abilene Goodwill Industries Inc","Abilene","TX",23380370,1.75),
 (24973,"Goodwill Southern Los Angeles County","Southern LA County","CA",30773976,1.72),
 (23868,"Goodwill Industries of Houston","Houston","TX",224604694,1.71),
 (26313,"Hagerstown Goodwill Industries Inc","Hagerstown","MD",14584952,1.63),
 (26305,"Zanesville Welfare Org & Goodwill Industries","Zanesville","OH",14644315,1.45),
 (24834,"Goodwill Industries of Hawaii Inc","Hawaii","HI",34510070,1.44),
 (25645,"Goodwill Industries of Northeast Iowa Inc","Northeast Iowa","IA",20160203,1.21),
 (24806,"Goodwill Temporary Services Inc","Goodwill Temporary Services","TX",35707645,1.01),
 (23951,"Goodwill Industries Manasota Inc","Manasota","FL",146987524,0.80),
 (24145,"Goodwill of Southwestern Pennsylvania","Southwestern Pennsylvania","PA",86731401,0.80),
 (25058,"Goodwill Industries of Redwood Empire","Redwood Empire","CA",28918453,0.77),
 (24040,"Goodwill Industries of North Central Wisc Inc","North Central Wisconsin","WI",106744713,0.75),
]
COHORT = dict(n=40, median=2.44, mean=3.77, q1=1.71, q3=3.86, all_nonprofit_median=2.40)

# select * from fn_recovery_evidence(23895)  -- authoritative per settled #206
RECOVERY = [
 dict(category="Operating Supply", filed=37971710, projects=69,
      p25=13.5, median=21.3, p75=34.4, weak=5126181, likely=8087974, strong=13062268),
 dict(category="Small Parcels (FedEx/UPS)", filed=2631840, projects=89,
      p25=13.7, median=23.0, p75=36.5, weak=360562, likely=605323, strong=960622),
 dict(category="Fleet Management", filed=2122533, projects=13,
      p25=7.8, median=14.8, p75=32.9, weak=165558, likely=314135, strong=698313),
]

# select ... from account_contractors where account_id = 23895
CONTRACTORS = [
 ("N&K ENTERPRISES","LAUNDRY DISTRIBUTION",1518596,"Coral Gables, FL"),
 ("SOURCEAMERICA","CONSULTING SERVICES",1332881,"Vienna, VA"),
 ("GALLAGHER BASSETT SERVICES INC","THIRD PARTY ADMINISTRATORS",558228,"Chicago, IL"),
 ("ADP INC","PAYROLL SERVICES",476232,"Boston, MA"),
 ("HAMMOQ INC","CONSULTING",312577,"Phoenix, AZ"),
]

# ADP: contractor_name ilike '%ADP%' — checked for false positives, only genuine
#   ADP variants returned. 19 orgs.
# SourceAmerica: upper(replace(contractor_name,' ','')) = 'SOURCEAMERICA' — the
#   firm is filed under three spellings and the brief's ilike '%SOURCEAMERICA%'
#   finds only one of them (6 orgs, median $922,664). Normalised: 13, $411,983.
# GALLAGHER BASSETT IS NOT HERE. The brief's "8 organisations, median $610,618"
#   comes from ilike '%GALLAGHER%', which sweeps in Arthur J Gallagher — a
#   different company — and a law firm. The real comparator set for Gallagher
#   Bassett Services Inc is TWO organisations, one of which is Goodwill itself.
#   One comparator is not a distribution and it is not published.
VENDORS = [
 dict(name="ADP", orgs=19, median=225708, lo=108830, hi=678036, theirs=476232,
      service="Payroll services"),
 dict(name="SourceAmerica", orgs=13, median=411983, lo=None, hi=1332881, theirs=1332881,
      service="Consulting services"),
]

# select ... from account_financials, lateral jsonb_array_elements(line_items)
FILING_LINES = [
 ("MATERIALS AND SUPPLIES (line 24)", 37971710, "Operating Supply"),
 ("Occupancy (line 16)", 24376137, None),
 ("Fees for services — Other (line 11g)", 8082654, None),
 ("FREIGHT AND POSTAGE (line 24)", 2631840, "Small Parcels (FedEx/UPS)"),
 ("SERVICE CHARGES (line 24)", 2423261, None),
 ("FLEET AND TRANSPORTATION (line 24)", 2122533, "Fleet Management"),
 ("All other expenses (line 24e)", 1502571, None),
 ("Office expenses (line 13)", 1372501, "Office Supplies"),
 ("Fees for services — Legal (line 11b)", 637913, "Professional Services"),
 ("Advertising and promotion (line 12)", 482421, "Marketing Services"),
 ("Travel (line 17)", 449863, "Travel"),
 ("Fees for services — Lobbying (line 11d)", 63200, None),
]

# select count(*), count(distinct contractor_name), count(distinct account_id),
#        sum(compensation_amt) from account_contractors
NETWORK = dict(contracts=18482, vendor_strings=15484, organisations=4542,
               total_usd=22.19e9)

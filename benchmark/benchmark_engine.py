"""
benchmark_engine.py — ERA Sector Benchmark renderer for the WPP render worker.

Mirrors cover_page_engine: worker.py calls render(sector_key, outfile). Each sector
is a data block in SECTORS; the template (benchmark_template.html, Poppins embedded)
is filled and written to a one-page PDF.

Add a sector: copy a SECTORS entry, fill every field, keep marquee sources + the
"oh-shit" personal-dollar band. Brand colors live in the template — do not change here.
"""
import os
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "benchmark_template.html")


def _cols(a, b):
    def col(items):
        return "".join(
            f'<div class="crow"><span>{c}</span><span class="p">{r}</span></div>'
            for c, r in items
        )
    return col(a), col(b)


_HC_A, _HC_B = _cols(
    [("Medical Supply", "8&ndash;18%"), ("Insurance", "8&ndash;25%"),
     ("Pharmacy", "6&ndash;15%"), ("Information Technology", "12&ndash;30%"),
     ("Food &amp; Catering", "10&ndash;22%")],
    [("Facilities &amp; Maintenance", "10&ndash;22%"), ("Waste Management", "15&ndash;35%"),
     ("Cleaning &amp; Laundry", "12&ndash;25%"), ("Telecommunications", "15&ndash;35%"),
     ("Energy &amp; Utilities", "8&ndash;20%")],
)
_NFP_A, _NFP_B = _cols(
    [("Insurance", "8&ndash;25%"), ("Information Technology", "12&ndash;30%"),
     ("Banking &amp; Financial Services", "10&ndash;30%"), ("Facilities &amp; Property", "10&ndash;22%"),
     ("Office Supplies", "12&ndash;25%")],
    [("Telecommunications", "15&ndash;35%"), ("Print, Mail &amp; Communications", "15&ndash;30%"),
     ("Cleaning &amp; Janitorial", "12&ndash;25%"), ("Energy &amp; Utilities", "8&ndash;20%"),
     ("Travel &amp; Operational", "10&ndash;20%")],
)

SECTORS = {
  "healthcare": {
    "KICK": "PREPARED FOR HEALTHCARE LEADERS",
    "SUB": "Healthcare", "SUBU": "HEALTHCARE",
    "LEAD": "The opportunity in your Snapshot is not a guess. It is grounded in independent "
            "healthcare-sector research and what ERA has recovered across thousands of similar "
            "engagements. A no-risk baseline review is the next step that confirms it against your own contracts.",
    "CTX": "So the real question is not whether savings exist in the sector &mdash; the authorities below "
           "settle that. It is how much is sitting in your cost base, and what it would take to get it back.",
    "BN": "$150M+", "S1N": "1,344", "S1L": "HEALTHCARE<br>CLIENTS", "S2N": "3,492", "S3N": "$1B+",
    "OSN": "$8&ndash;30M",
    "OST": "<b>a year is likely sitting in your cost base</b> &mdash; in spend you&rsquo;re already making. "
           "McKinsey puts a health system&rsquo;s external spend at 30&ndash;40% of total cost, with 5&ndash;15% "
           "recoverable. <i>No impact on care.</i>",
    "I1N": "1 in 4", "I1T": "dollars spent on U.S. healthcare is waste &mdash; up to $935 billion a year. "
           "The only real question is how much of it sits in your cost base.", "I1S": "JAMA, 2019",
    "I2N": "$265B", "I2T": "of U.S. healthcare administrative cost is reducible without compromising care &mdash; "
           "and most of it is capturable by a single organization, not just system-wide reform.",
           "I2S": "McKinsey &amp; Harvard, in JAMA",
    "I3N": "Zero cuts", "I3T": "Recovered non-clinical spend drops straight to margin &mdash; without touching "
           "staffing, service lines, or patient care. The rare lever with no trade-off.", "I3S": "The ERA model",
    "COLA": _HC_A, "COLB": _HC_B,
    "CAP": "These are a sample of the 50-plus indirect categories ERA benchmarks. Ranges are typical savings as a share of category spend, from prior healthcare engagements and "
           "independent benchmarking &mdash; not a forecast. Which categories apply is confirmed only in the "
           "no-risk baseline review.",
  },
  "not_for_profit": {
    "KICK": "PREPARED FOR NOT-FOR-PROFIT LEADERS",
    "SUB": "Not-for-Profit", "SUBU": "NOT-FOR-PROFIT",
    "LEAD": "The opportunity in your Snapshot is grounded in independent nonprofit-sector "
            "research and what ERA has recovered across thousands of similar engagements. "
            "",
    "CTX": "The question is not whether savings exist &mdash; the authorities below settle "
           "that. It is how much sits in your cost base, and what it would free for the mission.",
    "BN": "$50M+", "S1N": "604", "S1L": "NOT-FOR-PROFIT<br>CLIENTS", "S2N": "1,057", "S3N": "$300M+",
    "OSN": "$1&ndash;3M",
    "OST": "<b>a year likely recoverable for an organization your size</b> &mdash; from indirect spend you "
           "already make (insurance, IT, banking, facilities), straight back to the mission. "
           "<i>Without cutting a single program.</i>",
    "I1N": "Up to 35%", "I1T": "of a nonprofit&rsquo;s budget can go to non-program overhead under watchdog limits "
           "&mdash; the pool funders scrutinize, yet the one almost never competitively tested.",
           "I1S": "BBB Wise Giving Alliance",
    "I2N": "97%", "I2T": "of U.S. nonprofits have no procurement function &mdash; so supplier costs renew on "
           "autopilot, unchallenged for years. It is structural, not mismanagement.",
           "I2S": "National Council of Nonprofits",
    "I3N": "100%", "I3T": "of recovered overhead funds programs directly &mdash; and lifts the program-expense "
           "ratio funders and watchdogs judge you on. No trade-off against mission.", "I3S": "Charity Navigator",
    "COLA": _NFP_A, "COLB": _NFP_B,
    "CAP": "These are a sample of the 50-plus indirect categories ERA benchmarks. Ranges are typical savings as a share of category spend, from prior not-for-profit engagements and "
           "independent benchmarking &mdash; not a forecast. Which categories apply is confirmed only in the "
           "no-risk baseline review.",
  },
}

# accept a few friendly aliases from the enqueue params
ALIASES = {
    "nfp": "not_for_profit", "not-for-profit": "not_for_profit",
    "nonprofit": "not_for_profit", "non_profit": "not_for_profit",
    "health": "healthcare", "health_system": "healthcare",
}


def render(sector_key: str, outfile: str):
    key = ALIASES.get((sector_key or "").strip().lower(), (sector_key or "").strip().lower())
    if key not in SECTORS:
        raise ValueError(
            f"unknown sector '{sector_key}'. Known: {', '.join(sorted(SECTORS))}"
        )
    html = open(TEMPLATE).read()
    for k, v in SECTORS[key].items():
        html = html.replace("{{" + k + "}}", v)
    HTML(string=html).write_pdf(outfile)
    return outfile

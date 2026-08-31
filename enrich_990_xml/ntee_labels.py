"""ntee_labels.py — NTEE-CC code -> human label.

The IRS Business Master File stores the code ("P280"); nothing in our database
stores what it MEANS, so the label has to come from the published NTEE-CC
taxonomy. Codes below cover the classifications actually present in our book;
anything else falls back to its major-group letter, so a label is never blank
and never invented. label_for() returns (code3, label).
"""
MAJOR = {
    "A": "Arts, Culture and Humanities", "B": "Education",
    "C": "Environment", "D": "Animal-Related", "E": "Health Care",
    "F": "Mental Health and Crisis Intervention",
    "G": "Voluntary Health Associations and Medical Disciplines",
    "H": "Medical Research", "I": "Crime and Legal-Related",
    "J": "Employment", "K": "Food, Agriculture and Nutrition",
    "L": "Housing and Shelter", "M": "Public Safety, Disaster Relief",
    "N": "Recreation and Sports", "O": "Youth Development",
    "P": "Human Services", "Q": "International, Foreign Affairs",
    "R": "Civil Rights and Advocacy", "S": "Community Improvement",
    "T": "Philanthropy, Voluntarism and Grantmaking",
    "U": "Science and Technology", "V": "Social Science",
    "W": "Public and Societal Benefit", "X": "Religion-Related",
    "Y": "Mutual and Membership Benefit", "Z": "Unknown",
}
CODES = {
    "E11": "Health Care Single Organization Support",
    "E20": "Hospitals and Related Primary Medical Care Facilities",
    "E21": "Community Health Systems", "E22": "Hospital, General",
    "E30": "Ambulatory and Primary Health Care",
    "E32": "Community Clinic / Ambulatory Health Center",
    "E91": "Nursing Facilities", "E92": "Home Health Care",
    "F22": "Substance Abuse Prevention", "F30": "Mental Health Treatment",
    "F32": "Community Mental Health Center", "F33": "Group Home, Mental Health",
    "L20": "Housing Development, Construction and Management",
    "L22": "Senior Citizens Housing / Retirement Communities",
    "P20": "Human Service Organizations - Multipurpose",
    "P27": "Young Men's or Women's Associations",
    "P28": "Neighborhood Center, Settlement House",
    "P30": "Children's and Youth Services", "P40": "Family Services",
    "P70": "Residential Care and Adult Day Programs",
    "P73": "Group Home (Long Term)", "P74": "Hospice",
    "P75": "Senior Continuing Care Communities",
    "P80": "Centers to Support the Independence of Specific Populations",
    "P81": "Senior Centers and Services",
    "P82": "Developmentally Disabled Centers and Services",
}


def label_for(raw):
    """'P280' -> ('P28', 'Neighborhood Center, Settlement House')."""
    c = (raw or "").strip().upper()
    if not c:
        return None, None
    c3 = c[:3]
    if c3 in CODES:
        return c3, CODES[c3]
    if c[:1] in MAJOR:
        # No specific label: name the major group rather than guess a subcode.
        return (c3 if len(c) >= 3 else c[:1]), MAJOR[c[:1]]
    return c3, None

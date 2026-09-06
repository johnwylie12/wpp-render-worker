"""GENERATED FROM brand_tokens. DO NOT EDIT.

Regenerate with eor/question_led/generate_tokens.py. Editing this file by
hand recreates the exact failure mode that cost five production defects:
a fact stored in Postgres and also typed into the app, with nothing
forcing them to agree.
"""

# name -> hex, every colour token, in table order
TOKENS = {
    'Daybreak Blue': '#003A70',
    'Sunrise Yellow': '#FF9C00',
    'Cool Grey': '#97999B',
    'White': '#FFFFFF',
    'Black': '#000000',
    'Midnight Blue': '#111127',
    'Royal Blue': '#0304C8',
    'Sea Green': '#3CDBC0',
    'Sustainability Green': '#30703A',
    'Panel Mist': '#F2F5F8',
    'Panel Deep': '#E4EBF3',
    'Decision Cream': '#FEF4E2',
    'Cream Edge': '#F0D8A6',
    'Ink': '#1B2A41',
    'Slate': '#5A6577',
    'Hairline': '#D7DFE9',
}

DAYBREAK_BLUE = '#003A70'
SUNRISE_YELLOW = '#FF9C00'
COOL_GREY = '#97999B'
WHITE = '#FFFFFF'
BLACK = '#000000'
MIDNIGHT_BLUE = '#111127'
ROYAL_BLUE = '#0304C8'
SEA_GREEN = '#3CDBC0'
SUSTAINABILITY_GREEN = '#30703A'
PANEL_MIST = '#F2F5F8'
PANEL_DEEP = '#E4EBF3'
DECISION_CREAM = '#FEF4E2'
CREAM_EDGE = '#F0D8A6'
INK = '#1B2A41'
SLATE = '#5A6577'
HAIRLINE = '#D7DFE9'

# Hexes named as forbidden in a usage rule. A near-miss brand colour is the
# failure these tokens exist to prevent, so the list is machine-checkable.
FORBIDDEN_HEXES = {
    '#053879',
    '#16243F',
    '#C8930F',
    '#E8A317',
    '#F2A900',
    '#F5991A',
}

def css_variables(prefix='--'):
    """The same palette as CSS custom properties, for the stylesheet."""
    out = []
    for name, hex_ in TOKENS.items():
        var = name.lower().replace(' ', '-')
        out.append(f'{prefix}{var}: {hex_};')
    return '\n'.join(out)

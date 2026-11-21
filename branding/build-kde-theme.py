#!/usr/bin/env python3
"""Write the Slate KDE color schemes + system-wide KDE defaults into overlay/.

KDE apps read the actual color values from kdeglobals (not just the scheme name), so the
default scheme's [Colors:*] groups go into both SlateDark.colors (selectable in System
Settings) and /etc/xdg/kdeglobals (the default for every user, including root for the
installer). The other schemes are extra choices in System Settings > Colors.
Run with: python3 -I branding/build-kde-theme.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OV = os.path.join(ROOT, 'overlay')

NEG, NEU = '242,92,58', '242,197,58'

# Surfaces (RGB strings)
DARK = dict(ink='17,18,20', base='26,27,30', surface='34,35,39', raised='42,43,47',
            alt='38,39,43', text='230,230,230', muted='138,138,138', disabled='56,56,56')
LIGHT = dict(ink='222,223,226', base='233,234,236', surface='246,246,247', raised='252,252,252',
             alt='238,239,241', text='28,29,32', muted='110,112,118', disabled='200,200,200')

# Accents: (accent, hover, text-on-accent, link color on the surface)
ACCENTS = {
    'Lime':   ('182,242,58', '204,247,120', '17,18,20', '146,214,48'),
    'Cyan':   ('58,214,242', '120,228,247', '17,18,20', '58,190,226'),
    'Orange': ('242,163,58', '247,190,120', '17,18,20', '236,150,40'),
    'Violet': ('169,139,245', '196,176,248', '17,18,20', '160,130,240'),
}
# Lime on a light background needs a darker link/focus shade to stay readable
LIGHT_LIME = ('182,242,58', '204,247,120', '17,18,20', '86,128,10')

def build(surf, accent):
    acc, hi, on, link = accent
    def group(bg, alt, fg=surf['text'], inactive=surf['muted']):
        return {'BackgroundAlternate': alt, 'BackgroundNormal': bg,
                'DecorationFocus': acc, 'DecorationHover': hi,
                'ForegroundActive': link, 'ForegroundInactive': inactive,
                'ForegroundLink': link, 'ForegroundNegative': NEG, 'ForegroundNeutral': NEU,
                'ForegroundNormal': fg, 'ForegroundPositive': link, 'ForegroundVisited': surf['muted']}
    sel = group(acc, hi, fg=on, inactive=on)
    sel.update({'ForegroundActive': on, 'ForegroundLink': on, 'ForegroundVisited': on,
                'ForegroundPositive': on})
    colors = {
        'Colors:Button': group(surf['raised'], surf['surface']),
        'Colors:Complementary': group(DARK['ink'], DARK['base'], fg=DARK['text'], inactive=DARK['muted']),
        'Colors:Header': group(surf['ink'], surf['base']),
        'Colors:Header][Inactive': group(surf['base'], surf['ink']),
        'Colors:Selection': sel,
        'Colors:Tooltip': group(surf['ink'], surf['base']),
        'Colors:View': group(surf['surface'], surf['alt']),
        'Colors:Window': group(surf['base'], surf['surface']),
    }
    extra = {
        'ColorEffects:Disabled': {'Color': surf['disabled'], 'ColorAmount': '0', 'ColorEffect': '0',
                                  'ContrastAmount': '0.65', 'ContrastEffect': '1',
                                  'IntensityAmount': '0.1', 'IntensityEffect': '2'},
        'ColorEffects:Inactive': {'ChangeSelectionColor': 'true', 'Color': '112,111,110',
                                  'ColorAmount': '0.025', 'ColorEffect': '2', 'ContrastAmount': '0.1',
                                  'ContrastEffect': '2', 'Enable': 'false', 'IntensityAmount': '0',
                                  'IntensityEffect': '0'},
        'WM': {'activeBackground': surf['ink'], 'activeBlend': surf['text'],
               'activeForeground': surf['text'], 'inactiveBackground': surf['base'],
               'inactiveBlend': surf['muted'], 'inactiveForeground': surf['muted']},
    }
    return {**extra, **colors}

def ini(sections):
    lines = []
    for name, kv in sections.items():
        lines.append(f'[{name}]')
        lines += [f'{k}={v}' for k, v in kv.items()]
        lines.append('')
    return '\n'.join(lines)

def write(rel, text):
    path = os.path.join(OV, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(text)

# (file id, display name, surfaces, accent)
SCHEMES = [('SlateDark', 'Slate Dark', DARK, ACCENTS['Lime'])]
SCHEMES += [(f'SlateDark{n}', f'Slate Dark ({n})', DARK, a) for n, a in ACCENTS.items() if n != 'Lime']
SCHEMES += [('SlateLight', 'Slate Light', LIGHT, LIGHT_LIME)]

for sid, name, surf, accent in SCHEMES:
    scheme = {**build(surf, accent),
              'General': {'ColorScheme': sid, 'Name': name, 'shadeSortColumn': 'true'},
              'KDE': {'contrast': '4'}}
    write(f'usr/share/color-schemes/{sid}.colors', ini(scheme))

kdeglobals = {
    'General': {'ColorScheme': 'SlateDark', 'AccentColor': ACCENTS['Lime'][0],
                'font': 'Noto Sans,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1',
                'fixed': 'Hack,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1',
                'TerminalApplication': 'konsole', 'TerminalService': 'org.kde.konsole.desktop'},
    'KDE': {'LookAndFeelPackage': 'org.slate.desktop', 'widgetStyle': 'Breeze',
            'SingleClick': 'false',
            # the light/dark pair offered on System Settings > Quick Settings
            'DefaultLightLookAndFeel': 'org.slate.light.desktop',
            'DefaultDarkLookAndFeel': 'org.slate.desktop'},
    'Icons': {'Theme': 'Slate'},
    **build(DARK, ACCENTS['Lime']),
}
write('etc/xdg/kdeglobals',
      '# Slate defaults for every user (generated by branding/build-kde-theme.py)\n' + ini(kdeglobals))
print('wrote', ', '.join(s[0] for s in SCHEMES), '+ /etc/xdg/kdeglobals')

# --- Konsole: Slate color scheme + default profile ---
def rgb(s): return tuple(int(v) for v in s.split(','))
def mix(c, t, k): return ','.join(str(int(a + (b - a) * k)) for a, b in zip(rgb(c), rgb(t)))
ANSI = ['42,43,47', NEG, ACCENTS['Lime'][0], NEU, '90,160,242', ACCENTS['Violet'][0], ACCENTS['Cyan'][0], '200,200,200']
kon = {'General': {'Description': 'Slate', 'Opacity': '1', 'Blur': 'false'},
       'Background': {'Color': DARK['base']}, 'BackgroundIntense': {'Color': DARK['raised']},
       'BackgroundFaint': {'Color': DARK['base']},
       'Foreground': {'Color': DARK['text']}, 'ForegroundIntense': {'Color': '255,255,255'},
       'ForegroundFaint': {'Color': DARK['muted']}}
for i, c in enumerate(ANSI):
    kon[f'Color{i}'] = {'Color': c}
    kon[f'Color{i}Intense'] = {'Color': mix(c, '255,255,255', 0.25 if i else 0.3)}
    kon[f'Color{i}Faint'] = {'Color': mix(c, DARK['base'], 0.4)}
write('usr/share/konsole/Slate.colorscheme', ini(kon))
write('usr/share/konsole/Slate.profile', ini({
    'Appearance': {'ColorScheme': 'Slate', 'Font': 'Hack,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1',
                   'UseCustomCursorColor': 'true', 'CustomCursorColor': ACCENTS['Lime'][0]},
    'Cursor Options': {'CursorShape': '1'},
    'General': {'Name': 'Slate', 'Parent': 'FALLBACK/'},
}))
write('etc/xdg/konsolerc', ini({'Desktop Entry': {'DefaultProfile': 'Slate.profile'}}))
print('wrote Konsole Slate.colorscheme + Slate.profile + /etc/xdg/konsolerc')

import os
import json
import re
import base64

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")
BLUEPRINTS_DIR = os.path.join(BASE_DIR, "02_BLUEPRINTS")
CLIENT_DIR = os.path.join(BASE_DIR, "03_CLIENTS")
RESOURCES_DIR = os.path.join(BASE_DIR, "04_RESOURCES")
WORKBENCH_DIR = os.path.join(BASE_DIR, "05_WORKBENCH")

def get_blueprint_path(id_str):
    return os.path.join(BLUEPRINTS_DIR, f"id_{id_str}.md")

# --- UTILS ---
def extract_css_from_blueprint(blueprint_path):
    if not os.path.exists(blueprint_path):
        return ""
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'```css\n(.*?)\n```', content, re.DOTALL)
    return match.group(1) if match else ""

def get_asset_path(relative_path):
    # Converte caminhos baseados na estrutura antiga para a nova estrutura de RESOURCES
    if "assets/fonts" in relative_path:
        return os.path.join(RESOURCES_DIR, "fonts", os.path.basename(relative_path))
    if "placeholders" in relative_path:
        return os.path.join(RESOURCES_DIR, "placeholders", os.path.basename(relative_path))
    return os.path.join(BASE_DIR, relative_path.replace("/", os.sep))

def get_image_path(slide_index):
    img_name = f"Ativo {slide_index}.jpg"
    path = os.path.join(RESOURCES_DIR, "placeholders", "imgs", img_name)
    if os.path.exists(path):
        return path
    return None

def get_base64_from_file(path):
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding file {path}: {e}")
        return ""

# --- LOAD DATA ---
# Pega o primeiro JSON encontrado na pasta CLIENTS (ou usa um padrão)
client_files = [f for f in os.listdir(CLIENT_DIR) if f.endswith('.json')]
if not client_files:
    print(f"Error: No client JSON found in {CLIENT_DIR}")
    exit(1)

CLIENT_PATH = os.path.join(CLIENT_DIR, client_files[0])
with open(CLIENT_PATH, 'r', encoding='utf-8') as f:
    client = json.load(f)

brand_name = client['identity']['brand_name']
branding = client['branding']
colors = branding['colors']
fonts = branding['fonts']

# Encode Fonts for high-fidelity preview
h_font_path = get_asset_path(fonts['headline']['path'])
b_font_path = get_asset_path(fonts['body']['path'])

h_font_b64 = get_base64_from_file(h_font_path)
b_font_b64 = get_base64_from_file(b_font_path)

h_font_family = fonts['headline']['family']
b_font_family = fonts['body']['family']

# Detect Active ID
active_id_path = os.path.join(SCRATCH_DIR, "active_id.txt")
active_id = "003"
if os.path.exists(active_id_path):
    with open(active_id_path, 'r') as f:
        active_id = f.read().strip()

blueprint_path = get_blueprint_path(active_id)
custom_css = extract_css_from_blueprint(blueprint_path)

# Load Copy
COPY_PATH = os.path.join(SCRATCH_DIR, "copy_v1.txt")
if not os.path.exists(COPY_PATH):
    print(f"Error: copy_v1.txt not found at {COPY_PATH}")
    exit(1)

with open(COPY_PATH, 'r', encoding='utf-8') as f:
    raw_copy = f.read()

# Parse Slides
slides_data = {}
current_num = None
for line in raw_copy.split('\n'):
    m = re.search(r'\[SLIDE\s+(\d+)\]', line, re.IGNORECASE)
    if m:
        current_num = int(m.group(1))
        slides_data[current_num] = {}
    elif current_num and ':' in line:
        k, v = line.split(':', 1)
        slides_data[current_num][k.strip().lower()] = v.strip()

# --- GENERATE HTML ---
html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>KRO6 Preview - {brand_name} (ID {active_id})</title>
    <style>
        /* DYNAMIC BRANDING INJECTION */
        @font-face {{
            font-family: 'ClientHeadline';
            src: url('data:font/opentype;base64,{h_font_b64}');
        }}
        @font-face {{
            font-family: 'ClientBody';
            src: url('data:font/truetype;base64,{b_font_b64}');
        }}

        :root {{
            /* Mapping variables to Blueprint standards */
            --BG: {colors['dark_bg']};
            --ACC: {colors['accent']};
            --TXT: {colors['light_bg']};
            --PRIMARY: {colors['primary']};
            --H-FONT: 'ClientHeadline', serif;
            --B-FONT: 'ClientBody', sans-serif;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #111; padding: 50px; display: flex; flex-direction: column; align-items: center; }}

        .kro6-slide-container {{
            width: 1080px;
            height: 1350px;
            position: relative;
            overflow: hidden;
            margin-bottom: 50px;
            display: flex;
            flex-direction: column;
            background: var(--BG);
            background-size: cover;
            background-position: center;
        }}

        .brand-bar {{
            position: absolute;
            top: 56px; left: 56px; right: 56px;
            display: flex; justify-content: space-between;
            font-size: 14px; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.1em; opacity: 0.6; z-index: 100;
            font-family: var(--B-FONT);
            color: var(--TXT);
        }}

        .progress-bar {{
            position: absolute; bottom: 80px; left: 56px; right: 56px;
            height: 3px; background: rgba(255,255,255,0.1); z-index: 100;
        }}

        .progress-fill {{ height: 100%; background: var(--ACC); }}

        /* CUSTOM BLUEPRINT CSS */
        {custom_css}
    </style>
</head>
<body class="id-{active_id}">
"""

total_slides = 10 

for i in range(1, total_slides + 1):
    data = slides_data.get(i, {})
    perc = (i / total_slides) * 100
    
    img_path = get_image_path(i)
    img_b64 = get_base64_from_file(img_path)
    bg_style = f"background-image: url('data:image/jpeg;base64,{img_b64}');" if img_b64 else ""

    # Field Mapping
    values = list(data.values())
    title = values[0] if len(values) > 0 else ""
    body = values[1] if len(values) > 1 else ""

    html += f"""
    <div class="kro6-slide-container slide slide-{i}" style="{bg_style}">
        <div class="brand-bar">
            <div>{brand_name}® | 2026</div>
            <div>{i:02d}/{total_slides:02d}</div>
        </div>

        <div class="slide-content">
            <h1>{title}</h1>
            <p>{body}</p>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {perc}%"></div>
        </div>
    </div>
    """

html += """
</body>
</html>
"""

PREVIEW_PATH = os.path.join(WORKBENCH_DIR, "preview.html")
with open(PREVIEW_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"KRO6: Preview gerado para o ID {active_id} com branding dinâmico em {PREVIEW_PATH}")

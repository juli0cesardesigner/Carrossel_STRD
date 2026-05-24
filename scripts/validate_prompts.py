import os
import sys
import re
import json
from glob import glob

def load_prompt_rules():
    """Carrega regras globais e de cliente para validação de prompts."""
    strict_rules_path = os.path.join(".agent", "config", "STRICT_RULES.json")
    defaults = {
        "forbidden_terms": [],
        "allowed_terms_override": [],
        "forbidden_generator_flags": ["--ar", "--stylize", "--v"],
        "min_words": 200,
    }

    if not os.path.exists(strict_rules_path):
        return defaults

    try:
        with open(strict_rules_path, "r", encoding="utf-8") as f_rules:
            strict_rules = json.load(f_rules)
    except (OSError, json.JSONDecodeError):
        return defaults

    visual_cfg = strict_rules.get("global_constraints", {}).get("visual_prompts", {})
    rules = {
        "forbidden_terms": [],
        "allowed_terms_override": [
            str(term).strip()
            for term in visual_cfg.get("allowed_terms_override", [])
            if str(term).strip()
        ],
        "forbidden_generator_flags": [
            str(flag).strip()
            for flag in visual_cfg.get("forbidden_generator_flags", defaults["forbidden_generator_flags"])
            if str(flag).strip()
        ],
        "min_words": int(visual_cfg.get("min_words", defaults["min_words"])),
    }

    profile_path = strict_rules.get("active_client_profile")
    if not profile_path:
        return rules

    if not os.path.isabs(profile_path):
        profile_path = os.path.normpath(profile_path)

    if not os.path.exists(profile_path):
        return rules

    try:
        with open(profile_path, "r", encoding="utf-8") as f_client:
            client_cfg = json.load(f_client)
    except (OSError, json.JSONDecodeError):
        return rules

    profile_cfg = client_cfg.get("visual_prompts_rules", {})
    rules["forbidden_terms"].extend(
        [str(term).strip() for term in profile_cfg.get("forbidden_terms", []) if str(term).strip()]
    )
    rules["allowed_terms_override"].extend(
        [str(term).strip() for term in profile_cfg.get("allowed_terms_override", []) if str(term).strip()]
    )

    # Identidade agora é lida do client.json (não do plot.md).
    identity_cfg = client_cfg.get("identity", {})
    brand_name = str(identity_cfg.get("brand_name", "")).strip()
    niche_name = str(identity_cfg.get("niche", "")).strip()

    if brand_name:
        rules["forbidden_terms"].append(brand_name)
        if " " in brand_name:
            for part in brand_name.split():
                if len(part.strip()) > 2:
                    rules["forbidden_terms"].append(part.strip())

    # Adiciona termos do nicho como possíveis termos sensíveis de identidade.
    if niche_name:
        for token in re.split(r'[/,;|]', niche_name):
            token = token.strip()
            if len(token) > 2:
                rules["forbidden_terms"].append(token)
    return rules

def load_active_client_config():
    strict_rules_path = os.path.join(".agent", "config", "STRICT_RULES.json")
    if not os.path.exists(strict_rules_path):
        return {}
    try:
        with open(strict_rules_path, "r", encoding="utf-8") as f_rules:
            strict_rules = json.load(f_rules)
    except (OSError, json.JSONDecodeError):
        return {}

    profile_path = strict_rules.get("active_client_profile")
    if not profile_path:
        return {}
    if not os.path.isabs(profile_path):
        profile_path = os.path.normpath(profile_path)
    if not os.path.exists(profile_path):
        return {}
    try:
        with open(profile_path, "r", encoding="utf-8") as f_client:
            return json.load(f_client)
    except (OSError, json.JSONDecodeError):
        return {}

def _count_slides_in_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f_ref:
            text = f_ref.read()
    except OSError:
        return -1
    return len(re.findall(r'### Slide (\d+):', text))

def _pick_benchmark_file(source_path, slides_required):
    md_files = [p for p in glob(os.path.join(source_path, "*.md")) if os.path.isfile(p)]
    if not md_files:
        return None

    prompt_files = [p for p in md_files if "prompt" in os.path.basename(p).lower()]
    if not prompt_files:
        return None

    required_count = len(slides_required)
    matched_count = [p for p in prompt_files if _count_slides_in_file(p) == required_count]
    if len(matched_count) == 1:
        return matched_count[0]
    if len(matched_count) > 1:
        return sorted(matched_count)[0]

    return sorted(prompt_files)[0]

def resolve_prompts_benchmark_path(slides_required):
    """
    Aceita benchmarks.prompts como:
    - string com pasta (auto por quantidade de slides) ou arquivo fixo
    - objeto {"source":"pasta|arquivo", "file":"arquivo.md"} para fixar manualmente
    """
    client_cfg = load_active_client_config()
    bench_cfg = client_cfg.get("benchmarks", {}).get("prompts")
    if not bench_cfg:
        return None, None

    if isinstance(bench_cfg, str):
        source = bench_cfg
        fixed_file = ""
    elif isinstance(bench_cfg, dict):
        source = str(bench_cfg.get("source", "")).strip()
        fixed_file = str(bench_cfg.get("file", "")).strip()
    else:
        return None, "Formato inválido em benchmarks.prompts."

    if not source:
        return None, "benchmarks.prompts está vazio."

    source_path = source if os.path.isabs(source) else os.path.normpath(source)
    if not os.path.exists(source_path):
        return None, f"Caminho de benchmark inexistente: {source_path}"

    if os.path.isfile(source_path):
        return source_path, None

    if fixed_file:
        file_path = fixed_file if os.path.isabs(fixed_file) else os.path.join(source_path, fixed_file)
        file_path = os.path.normpath(file_path)
        if not os.path.exists(file_path):
            return None, f"Arquivo fixo de benchmark não encontrado: {file_path}"
        return file_path, None

    picked = _pick_benchmark_file(source_path, slides_required)
    if not picked:
        return None, f"Nenhum benchmark de prompts encontrado em: {source_path}"
    return picked, None

def validate_prompts(file_path, slides_required):
    """
    Validador de Prompts de Elite (Sala de Guerra)
    Verifica: Anonimização, Camadas (5 densas), Contagem de Palavras (+200) e Slides.
    """
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo {file_path} não encontrado.")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    prompt_rules = load_prompt_rules()
    benchmark_path, benchmark_error = resolve_prompts_benchmark_path(slides_required)
    benchmark_text = ""
    if benchmark_error:
        print(f"FALHA: Benchmark de prompts inválido: {benchmark_error}")
        return False
    if benchmark_path:
        try:
            with open(benchmark_path, "r", encoding="utf-8") as f_bench:
                benchmark_text = f_bench.read()
        except OSError:
            print(f"FALHA: Não foi possível ler benchmark de prompts: {benchmark_path}")
            return False

    # --- 1. ANONIMIZAÇÃO DINÂMICA ---
    # Busca termos proibidos via client.json (perfil ativo em STRICT_RULES).
    forbidden_terms = ["cliente", "marca", "persona"] # Default base
    forbidden_terms.extend(prompt_rules["forbidden_terms"])

    # Remove exceções explícitas (allowlist) antes de validar anonimização.
    allowed_terms = {term.casefold() for term in prompt_rules["allowed_terms_override"]}
    filtered_forbidden_terms = [
        term for term in set(forbidden_terms) if term.casefold() not in allowed_terms
    ]

    # Verifica se algum termo proibido aparece (Case Insensitive)
    for term in filtered_forbidden_terms:
        if len(term) < 3: continue # Evita termos muito curtos
        if re.search(r'\b' + re.escape(term) + r'\b', content, re.IGNORECASE):
            print(f"FALHA CRÍTICA: Termo proibido '{term}' (anonimização violada) encontrado.")
            return False

    # --- 2. VERIFICAÇÃO DE SLIDES ---
    # Encontra todos os blocos de prompt
    # Padrão esperado: ### Slide X: ... **Prompt:** [Camadas...]
    slides_found = re.findall(r'### Slide (\d+):', content)

    # --- 2. VERIFICAÇÃO DE SLIDES ---
    # Encontra todos os blocos de prompt
    # Padrão esperado: ### Slide X: ... **Prompt:** [Camadas...]
    slides_found = re.findall(r'### Slide (\d+):', content)
    
    if not slides_found:
        print("FALHA: Nenhum slide formatado com '### Slide X:' foi encontrado.")
        return False

    # Converte para int e verifica se todos os requeridos estão presentes
    slides_found_int = [int(s) for s in slides_found]
    req_set = {int(req) for req in slides_required}
    for req in slides_required:
        if int(req) not in slides_found_int:
            print(f"FALHA: Slide {req} é obrigatório mas não possui prompt no arquivo.")
            return False

    # --- 3. DENSIDADE E CAMADAS ---
    blocks = re.split(r'### Slide \d+:', content)[1:] # Ignora o cabeçalho do arquivo
    requires_resumo_ptbr = "**Resumo (PT-BR):**" in benchmark_text if benchmark_text else False
    requires_separator = "\n---" in benchmark_text if benchmark_text else False

    if requires_separator:
        separators_found = len(re.findall(r'\n---\s*', content))
        if separators_found < max(0, len(slides_found) - 1):
            print("FALHA ESTRUTURAL: Separadores '---' insuficientes em relação ao benchmark.")
            return False
    
    for i, block in enumerate(blocks):
        slide_num = int(slides_found[i])

        if requires_resumo_ptbr and not re.search(r'\*\*Resumo \(PT-BR\):\*\*', block):
            print(f"FALHA: Slide {slide_num} não contém '**Resumo (PT-BR):**' exigido pelo benchmark.")
            return False
        
        has_prompt_marker = "**Prompt:**" in block
        has_none_context = bool(re.search(r'visual_context:\s*["\']none["\']', block, re.IGNORECASE))

        if slide_num in req_set:
            if has_none_context:
                print(f"FALHA: Slide {slide_num} é obrigatório (está nos slides requeridos), mas contém 'visual_context: \"none\"'.")
                return False
            if not has_prompt_marker:
                print(f"FALHA: Slide {slide_num} é obrigatório e deve conter o marcador '**Prompt:**'.")
                return False
        else:
            if not has_none_context:
                print(f"FALHA: Slide {slide_num} não está na lista de slides requeridos, logo deve conter 'visual_context: \"none\"'.")
                return False
            if has_prompt_marker:
                print(f"FALHA: Slide {slide_num} não deve conter o marcador '**Prompt:**' pois está configurado como visual_context: \"none\".")
                return False
            continue

        prompt_match = re.search(r'\*\*Prompt:\*\*\s*(.*)', block, re.DOTALL)
        if not prompt_match:
            print(f"FALHA: Slide {slide_num} não contém o marcador '**Prompt:**'.")
            return False

            
        prompt_text = prompt_match.group(1).split('---')[0].strip() # Pega apenas o prompt antes do próximo separador

        # Bloqueia sufixos específicos de engines (Midjourney e similares).
        for flag in prompt_rules["forbidden_generator_flags"]:
            if re.search(r'(?<!\S)' + re.escape(flag) + r'(?!\S)', prompt_text, re.IGNORECASE):
                print(f"FALHA: Slide {slide_num} contém parâmetro de engine proibido ('{flag}').")
                return False
        
        # Contagem de Palavras
        words = prompt_text.split()
        if len(words) < prompt_rules["min_words"]:
            print(f"FALHA: Slide {slide_num} tem apenas {len(words)} palavras. Mínimo exigido: {prompt_rules['min_words']}.")
            return False
            
        # Contagem de Camadas (Parágrafos)
        # O Visual Prompt Pro deve separar as 5 camadas com uma linha vazia (\n\n)
        layers = [l.strip() for l in prompt_text.split('\n\n') if l.strip() and len(l.strip()) > 20]
        
        # Se o agente usou apenas \n em vez de \n\n, vamos avisar
        if len(layers) < 5:
            print(f"FALHA ESTRUTURAL: Slide {slide_num} tem {len(layers)} camadas detectadas.")
            print("Certifique-se de separar as 5 camadas com UMA LINHA VAZIA entre elas.")
            return False

    if benchmark_path:
        print(f"[INFO] Benchmark prompts usado: {benchmark_path}")
    print("[OK] APROVADO: Os prompts seguem todos os padrões de elite e anonimização.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/validate_prompts.py [arquivo_md] [slides_requeridos_separados_por_espaço]")
        sys.exit(1)
    
    file_to_check = sys.argv[1]
    required = sys.argv[2:]
    
    if validate_prompts(file_to_check, required):
        sys.exit(0)
    else:
        sys.exit(1)

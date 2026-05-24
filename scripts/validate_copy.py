import os
import sys
import re
import json
from glob import glob

def load_copy_limits():
    """Carrega modo de limite para copy (hard_limit ou soft_limit)."""
    defaults = {
        "mode": "hard_limit",
        "soft_margin_percent": 30,
        "soft_margin_min_chars": 5,
    }
    strict_rules_path = os.path.join(".agent", "config", "STRICT_RULES.json")
    if not os.path.exists(strict_rules_path):
        return defaults

    try:
        with open(strict_rules_path, "r", encoding="utf-8") as f_rules:
            strict_rules = json.load(f_rules)
    except (OSError, json.JSONDecodeError):
        return defaults

    copy_cfg = strict_rules.get("global_constraints", {}).get("copy_text", {})
    limits_cfg = copy_cfg.get("max_chars_enforcement")

    # Compatibilidade com configuração antiga: max_words_enforcement string.
    if isinstance(limits_cfg, dict):
        mode = str(limits_cfg.get("mode", defaults["mode"])).strip().lower()
        soft_margin_percent = int(
            limits_cfg.get("soft_margin_percent", defaults["soft_margin_percent"])
        )
        soft_margin_min_chars = int(
            limits_cfg.get("soft_margin_min_chars", defaults["soft_margin_min_chars"])
        )
    else:
        mode = str(copy_cfg.get("max_words_enforcement", defaults["mode"])).strip().lower()
        soft_margin_percent = defaults["soft_margin_percent"]
        soft_margin_min_chars = defaults["soft_margin_min_chars"]

    if mode not in {"hard_limit", "soft_limit"}:
        mode = defaults["mode"]

    return {
        "mode": mode,
        "soft_margin_percent": max(0, soft_margin_percent),
        "soft_margin_min_chars": max(0, soft_margin_min_chars),
    }

def load_copy_rules():
    """Carrega regras de formatação de copy do STRICT_RULES."""
    defaults = {"prohibited_regex": []}
    strict_rules_path = os.path.join(".agent", "config", "STRICT_RULES.json")
    if not os.path.exists(strict_rules_path):
        return defaults

    try:
        with open(strict_rules_path, "r", encoding="utf-8") as f_rules:
            strict_rules = json.load(f_rules)
    except (OSError, json.JSONDecodeError):
        return defaults

    copy_cfg = strict_rules.get("global_constraints", {}).get("copy_text", {})
    return {
        "prohibited_regex": [
            str(pattern).strip()
            for pattern in copy_cfg.get("prohibited_regex", [])
            if str(pattern).strip()
        ]
    }

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

def _pick_benchmark_file(source_path, kind, template_id):
    md_files = [p for p in glob(os.path.join(source_path, "*.md")) if os.path.isfile(p)]
    if not md_files:
        return None

    # Prefere arquivo do tipo esperado (copy_...) e template correspondente.
    candidates = []
    # Escape do ID e tratamento de barras como underscores para busca de arquivos no disco
    tid_safe = re.escape(template_id).replace('/', '[/_]').replace(r'\/', '[/_]')
    template_pattern = re.compile(rf'(^|[_-]){tid_safe}([_-]|\.|$)', re.IGNORECASE)
    for path in md_files:
        name = os.path.basename(path).lower()
        if kind == "copy" and "copy" not in name:
            continue
        if template_pattern.search(name):
            candidates.append(path)

    if candidates:
        return sorted(candidates)[0]

    # Fallback em auto: qualquer benchmark de copy.
    generic = [p for p in md_files if "copy" in os.path.basename(p).lower()]
    return sorted(generic)[0] if generic else None

def resolve_copy_benchmark_path(template_id):
    """
    Aceita benchmarks.copy como:
    - string com pasta (auto por template) ou arquivo fixo
    - objeto {"source":"pasta|arquivo", "file":"arquivo.md"} para fixar manualmente
    """
    client_cfg = load_active_client_config()
    bench_cfg = client_cfg.get("benchmarks", {}).get("copy")
    if not bench_cfg:
        return None, None

    if isinstance(bench_cfg, str):
        source = bench_cfg
        fixed_file = ""
    elif isinstance(bench_cfg, dict):
        source = str(bench_cfg.get("source", "")).strip()
        fixed_file = str(bench_cfg.get("file", "")).strip()
    else:
        return None, "Formato inválido em benchmarks.copy."

    if not source:
        return None, "benchmarks.copy está vazio."

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

    picked = _pick_benchmark_file(source_path, "copy", template_id)
    if not picked:
        return None, f"Nenhum benchmark de copy encontrado em: {source_path}"
    return picked, None

def extract_txt_keys_in_order(text):
    return re.findall(r'^\s*(txt\d+)\s*-\s*', text, flags=re.MULTILINE)

def parse_templates(template_path):
    """Lê o BANCO DE TEMPLATES e extrai as regras de campos por ID."""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    templates = {}
    # Divide por IDs de template
    blocks = re.split(r'- id: "(.*?)"', content)[1:]
    
    for i in range(0, len(blocks), 2):
        template_id = blocks[i]
        block_text = blocks[i+1]
        
        # Extrai nomes de campos e max_chars
        fields = re.findall(r'key: "(txt\d+)"', block_text)
        max_chars = re.findall(r'max_chars: (\d+)', block_text)
        
        # Cria um dicionário com o campo e seu limite de caracteres
        rules = {}
        for f_key, m_char in zip(fields, max_chars):
            rules[f_key] = int(m_char)
        
        templates[template_id] = rules
    return templates

def validate_copy(copy_path, template_id, templates_rules, limits_cfg, copy_rules):
    """Valida se o copy segue o template escolhido."""
    if template_id not in templates_rules:
        print(f"FALHA: Template ID '{template_id}' não localizado no BANCO DE TEMPLATES.")
        return False
    
    with open(copy_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rules = templates_rules[template_id]
    errors = []

    benchmark_path, benchmark_error = resolve_copy_benchmark_path(template_id)
    if benchmark_error:
        errors.append(f"Benchmark copy inválido: {benchmark_error}")
    elif benchmark_path:
        try:
            with open(benchmark_path, "r", encoding="utf-8") as f_bench:
                benchmark_text = f_bench.read()
        except OSError:
            errors.append(f"Não foi possível ler benchmark de copy: {benchmark_path}")
            benchmark_text = ""

        if benchmark_text:
            expected_order = extract_txt_keys_in_order(benchmark_text)
            found_order = extract_txt_keys_in_order(content)
            if not expected_order:
                errors.append(
                    f"Benchmark de copy sem campos txtN válidos: {benchmark_path}"
                )
            elif found_order != expected_order:
                errors.append(
                    f"Ordem de campos txtN diverge do benchmark ({os.path.basename(benchmark_path)})."
                )

    # Reprova linhas estruturais fora do padrão (ex: Slide X, Eixo Selecionado).
    for lineno, line in enumerate(content.splitlines(), start=1):
        for pattern in copy_rules["prohibited_regex"]:
            if re.search(pattern, line, re.IGNORECASE):
                errors.append(
                    f"Linha {lineno} contém estrutura proibida: '{line.strip()}'."
                )
                break
    
    # Verifica cada campo obrigatório do template no copy
    for field, limit in rules.items():
        # Busca o conteúdo que começa com 'txtX - ' e vai até o próximo 'txtY - ' ou fim do arquivo
        # Usamos uma lookahead positiva para encontrar o próximo marcador sem consumi-lo
        pattern = rf'^\s*{field}\s*-\s*(.*?)(?=^\s*txt\d+\s*-\s*|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        
        if not match:
            errors.append(f"Campo obrigatório '{field}' AUSENTE no arquivo de copy.")
            continue
        
        text = match.group(1).strip()
        char_count = len(text)
        
        mode = limits_cfg["mode"]
        margin = max(
            limits_cfg["soft_margin_min_chars"],
            int(limit * (limits_cfg["soft_margin_percent"] / 100)),
        )

        if mode == "hard_limit":
            if char_count > limit:
                errors.append(
                    f"Campo '{field}' excedeu o limite do template em modo hard_limit ({char_count}/{limit})."
                )
        else:
            if char_count > (limit + margin):
                errors.append(
                    f"Campo '{field}' excedeu o limite + margem em modo soft_limit ({char_count}/{limit} + margem {margin})."
                )
            elif char_count > limit:
                print(
                    f"[AVISO] Campo '{field}' acima do ideal, dentro da margem do soft_limit ({char_count}/{limit})."
                )
            
    if errors:
        for err in errors:
            print(f"[ERRO] {err}")
        return False
    
    if benchmark_path:
        print(f"[INFO] Benchmark copy usado: {benchmark_path}")
    print(f"[OK] APROVADO: O copy segue rigorosamente o Template {template_id} e o novo padrão Gold Standard.")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/validate_copy.py [arquivo_copy.md]")
        sys.exit(1)
    
    copy_file = sys.argv[1]
    template_bank = os.path.join("knowledge", "BANCO DE TEMPLATES.md")
    
    # Tenta descobrir o ID do template no arquivo de copy
    with open(copy_file, 'r', encoding='utf-8') as f:
        header = f.read(500)
        id_match = re.search(r'Template: (\d+[/]?\w*)', header)
    
    if not id_match:
        print("FALHA: ID do Template não encontrado no cabeçalho do arquivo (ex: Template: 015).")
        sys.exit(1)
    
    tid = id_match.group(1).strip()
    rules_bank = parse_templates(template_bank)
    
    limits = load_copy_limits()
    copy_rules = load_copy_rules()

    if validate_copy(copy_file, tid, rules_bank, limits, copy_rules):
        sys.exit(0)
    else:
        sys.exit(1)

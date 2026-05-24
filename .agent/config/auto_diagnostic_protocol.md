# Protocolo de Auto-Diagnóstico Vivo

Este protocolo define a conduta do Antigravity quando o sistema detecta falhas repetitivas de conformidade.

## 1. Gatilho de Ativação
- Se um script de validação (`validate_copy.py` ou `validate_prompts.py`) falhar mais de **3 vezes** para o mesmo arquivo.
- Se o usuário detectar que o sistema ignorou uma regra explícita do `STRICT_RULES.json`.

## 2. Ações de Bloqueio
1. **Pausa Imediata:** O assistente deve parar de tentar gerar conteúdo.
2. **Análise de Causa Raiz:** O assistente deve ler o log de erro e comparar com o `STRICT_RULES.json`.
3. **Relatório de Falha:** O assistente deve relatar: "Falha Sistêmica Detectada. Motivo: [X]. Sugestão de Ajuste: [Y]."

## 3. Manutenção da Blindagem
- As regras no arquivo `.agent/config/STRICT_RULES.json` são soberanas.
- Exemplos em `examples/` servem como o único referencial estético e estrutural aprovado.

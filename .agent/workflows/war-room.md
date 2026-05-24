---
description: Executa o Brainstorming EVAI MIND para Calendário Mensal ou Post Avulso.
---

# Workflow: Sala de Guerra (EVAI MIND Editorial)

Este workflow ativa uma sessão de brainstorming de nível genial com dois modos de entrada:
- **Calendário Mensal** (planejamento de 30 dias).
- **Post Avulso** (briefing direto com tema/contexto/link).

## Fase 0: Verificação de Estado (Obrigatório)
1. **Check de Arquivos**: O sistema DEVE listar a pasta `output/` antes de qualquer outra ação.
2. **Menu de Entrada (Obrigatório)**:
   - Perguntar ao usuário:
     - `1) Calendário Mensal`
     - `2) Post Avulso (tema / contexto / link)`
3. **Decisão de Atalho (Somente Calendário Mensal)**:
   - Se o usuário escolher `Calendário Mensal` e existir qualquer arquivo `.md` em `output/`: o sistema **não inicia setup automático**.
   - Perguntar: "Detectei calendários existentes. Deseja iniciar a **Fase 4: Especialização Solo** do Arquiteto de Eixos, continuar um calendário existente ou criar um novo planejamento do zero?"

## Fase 1: Briefing de Entrada (Auto-Discovery)
1. **Identificação**: Leitura de `knowledge/plot.md`.
2. **Setup do Ciclo (Calendário Mensal)**: Pede Mês/Ano e Direção do Mês.
3. **Setup do Ciclo (Post Avulso)**: Pede briefing objetivo com:
   - Tema
   - Contexto
   - Link (opcional, quando existir)

## Fase 2: Planejamento Editorial Estruturado (30 Dias | Somente Calendário Mensal)
// turbo
1. **Geração Direta**: O **Estrategista** analisa o `plot.md`, a estratégia de conteúdo em `knowledge/Content Strategy.md`, e gera diretamente o planejamento de 30 dias com temas baseados em pilares (Autoridade, Relacionamento, Conversão) sem simulações de debate.
2. **Construção do Mix**: 
   - Definição clara da distribuição de objetivos e temas.
   - **Protocolo de Pausa**: O sistema apresenta o calendário planejado e pausa para a intervenção do usuário.

## Fase 3: Entrega do Calendário (Full Detail | Somente Calendário Mensal)
// turbo
1. **Consolidação**: O **ESTRATEGISTA** cria a tabela em `output/calendario_[mes]_[ano].md`.

## Fase 4: Especialização de Post (Os 12 Eixos Narrativos)
1. **Ativação Solo**: **ARQUITETO DE EIXOS**.
2. **Input Obrigatório**:
   - Em `Calendário Mensal`: o sistema **AGUARDA** a escolha de um Dia/Tema.
   - Em `Post Avulso`: usa o briefing (tema/contexto/link) coletado na Fase 1.
3. **Gerador de 12 Eixos**: Gera 12 variações de ângulo baseadas em `knowledge/eixos narrativos.md`, respeitando o modo escolhido.
4. **Pausa**: "(PAUSA) Qual desses **12 Eixos** você deseja seguir para este post?"

## Fase 5: Detalhamento de Post (Escrita do Copy e Blindagem Textual)
1. **Criação do Conteúdo**: O **Copywriter** escreve o copy do carrossel slide a slide, baseado estritamente na metodologia **Light Copy (Copy de Premissas)** de [Copywriting.md](file:///f:/Julio%20Cesar/Artes/Clientes/Estradao/CARROSSEL_STRD/knowledge/Copywriting.md). Não há debates nem simulação de conselho editorial.
2. **Escrita em Arquivo (Redirecionamento)**: O Copywriter **DEVE** sobrescrever o arquivo de copy do template correspondente em `design/templates/XXX/copy_gold_standard_XXX.md` (onde `XXX` é o ID do template selecionado). Para histórico e backup, também deve salvar uma cópia idêntica em `output/[data]/[data]_[titulo]_copy.md`.
3. **Padrão de Conteúdo**: O arquivo gravado deve conter o cabeçalho obrigatório (para fins de validação pelo script):
   ```markdown
   # GOLD STANDARD: CAROUSEL COPY
   # Template: XXX
   ```
   Seguido estritamente pelas linhas de campos no formato `txtX - [conteúdo]`. Os arquivos HTML locais ignoram esse cabeçalho no fetch.
4. **Loop de Blindagem de Copy (Obrigatório)**:
   // turbo
   - O sistema **DEVE** rodar `python scripts/validate_copy.py design/templates/XXX/copy_gold_standard_XXX.md`.
   - Se houver falha (excesso de palavras ou campos ausentes), o Copywriter deve ajustar o texto imediatamente no arquivo do template.

## Fase 5.5: Pausa Estratégica da Capa (Slide 1)
1. **Objetivo**: Definir o impacto visual da capa sem contaminar o estilo dos demais slides.
2. **Entrega Obrigatória (curta, em português)**:
   - O sistema apresenta 4 opções de conceito visual para o Slide 1 como **descritivos gerais**, sem prompt longo e sem inglês.
3. **Formato da Pausa (obrigatório)**:
   - `>Classico de Alta Conversao`
   - `>Reenquadramento Estrategico`
   - `>Tensao Narrativa`
   - `>Polarizacao Controlada`
   - `>Opcao personalizada do usuario`
4. **Regra de Isolamento**:
   - O modo escolhido para a capa vale **somente** para o Slide 1.
   - Slides 2..N devem seguir o perfil narrativo normal do post.

## Fase 6: Engenharia Visual e Blindagem de Qualidade
1. **Mapeamento Prévio (Obrigatório - Anti-Desperdício)**: 
   - Antes de iniciar a geração, o sistema **DEVE** analisar o template correspondente no `BANCO DE TEMPLATES.md`.
   - Identificar e listar explicitamente quais slides têm `visual_context: "none"` e quais requerem imagens.
   - **Regra Rígida**: O **VISUAL PROMPT PRO** gerará prompts **apenas** para a lista de slides com imagens. Os slides com "none" serão salvos contendo apenas `visual_context: "none"` e sem qualquer prompt em inglês, reduzindo o consumo de tokens.
2. **Ativação**: O **VISUAL PROMPT PRO** assume o controle sabendo exatamente o mapeamento dos slides.
3. **Blindagem Contra Erros (Rigor Gold Standard)**:
   - **Anonimização**: Nomes da identidade carregada via `.agent/config/clients/client.json` são terminantemente proibidos.
   - **Densidade de Elite**: +200 palavras por prompt.
   - **Estrutura**: 5 camadas (parágrafos) separadas por **linha vazia**.
   - **Clareza para Usuário Final**: Inserir `**Resumo (PT-BR):**` antes de cada `**Prompt:**`.
4. **Entrega**: Gera o arquivo em `output/[data]/[data]_prompts_[titulo].md`.
4. **Loop de Qualidade Visual (Obrigatório)**:
   // turbo
   - O sistema **DEVE** rodar `python scripts/validate_prompts.py [arquivo] [slides]`.
   - Se o script retornar **FALHA**, o Visual Prompt Pro deve analisar o erro no log e **REFAZER** o arquivo imediatamente até a aprovação.
5. **Pausa para Geração de Imagens (Obrigatório)**:
   - **PAUSA**: O sistema apresenta os prompts validados e pausa a execução.
   - O usuário gera as imagens no Midjourney e as adiciona na pasta `design/templates/XXX/images/` no formato esperado pelo template (normalmente `001.webp`, `002.webp`, sequencialmente).
   - O usuário confirma que inseriu as imagens para prosseguir.
6. **Renderização do Carrossel (PNG)**:
   - Após a confirmação de que as imagens foram inseridas, o sistema **DEVE** rodar `python render_carousel.py design/templates/XXX/index.html output/[data]/slides` para renderizar o carrossel final com as novas imagens e exportar os slides como imagens PNG de alta resolução.
7. **Sequência Híbrida de Geração**:
   - Gerar primeiro os prompts dos Slides 2..N com perfil narrativo padrão.
   - Após a escolha da Fase 5.5, gerar o prompt do Slide 1 no modo de capa selecionado.
   - Integrar o Slide 1 ao arquivo final e validar o conjunto completo.

**Nota do Arquiteto (Antigravity):** Meu papel é manter a integridade operacional. O sistema auto-ajustável garante que falhas estruturais sejam corrigidas antes que o usuário as veja.
"""
╔════════════════════════════════════════════════════════════════════════════╗
║        GUIA COMPLETO: BANCO DE DADOS DO SUPABASE PARA SEU TCC             ║
╚════════════════════════════════════════════════════════════════════════════╝

Este documento explica COMO FUNCIONA a implementação de banco de dados
que foi criada para seu projeto de evolução de agentes.


═══════════════════════════════════════════════════════════════════════════════
1. ARQUITETURA DO SISTEMA
═══════════════════════════════════════════════════════════════════════════════

Seu sistema de evolução agora funciona assim:

    ┌──────────────────┐
    │ integracao.py    │  ← Seu código principal de evolução
    └────────┬─────────┘
             │
             ├─→ Roda gerações normalmente (como antes)
             │
             └─→ Após cada geração:
                 ┌────────────────────────┐
                 │  supabase_handler.py   │  ← Novo módulo
                 └──────────┬─────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
            ┌───────▼────────┐  ┌───▼────────────┐
            │  generations   │  │generation_stats│
            │  (tabela)      │  │   (tabela)     │
            └────────────────┘  └────────────────┘
                    │                   │
                    └───────┬───────────┘
                            │
                    ┌───────▼───────┐
                    │ best_agents   │
                    │  (tabela)     │
                    └───────────────┘
                            │
                    ┌───────▼──────────┐
                    │ Supabase Cloud   │
                    │  (PostgreSQL)    │
                    └──────────────────┘


═══════════════════════════════════════════════════════════════════════════════
2. O QUE CADA ARQUIVO FAZ
═══════════════════════════════════════════════════════════════════════════════

📄 migrations.sql
    └─ Arquivo com o SQL necessário para criar as tabelas no Supabase
    └─ Você copia esse conteúdo e executa no Supabase SQL Editor
    └─ Cria 4 tabelas principais: generations, generation_stats, best_agents
    └─ Cria 1 VIEW para análise histórica


📄 supabase_handler.py
    └─ Módulo Python que gerencia a comunicação com Supabase
    └─ Métodos principais:
       ├─ save_generation_data()      → Salva dados de uma geração
       ├─ get_generation_stats()      → Recupera stats de uma gen
       ├─ get_evolution_comparison()  → Compara gerações
       ├─ get_best_agent_network()    → Recupera rede neural antigo
       ├─ list_all_generations()      → Lista todas as gerações
       └─ export_comparison_report()  → Exporta relatório em JSON


📄 integracao.py (MODIFICADO)
    └─ Seu arquivo principal agora com integração Supabase
    └─ Mudanças:
       ├─ Importa SupabaseHandler
       ├─ Carrega credenciais do .env
       ├─ Função _get_experiment_params() coleta todos os parâmetros
       └─ No loop principal: chama supabase_handler.save_generation_data()


═══════════════════════════════════════════════════════════════════════════════
3. ESTRUTURA DAS TABELAS NO BANCO
═══════════════════════════════════════════════════════════════════════════════

A. TABELA "generations" - Metadados de cada geração
   ┌──────────────────────────────────────┐
   │ id (PK)           → 1, 2, 3, ...     │
   │ generation_number → 1, 2, 3, ...     │
   │ created_at        → 2026-03-30...    │
   │ duration_seconds  → 20.5, 19.8, ...  │  ← Tempo da geração
   │ num_agents        → 20               │
   │ mutation_rate     → 0.1              │  Parâmetros
   │ elite_ratio       → 0.2              │  da
   │ mutation_strength → 0.2              │  evolução
   │ progress_reward   → 5.0              │
   │ reach_bonus       → 200.0            │
   │ hold_bonus        → 16.0             │
   │ wall_penalty      → 8.0              │
   │ distance_penalty  → 0.004            │
   └──────────────────────────────────────┘
   
   POR QUE ISSO IMPORTA:
   → Você saberá EXATAMENTE que parâmetros produziram cada geração
   → Se mudar mutation_rate na geração 50, o banco registra isso
   → Facilita reproduzibilidade: pode "recriar" gerações antigas


B. TABELA "generation_stats" - Estatísticas e métricas
   ┌────────────────────────────────────────┐
   │ id (PK)           → 1, 2, 3, ...       │
   │ generation_id (FK)→ 1, 2, 3, ...       │
   │ avg_fitness       → 145.23             │  Média dos     
   │ max_fitness       → 255.87             │  fitness
   │ min_fitness       → 45.12              │  de todos
   │ median_fitness    → 142.5              │  os agentes
   │ std_fitness       → 52.1               │  da gen
   │ success_rate      → 0.75               │  75% atingiram alvo
   │ avg_time_alive    → 18.2               │  Tempo médio vivo
   │ elite_count       → 4                  │  Quantos foram elite
   │ created_at        → 2026-03-30...      │
   └────────────────────────────────────────┘
   
   POR QUE ISSO IMPORTA:
   → Vê claramente se a população está evoluindo ou não
   → Se max_fitness não muda por 20 gerações = convergência
   → Pode detectar problemas (ex: taxa sucesso caindo)


C. TABELA "best_agents" - Melhores agentes de cada geração
   ┌────────────────────────────────────────────────────────┐
   │ id (PK)           → 1, 2, 3, ...                        │
   │ generation_id (FK)→ 1, 1, 1, 2, 2, 2, ...              │
   │ agent_rank        → 1, 2, 3, 1, 2, 3, ...              │
   │ fitness           → 255.87, 248.5, 240.2, ...          │
   │ time_alive        → 19.8, 20.0, 19.3, ...              │
   │ reached_target    → true, true, false, ...             │
   │ network_w1        → [[0.2, -0.1, ...], ...]            │  Rede neural
   │ network_w2        → [[0.5, 0.3], ...]                  │  em formato
   │ network_b1        → [0.1, -0.2, ...]                   │  JSON
   │ network_b2        → [0.15, 0.05]                       │
   │ created_at        → 2026-03-30...                      │
   └────────────────────────────────────────────────────────┘
   
   POR QUE ISSO IMPORTA:
   → Você pode RECUPERAR agentes antigos para testar depois
   → Comparar: "O agente melhor de gen 10 seria bom na gen 100?"
   → Análise: Como a rede neural evoluiu ao longo do tempo?
   → REPLICAÇÃO: Pode recriar exatamente o agente da gen 5


═══════════════════════════════════════════════════════════════════════════════
4. FLUXO PASSO A PASSO: O QUE ACONTECE A CADA GERAÇÃO
═══════════════════════════════════════════════════════════════════════════════

GERAÇÃO 1:
┌─ Cria 20 agentes com redes neurais aleatórias
├─ Roda por 20 segundos (GEN_DURATION)
├─ Agentes ganham/perdem fitness conforme se movem
│
└─ FINAL DA GERAÇÃO:
   ├─ PASSO 1: Insere em "generations"
   │  └─> INSERT INTO generations VALUES (1, 1, now(), 20.5, 20, 0.1, ...)
   │
   ├─ PASSO 2: Calcula stats
   │  ├─> avg_fitness = mean([67.3, 145.2, 82.1, ...]) = 112.4
   │  ├─> max_fitness = 255.87 (melhor agente)
   │  ├─> success_rate = 15/20 = 0.75 (75% atingiu alvo)
   │  └─> INSERT INTO generation_stats VALUES (1, 112.4, 255.87, ...)
   │
   ├─ PASSO 3: Salva 3 melhores agentes
   │  ├─> Agent #1: fitness=255.87, rank=1
   │  │   └─> INSERT com network_w1, network_w2, b1, b2 em JSON
   │  ├─> Agent #5: fitness=248.5, rank=2
   │  │   └─> INSERT com network_w1, network_w2, b1, b2 em JSON
   │  └─> Agent #12: fitness=240.2, rank=3
   │      └─> INSERT com network_w1, network_w2, b1, b2 em JSON
   │
   └─ PASSO 4: Evolui para próxima geração
      └─> Elite (top 4 agentes) são copiados
         → Resto é criado por mutação da elite


GERAÇÃO 2:
└─ Repete tudo acima, mas agora com população evoluída


═══════════════════════════════════════════════════════════════════════════════
5. COMO COMEÇAR (PASSO A PASSO)
═══════════════════════════════════════════════════════════════════════════════

1️⃣  CRIAR CONTA SUPABASE
    ├─ Vá para https://supabase.com
    ├─ Crie uma conta (grátis)
    ├─ Crie um novo projeto
    └─ Anote o URL e a chave anon dos Settings

2️⃣  EXECUTAR AS MIGRAÇÕES SQL
    ├─ Abra Supabase > Seu projeto > SQL Editor
    ├─ Crie uma nova query
    ├─ Copie TODO o conteúdo de "migrations.sql"
    ├─ Cole no SQL Editor
    ├─ Clique "Run"
    └─ Verifique que 4 tabelas foram criadas na aba "Tables"

3️⃣  CONFIGURAR SEU .env
    ├─ Renomeie ".env.example" para ".env"
    ├─ Preenchha os valores:
    │  SUPABASE_URL=https://seu-projeto.supabase.co
    │  SUPABASE_KEY=sua-chave-anon-aqui
    └─ Salve o arquivo

4️⃣  INSTALAR DEPENDÊNCIA
    ├─ Terminal: pip install -r requirements.txt
    └─ Isso instala supabase==2.0.3 automaticamente

5️⃣  RODAR O CÓDIGO
    ├─ Terminal: python integracao.py
    ├─ Veja as mensagens na console:
    │  [✓] Conectado ao Supabase com sucesso!
    │  [✓] Banco de dados ativado!
    └─ Cada geração, verá:
       [⏳] Salvando geração 1...
       [✓] Geração criada com ID 1
       [✓] Estatísticas salvas:
           └─ Fitness Médio: 112.40
           └─ Fitness Máximo: 255.87
           └─ Taxa de Sucesso: 75.0%
       [✓] Salvos 3 melhores agentes


═══════════════════════════════════════════════════════════════════════════════
6. EXEMPLOS DE USO
═══════════════════════════════════════════════════════════════════════════════

ANALISAR EVOLUÇÃO:
────────────────────

    from supabase_handler import SupabaseHandler
    
    handler = SupabaseHandler("seu_url", "sua_key")
    
    # Comparar gerações 1 a 50
    evolution = handler.get_evolution_comparison(1, 50)
    
    for gen in evolution:
        print(f"Gen {gen['generation_number']}:")
        print(f"  Fitness médio: {gen['avg_fitness']:.2f}")
        print(f"  Taxa sucesso: {gen['success_rate']:.1%}")
        print(f"  Melhoria: {gen['fitness_improvement']:.2f}")


RECUPERAR AGENTE ANTIGO PARA TESTAR:
─────────────────────────────────────

    from rede_neural import RedeNeural
    
    # Pega o melhor agente da geração 10
    network_data = handler.get_best_agent_network(
        generation_number=10,
        rank=1  # melhor agente
    )
    
    # Reconstrói a rede neural
    rede = RedeNeural()
    rede.w1 = network_data['w1']
    rede.w2 = network_data['w2']
    rede.b1 = network_data['b1']
    rede.b2 = network_data['b2']
    
    # Agora pode testar esse agente em um novo cenário
    output = rede.forward([0.5, -0.3, 0.7])


EXPORTAR RELATÓRIO PARA ANÁLISE:
──────────────────────────────────

    handler.export_comparison_report("meu_relatorio.json")
    
    # Gera um arquivo JSON com ALL os dados para análise no Excel,
    # Python, ou qualquer ferramenta de análise


═══════════════════════════════════════════════════════════════════════════════
7. VANTAGENS DESSA IMPLEMENTAÇÃO
═══════════════════════════════════════════════════════════════════════════════

✅ RASTREABILIDADE COMPLETA
   → Sabe exatamente quais parâmetros produziram cada resultado
   → Reproduzibilidade: pode "recriar" experimentos antigos

✅ COMPARAÇÃO TEMPORAL
   → Vê como a evolução progride (ou não progride)
   → Detecta plateaus, regressões, ou divergências

✅ RECUPERAÇÃO DE AGENTES
   → Pode testar um agente de 50 gerações atrás
   → Análise comparativa: Como ele se sairia hoje?

✅ SEGURANÇA
   → Dados na nuvem (Supabase), não depende do seu HD
   → Já faz backups automaticamente

✅ ESCALABILIDADE
   → Pode rodar múltiplas "runs" paralelas
   → Agrupa todos os dados no mesmo lugar

✅ FACILITA TRABALHO ACADÊMICO
   → Dados estruturados para análise estatística
   → Pronto para gerar gráficos e relatórios do TCC


═══════════════════════════════════════════════════════════════════════════════
8. DÚVIDAS COMUNS
═══════════════════════════════════════════════════════════════════════════════

P: Como mudo os parâmetros entre gerações?
R: Edite as constantes no topo de integracao.py entre execuções.
   O banco automaticamente registra cada mudança.

P: Posso rodar sem Supabase?
R: Sim! Se não configurar .env, o código roda normalmente sem salvar.

P: Quantos dados são armazenados?
R: Muito pouco. Cada geração = ~2KB. 100 gerações = ~200KB.
   Supabase plano free = 500MB = suficiente para anos de experimento.

P: Como recupero dados antigos?
R: Use handler.get_best_agent_network(generation=X, rank=Y)
   Reconstrói a rede neural exatamente como era.

P: Posso visualizar os dados no Supabase?
R: Sim! Vá em Supabase > Seu projeto > Tables
   Vê em tempo real todos os dados sendo salvos.

P: Como exporto para análise?
R: Use handler.export_comparison_report("arquivo.json")
   Aí importa no Excel, Python, Pandas, etc.


═══════════════════════════════════════════════════════════════════════════════
9. PRÓXIMOS PASSOS (MELHORIAS FUTURAS)
═══════════════════════════════════════════════════════════════════════════════

• Criar dashboard de visualização em tempo real
• Implementar alertas (ex: "fitness não mudou em 30 gerações")
• Comparar múltiplos "runs" do mesmo experimento
• Machine Learning para prever evolução futura
• Integrar com TensorBoard para visualizar redes neurais evoluídas

═════════════════════════════════════════════════════════════════════════════════

Pronto! Seu sistema agora tem banco de dados completo, rastreável e escalável! 🚀
"""

# Nota: Esse arquivo é apenas documentação. Você pode lê-lo assim:
# python -c "import banco_dados_setup; print(banco_dados_setup.__doc__)"

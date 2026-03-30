-- =====================================================
-- MIGRAÇÕES PARA BANCO DE DADOS DO SUPABASE
-- =====================================================

-- 1. TABELA DE GERAÇÕES (metadados de cada geração)
-- Armazena informações sobre quando cada geração foi executada e quais foram os parâmetros
CREATE TABLE IF NOT EXISTS generations (
    id BIGSERIAL PRIMARY KEY,
    generation_number BIGINT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_seconds FLOAT NOT NULL,
    num_agents BIGINT NOT NULL,
    mutation_rate FLOAT NOT NULL,
    elite_ratio FLOAT NOT NULL,
    mutation_strength FLOAT NOT NULL,
    -- Parâmetros de recompensa e penalidade
    progress_reward FLOAT,
    reach_bonus FLOAT,
    hold_bonus FLOAT,
    wall_penalty FLOAT,
    distance_penalty FLOAT
);

-- Índices para melhorar buscas
CREATE INDEX idx_generations_number ON generations(generation_number DESC);
CREATE INDEX idx_generations_created_at ON generations(created_at DESC);


-- 2. TABELA DE ESTATÍSTICAS POR GERAÇÃO
-- Armazena métricas agregadas de fitness e desempenho
CREATE TABLE IF NOT EXISTS generation_stats (
    id BIGSERIAL PRIMARY KEY,
    generation_id BIGINT NOT NULL UNIQUE REFERENCES generations(id) ON DELETE CASCADE,
    avg_fitness FLOAT NOT NULL,
    max_fitness FLOAT NOT NULL,
    min_fitness FLOAT NOT NULL,
    median_fitness FLOAT NOT NULL,
    std_fitness FLOAT NOT NULL,
    success_rate FLOAT NOT NULL, -- porcentagem de agentes que atingiram o alvo
    avg_time_alive FLOAT NOT NULL,
    elite_count BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gen_stats_generation_id ON generation_stats(generation_id);
CREATE INDEX idx_gen_stats_max_fitness ON generation_stats(max_fitness DESC);


-- 3. TABELA DE MELHORES AGENTES
-- Armazena os melhores agentes de cada geração (pode salvar os N melhores ou apenas o top 1)
CREATE TABLE IF NOT EXISTS best_agents (
    id BIGSERIAL PRIMARY KEY,
    generation_id BIGINT NOT NULL REFERENCES generations(id) ON DELETE CASCADE,
    agent_rank BIGINT NOT NULL, -- 1 para melhor, 2 para segundo melhor, etc
    fitness FLOAT NOT NULL,
    time_alive FLOAT NOT NULL,
    reached_target BOOLEAN NOT NULL,
    
    -- Pesos da rede neural (salvamos como JSON)
    -- Layer 1: input -> hidden
    network_w1 JSONB NOT NULL,
    -- Layer 2: hidden -> output
    network_w2 JSONB NOT NULL,
    -- Bias layer 1
    network_b1 JSONB NOT NULL,
    -- Bias layer 2
    network_b2 JSONB NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_best_agents_generation_id ON best_agents(generation_id);
CREATE INDEX idx_best_agents_rank ON best_agents(agent_rank);
CREATE INDEX idx_best_agents_fitness ON best_agents(fitness DESC);


-- 4. TABELA DE COMPARAÇÃO HISTÓRICA (VIEW para facilitar análise)
-- Essa view permite comparar evolução entre gerações facilmente
CREATE VIEW generation_evolution AS
SELECT 
    g.generation_number,
    g.created_at,
    gs.avg_fitness,
    gs.max_fitness,
    gs.min_fitness,
    gs.median_fitness,
    gs.std_fitness,
    gs.success_rate,
    gs.avg_time_alive,
    -- Melhor agente de cada geração
    (SELECT fitness FROM best_agents 
     WHERE generation_id = g.id AND agent_rank = 1 
     LIMIT 1) as best_agent_fitness,
    -- Comparação com geração anterior
    LAG(gs.avg_fitness) OVER (ORDER BY g.generation_number) as prev_avg_fitness,
    (LAG(gs.avg_fitness) OVER (ORDER BY g.generation_number) - gs.avg_fitness) as fitness_improvement
FROM generations g
LEFT JOIN generation_stats gs ON g.id = gs.generation_id
ORDER BY g.generation_number;


-- =====================================================
-- INSTRUÇÕES PARA USAR ESSAS MIGRAÇÕES
-- =====================================================
-- 1. Vá para Supabase > SQL Editor
-- 2. Copie e cole este arquivo inteiro
-- 3. Execute o SQL
-- 4. Pronto! Seu banco está criado

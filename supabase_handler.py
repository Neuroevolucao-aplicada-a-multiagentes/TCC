"""
=====================================================
MÓDULO DE INTEGRAÇÃO COM SUPABASE
=====================================================

Este módulo gerencia toda a comunicação com o banco de dados PostgreSQL
hospedado no Supabase. Ele salva:
1. Metadados de cada geração
2. Estatísticas de fitness (média, max, min, desvio padrão)
3. Melhores agentes (com seus pesos de rede neural)

Uso:
    from supabase_handler import SupabaseHandler
    
    handler = SupabaseHandler(url, key)
    handler.save_generation_data(
        generation_number=1,
        duration=20.0,
        agentes=agentes,
        params=params
    )
"""

import json
from datetime import datetime
from statistics import mean, median, stdev
import numpy as np
from supabase import create_client, Client


class SupabaseHandler:
    def __init__(self, url: str, key: str):
        """
        Inicializa conexão com Supabase
        
        Args:
            url: URL do projeto Supabase (ex: https://xxxx.supabase.co)
            key: Chave anon do Supabase (de Settings > API)
        """
        self.client: Client = create_client(url, key)
        print("[✓] Conectado ao Supabase com sucesso!")
    
    def _agent_network_to_dict(self, brain):
        """
        Converte a rede neural de um agente para formato JSON serializável
        
        Args:
            brain: Objeto RedeNeural com w1, w2, b1, b2
            
        Returns:
            dict com os pesos em formato lista
        """
        return {
            'w1': brain.w1.tolist(),
            'w2': brain.w2.tolist(),
            'b1': brain.b1.tolist(),
            'b2': brain.b2.tolist(),
        }
    
    def save_generation_data(self, generation_number: int, duration: float, 
                            agentes: list, params: dict) -> bool:
        """
        Salva todos os dados de uma geração no banco de dados
        
        Fluxo:
        1. Cria registro na tabela 'generations'
        2. Calcula estatísticas e salva em 'generation_stats'
        3. Salva os N melhores agentes em 'best_agents'
        
        Args:
            generation_number: Número da geração (1, 2, 3, ...)
            duration: Tempo de duração da geração em segundos
            agentes: Lista de objetos AgenteSolido da geração
            params: Dict com parâmetros do experimento
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            # PASSO 1: Inserir na tabela 'generations'
            print(f"\n[⏳] Salvando geração {generation_number}...")
            
            generation_data = {
                'generation_number': generation_number,
                'duration_seconds': duration,
                'num_agents': len(agentes),
                'mutation_rate': params.get('mutation_rate', 0.1),
                'elite_ratio': params.get('elite_ratio', 0.2),
                'mutation_strength': params.get('mutation_strength', 0.2),
                'progress_reward': params.get('progress_reward', 5.0),
                'reach_bonus': params.get('reach_bonus', 200.0),
                'hold_bonus': params.get('hold_bonus', 16.0),
                'wall_penalty': params.get('wall_penalty', 8.0),
                'distance_penalty': params.get('distance_penalty', 0.004),
            }
            
            response = self.client.table('generations').insert(generation_data).execute()
            generation_id = response.data[0]['id']
            print(f"[✓] Geração criada com ID {generation_id}")
            
            # PASSO 2: Calcular e salvar estatísticas
            fitness_scores = [a.fitness for a in agentes]
            success_count = sum(1 for a in agentes if a.reached)
            time_alive_scores = [a.time_alive for a in agentes]
            
            stats = {
                'generation_id': generation_id,
                'avg_fitness': float(mean(fitness_scores)),
                'max_fitness': float(max(fitness_scores)),
                'min_fitness': float(min(fitness_scores)),
                'median_fitness': float(median(fitness_scores)),
                'std_fitness': float(stdev(fitness_scores)) if len(fitness_scores) > 1 else 0.0,
                'success_rate': float(success_count / len(agentes)),
                'avg_time_alive': float(mean(time_alive_scores)),
                'elite_count': max(1, int(len(agentes) * params.get('elite_ratio', 0.2))),
            }
            
            self.client.table('generation_stats').insert(stats).execute()
            print(f"[✓] Estatísticas salvas:")
            print(f"    └─ Fitness Médio: {stats['avg_fitness']:.2f}")
            print(f"    └─ Fitness Máximo: {stats['max_fitness']:.2f}")
            print(f"    └─ Taxa de Sucesso: {stats['success_rate']:.1%}")
            
            # PASSO 3: Salvar os melhores agentes
            agentes_ordenados = sorted(agentes, key=lambda a: a.fitness, reverse=True)
            TOP_N = 3  # Salva os 3 melhores agentes
            
            best_agents_data = []
            for rank, agente in enumerate(agentes_ordenados[:TOP_N], 1):
                network_dict = self._agent_network_to_dict(agente.brain)
                
                best_agent = {
                    'generation_id': generation_id,
                    'agent_rank': rank,
                    'fitness': float(agente.fitness),
                    'time_alive': float(agente.time_alive),
                    'reached_target': bool(agente.reached),
                    'network_w1': network_dict['w1'],
                    'network_w2': network_dict['w2'],
                    'network_b1': network_dict['b1'],
                    'network_b2': network_dict['b2'],
                }
                best_agents_data.append(best_agent)
            
            self.client.table('best_agents').insert(best_agents_data).execute()
            print(f"[✓] Salvos {TOP_N} melhores agentes (rank 1-{TOP_N})")
            
            return True
            
        except Exception as e:
            print(f"[✗] Erro ao salvar dados: {str(e)}")
            return False
    
    def get_generation_stats(self, generation_number: int) -> dict:
        """
        Recupera estatísticas de uma geração específica
        
        Args:
            generation_number: Número da geração
            
        Returns:
            Dict com estatísticas ou None se não encontrado
        """
        try:
            response = self.client.table('generation_stats').select(
                '*, generations(generation_number)'
            ).eq('generations.generation_number', generation_number).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"[✗] Erro ao buscar: {e}")
            return None
    
    def get_evolution_comparison(self, gen_start: int, gen_end: int) -> dict:
        """
        Comparação da evolução entre duas gerações
        
        Mostra como o fitness médio, máximo e taxa de sucesso evoluíram
        
        Args:
            gen_start: Geração inicial
            gen_end: Geração final
            
        Returns:
            Dict com dados de evolução ou None
        """
        try:
            # Usa a VIEW 'generation_evolution' para comparação
            response = self.client.table('generation_evolution').select('*').gte(
                'generation_number', gen_start
            ).lte('generation_number', gen_end).execute()
            
            return response.data
        except Exception as e:
            print(f"[✗] Erro ao buscar evolução: {e}")
            return None
    
    def get_best_agent_network(self, generation_number: int, rank: int = 1):
        """
        Recover a rede neural do melhor agente de uma geração
        
        Útil para reconstruir e testar um agente antigo
        
        Args:
            generation_number: Número da geração
            rank: Rank do agente (1 = melhor, 2 = segundo melhor, etc)
            
        Returns:
            Dict com os pesos da rede ou None
        """
        try:
            response = self.client.table('best_agents').select('*').eq(
                'agent_rank', rank
            ).eq('generations.generation_number', generation_number).execute()
            
            if response.data:
                agent = response.data[0]
                return {
                    'w1': np.array(agent['network_w1']),
                    'w2': np.array(agent['network_w2']),
                    'b1': np.array(agent['network_b1']),
                    'b2': np.array(agent['network_b2']),
                    'fitness': agent['fitness'],
                    'time_alive': agent['time_alive'],
                }
            return None
        except Exception as e:
            print(f"[✗] Erro ao buscar agente: {e}")
            return None
    
    def list_all_generations(self) -> list:
        """
        Lista todas as gerações armazenadas
        
        Returns:
            Lista de dicts com info de cada geração
        """
        try:
            response = self.client.table('generation_evolution').select('*').execute()
            return response.data
        except Exception as e:
            print(f"[✗] Erro ao listar gerações: {e}")
            return []
    
    def export_comparison_report(self, output_file: str = "evolution_report.json"):
        """
        Exporta relatório completo de evolução em JSON
        
        Args:
            output_file: Nome do arquivo de saída
        """
        try:
            data = self.list_all_generations()
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"[✓] Relatório exportado para {output_file}")
        except Exception as e:
            print(f"[✗] Erro ao exportar: {e}")

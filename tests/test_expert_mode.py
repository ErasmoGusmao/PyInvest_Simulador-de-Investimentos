"""
Testes Unitários - Modo Expert PyInvest
Valida implementação de Bootstrap, Normal e t-Student.
"""

import unittest
import numpy as np
from datetime import date

# Importar módulos do projeto
import sys
sys.path.insert(0, '.')

from core.monte_carlo import (
    ParameterRange, MonteCarloInput, MonteCarloEngine, MonteCarloResult,
    bootstrap_returns, normal_returns, t_student_returns
)


class TestReturnGenerators(unittest.TestCase):
    """Testes para funções de geração de retornos."""
    
    def setUp(self):
        """Dados históricos de exemplo (retornos anuais em %)."""
        self.historical = [15.0, -5.0, 22.0, 8.0, -12.0, 30.0, 5.0, 18.0, -3.0, 10.0]
        self.n_years = 10
        self.n_simulations = 1000
        self.seed = 42
    
    def test_bootstrap_returns_shape(self):
        """Bootstrap deve retornar matriz com shape correto."""
        result = bootstrap_returns(
            self.historical, self.n_years, self.n_simulations, seed=self.seed
        )
        
        self.assertEqual(result.shape, (self.n_simulations, self.n_years))
        print(f"✓ Bootstrap shape: {result.shape}")
    
    def test_bootstrap_returns_values_in_historical(self):
        """Bootstrap só deve retornar valores do conjunto histórico."""
        result = bootstrap_returns(
            self.historical, self.n_years, self.n_simulations, seed=self.seed
        )
        
        unique_values = set(result.flatten())
        historical_set = set(self.historical)
        
        self.assertTrue(unique_values.issubset(historical_set))
        print(f"✓ Bootstrap valores únicos ({len(unique_values)}) estão no histórico")
    
    def test_normal_returns_shape(self):
        """Normal deve retornar matriz com shape correto."""
        mean = np.mean(self.historical)
        std = np.std(self.historical)
        
        result = normal_returns(mean, std, self.n_years, self.n_simulations, seed=self.seed)
        
        self.assertEqual(result.shape, (self.n_simulations, self.n_years))
        print(f"✓ Normal shape: {result.shape}")
    
    def test_normal_returns_statistics(self):
        """Normal deve ter média e desvio próximos do esperado."""
        mean = 10.0
        std = 15.0
        
        result = normal_returns(mean, std, self.n_years, 10000, seed=self.seed)
        
        actual_mean = np.mean(result)
        actual_std = np.std(result)
        
        # Tolerância de 5%
        self.assertAlmostEqual(actual_mean, mean, delta=mean * 0.05)
        self.assertAlmostEqual(actual_std, std, delta=std * 0.05)
        print(f"✓ Normal: média={actual_mean:.2f} (esperado {mean}), std={actual_std:.2f} (esperado {std})")
    
    def test_t_student_returns_shape(self):
        """t-Student deve retornar matriz com shape correto."""
        mean = np.mean(self.historical)
        std = np.std(self.historical)
        
        result = t_student_returns(mean, std, self.n_years, self.n_simulations, seed=self.seed)
        
        self.assertEqual(result.shape, (self.n_simulations, self.n_years))
        print(f"✓ t-Student shape: {result.shape}")
    
    def test_t_student_has_fatter_tails(self):
        """t-Student deve ter caudas mais pesadas que Normal."""
        mean = 10.0
        std = 15.0
        n_sims = 50000
        
        normal_result = normal_returns(mean, std, self.n_years, n_sims, seed=self.seed)
        t_result = t_student_returns(mean, std, self.n_years, n_sims, df=5, seed=self.seed+1)
        
        # Contar valores extremos (> 3 desvios)
        normal_extremes = np.sum(np.abs(normal_result - mean) > 3 * std)
        t_extremes = np.sum(np.abs(t_result - mean) > 3 * std)
        
        # t-Student deve ter mais extremos
        self.assertGreater(t_extremes, normal_extremes)
        print(f"✓ t-Student extremos ({t_extremes}) > Normal extremos ({normal_extremes})")


class TestMonteCarloInputExpert(unittest.TestCase):
    """Testes para MonteCarloInput com Modo Expert."""
    
    def setUp(self):
        """Configuração padrão."""
        self.capital = ParameterRange(deterministic=10000)
        self.aporte = ParameterRange(deterministic=500)
        self.rentabilidade = ParameterRange(deterministic=10)
        self.historical = [15.0, -5.0, 22.0, 8.0, -12.0, 30.0, 5.0, 18.0, -3.0, 10.0]
    
    def test_has_expert_mode_false_by_default(self):
        """Modo Expert deve estar desativado por padrão."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=10
        )
        
        self.assertFalse(mc_input.has_expert_mode())
        print("✓ Modo Expert desativado por padrão")
    
    def test_has_expert_mode_needs_historical(self):
        """Modo Expert requer pelo menos 2 retornos históricos."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=10,
            expert_mode=True,
            historical_returns=[10.0]  # Apenas 1
        )
        
        self.assertFalse(mc_input.has_expert_mode())
        print("✓ Modo Expert requer >= 2 retornos históricos")
    
    def test_has_expert_mode_true_with_historical(self):
        """Modo Expert ativo com dados suficientes."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=10,
            expert_mode=True,
            historical_returns=self.historical
        )
        
        self.assertTrue(mc_input.has_expert_mode())
        print("✓ Modo Expert ativo com dados históricos")


class TestMonteCarloEngineExpert(unittest.TestCase):
    """Testes para MonteCarloEngine com Modo Expert."""
    
    def setUp(self):
        """Configuração padrão."""
        self.capital = ParameterRange(deterministic=10000)
        self.aporte = ParameterRange(deterministic=500)
        self.rentabilidade = ParameterRange(deterministic=10)
        self.historical = [15.0, -5.0, 22.0, 8.0, -12.0, 30.0, 5.0, 18.0, -3.0, 10.0]
    
    def test_expert_bootstrap_simulation(self):
        """Simulação Expert com Bootstrap deve funcionar."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=5,
            n_simulations=100,
            expert_mode=True,
            historical_returns=self.historical,
            simulation_method='bootstrap'
        )
        
        engine = MonteCarloEngine(mc_input)
        result = engine.run()
        
        self.assertTrue(result.has_monte_carlo)
        self.assertEqual(result.simulation_method, 'bootstrap')
        self.assertIsNotNone(result.sampled_final_balances)
        self.assertEqual(len(result.sampled_final_balances), 100)
        print(f"✓ Bootstrap: {result.n_simulations} simulações, método={result.simulation_method}")
        print(f"  Saldo médio: R$ {result.final_balance_mean:,.2f}")
    
    def test_expert_normal_simulation(self):
        """Simulação Expert com Normal deve funcionar."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=5,
            n_simulations=100,
            expert_mode=True,
            historical_returns=self.historical,
            simulation_method='normal'
        )
        
        engine = MonteCarloEngine(mc_input)
        result = engine.run()
        
        self.assertTrue(result.has_monte_carlo)
        self.assertEqual(result.simulation_method, 'normal')
        print(f"✓ Normal: {result.n_simulations} simulações, método={result.simulation_method}")
        print(f"  Saldo médio: R$ {result.final_balance_mean:,.2f}")
    
    def test_expert_t_student_simulation(self):
        """Simulação Expert com t-Student deve funcionar."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=5,
            n_simulations=100,
            expert_mode=True,
            historical_returns=self.historical,
            simulation_method='t_student'
        )
        
        engine = MonteCarloEngine(mc_input)
        result = engine.run()
        
        self.assertTrue(result.has_monte_carlo)
        self.assertEqual(result.simulation_method, 't_student')
        print(f"✓ t-Student: {result.n_simulations} simulações, método={result.simulation_method}")
        print(f"  Saldo médio: R$ {result.final_balance_mean:,.2f}")
    
    def test_expert_vs_standard_difference(self):
        """Expert e Standard devem produzir resultados diferentes."""
        # Modo Expert
        mc_expert = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=10,
            n_simulations=1000,
            expert_mode=True,
            historical_returns=self.historical,
            simulation_method='bootstrap'
        )
        
        # Modo Standard (com range)
        mc_standard = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=ParameterRange(min_value=5, deterministic=10, max_value=15),
            periodo_anos=10,
            n_simulations=1000
        )
        
        result_expert = MonteCarloEngine(mc_expert).run()
        result_standard = MonteCarloEngine(mc_standard).run()
        
        # Ambos devem ter Monte Carlo
        self.assertTrue(result_expert.has_monte_carlo)
        self.assertTrue(result_standard.has_monte_carlo)
        
        # Métodos diferentes
        self.assertEqual(result_expert.simulation_method, 'bootstrap')
        self.assertEqual(result_standard.simulation_method, 'parameter_range')
        
        print(f"✓ Expert (bootstrap): saldo médio R$ {result_expert.final_balance_mean:,.2f}")
        print(f"✓ Standard (ranges): saldo médio R$ {result_standard.final_balance_mean:,.2f}")
    
    def test_expert_result_has_statistics(self):
        """Resultado Expert deve ter todas as estatísticas."""
        mc_input = MonteCarloInput(
            capital_inicial=self.capital,
            aporte_mensal=self.aporte,
            rentabilidade_anual=self.rentabilidade,
            periodo_anos=5,
            n_simulations=500,
            expert_mode=True,
            historical_returns=self.historical,
            simulation_method='bootstrap'
        )
        
        result = MonteCarloEngine(mc_input).run()
        
        # Verificar estatísticas
        self.assertIsNotNone(result.percentile_stats)
        self.assertIsNotNone(result.representative_scenarios)
        self.assertGreater(len(result.representative_scenarios), 0)
        
        # Verificar arrays
        self.assertIsNotNone(result.balances_mean)
        self.assertIsNotNone(result.balances_p5)
        self.assertIsNotNone(result.balances_p95)
        
        # Verificar projeção anual
        self.assertEqual(len(result.yearly_projection), 6)  # Anos 0 a 5
        
        print(f"✓ Estatísticas completas geradas")
        print(f"  - PercentileStats: P5={result.percentile_stats.p5:,.0f}, P50={result.percentile_stats.p50:,.0f}, P95={result.percentile_stats.p95:,.0f}")
        print(f"  - Cenários representativos: {len(result.representative_scenarios)}")


class TestIntegration(unittest.TestCase):
    """Testes de integração end-to-end."""
    
    def test_full_expert_workflow(self):
        """Fluxo completo do Modo Expert."""
        # 1. Dados históricos reais (simulando Ibovespa)
        ibovespa_returns = [
            15.5,   # Ano 1
            -12.3,  # Ano 2
            22.7,   # Ano 3
            8.9,    # Ano 4
            -15.2,  # Ano 5
            31.5,   # Ano 6
            5.2,    # Ano 7
            18.8,   # Ano 8
            -3.1,   # Ano 9
            12.4    # Ano 10
        ]
        
        # 2. Criar input
        mc_input = MonteCarloInput(
            capital_inicial=ParameterRange(deterministic=100000),
            aporte_mensal=ParameterRange(deterministic=1000),
            rentabilidade_anual=ParameterRange(deterministic=10),  # Será ignorado no Expert
            periodo_anos=10,
            meta=500000,
            n_simulations=5000,
            expert_mode=True,
            historical_returns=ibovespa_returns,
            simulation_method='bootstrap'
        )
        
        # 3. Executar simulação
        engine = MonteCarloEngine(mc_input)
        result = engine.run()
        
        # 4. Verificações
        self.assertTrue(result.has_monte_carlo)
        self.assertEqual(result.simulation_method, 'bootstrap')
        
        # Verificar que usou dados históricos (variabilidade alta)
        std_final = np.std(result.sampled_final_balances)
        self.assertGreater(std_final, 10000)  # Alta variabilidade
        
        # Verificar métricas
        self.assertIsNotNone(result.percentile_stats)
        
        # Verificar cenários representativos
        self.assertGreater(len(result.representative_scenarios), 0)
        
        print("\n" + "="*60)
        print("TESTE DE INTEGRAÇÃO - MODO EXPERT COMPLETO")
        print("="*60)
        print(f"Capital inicial: R$ 100.000")
        print(f"Aporte mensal: R$ 1.000")
        print(f"Período: 10 anos")
        print(f"Simulações: {result.n_simulations:,}")
        print(f"Método: {result.simulation_method}")
        print("-"*60)
        print(f"Saldo determinístico: R$ {result.final_balance_det:,.2f}")
        print(f"Saldo médio MC: R$ {result.final_balance_mean:,.2f}")
        print(f"Intervalo: R$ {result.final_balance_min:,.2f} → R$ {result.final_balance_max:,.2f}")
        print("-"*60)
        ps = result.percentile_stats
        print(f"Percentis: P5={ps.p5:,.0f} | P25={ps.p25:,.0f} | P50={ps.p50:,.0f} | P75={ps.p75:,.0f} | P95={ps.p95:,.0f}")
        print("="*60)


if __name__ == '__main__':
    # Executar testes com verbosidade
    unittest.main(verbosity=2)

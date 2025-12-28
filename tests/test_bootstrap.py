"""
Testes Unitários - Módulo Bootstrap

Testa todas as funcionalidades do módulo core/bootstrap.py:
- MonthlyReturnData
- BootstrapEngine (Simple e Block)
- ACF e diagnóstico
- Importação/Exportação CSV
- Geração de cenários

Executar com: python -m tests.test_bootstrap
Ou diretamente: python tests/test_bootstrap.py
"""

import sys
import os
import unittest
import numpy as np

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bootstrap import (
    MonthlyReturnData,
    SyntheticScenariosResult,
    BootstrapEngine,
    BootstrapMethod,
    generate_monthly_template_csv,
    parse_monthly_csv,
    export_scenarios_csv,
    import_scenarios_csv,
    estimate_generation_time,
    format_time_estimate,
    SyntheticDataConfig
)


class TestMonthlyReturnData(unittest.TestCase):
    """Testes para a classe MonthlyReturnData."""
    
    def setUp(self):
        """Dados de teste."""
        self.periods = [f'Jan/2017', 'Fev/2017', 'Mar/2017', 'Abr/2017',
                       'Mai/2017', 'Jun/2017', 'Jul/2017', 'Ago/2017',
                       'Set/2017', 'Out/2017', 'Nov/2017', 'Dez/2017']
        self.returns = np.array([1.5, 2.0, -0.5, 3.0, 1.0, 2.5, 
                                 1.8, -1.0, 2.2, 3.5, 1.2, 2.8])
    
    def test_creation(self):
        """Teste de criação básica."""
        data = MonthlyReturnData(periods=self.periods, returns=self.returns)
        
        self.assertEqual(data.n_months, 12)
        self.assertEqual(data.n_complete_years, 1)
        self.assertEqual(data.start_period, 'Jan/2017')
        self.assertEqual(data.end_period, 'Dez/2017')
    
    def test_validation_success(self):
        """Teste de validação com dados válidos."""
        data = MonthlyReturnData(periods=self.periods, returns=self.returns)
        is_valid, errors = data.validate()
        
        self.assertTrue(is_valid)
        self.assertEqual(len([e for e in errors if not e.startswith("⚠️")]), 0)
    
    def test_validation_minimum_months(self):
        """Teste de validação com menos de 12 meses."""
        data = MonthlyReturnData(
            periods=['Jan/2017', 'Fev/2017'],
            returns=np.array([1.0, 2.0])
        )
        is_valid, errors = data.validate()
        
        self.assertFalse(is_valid)
        self.assertTrue(any('12 meses' in e for e in errors))
    
    def test_validation_extreme_values(self):
        """Teste de validação com valores extremos (>50%)."""
        extreme_returns = np.array([60.0] + [1.0] * 11)
        data = MonthlyReturnData(periods=self.periods, returns=extreme_returns)
        is_valid, errors = data.validate()
        
        # É válido mas tem warning
        self.assertTrue(is_valid)
        self.assertTrue(any('⚠️' in e for e in errors))
    
    def test_validation_invalid_range(self):
        """Teste de validação com retorno inválido (>1000%)."""
        invalid_returns = np.array([1500.0] + [1.0] * 11)
        data = MonthlyReturnData(periods=self.periods, returns=invalid_returns)
        is_valid, errors = data.validate()
        
        self.assertFalse(is_valid)
    
    def test_statistics(self):
        """Teste de cálculo de estatísticas."""
        data = MonthlyReturnData(periods=self.periods, returns=self.returns)
        stats = data.get_statistics()
        
        self.assertIn('mean', stats)
        self.assertIn('std', stats)
        self.assertIn('skewness', stats)
        self.assertAlmostEqual(stats['mean'], np.mean(self.returns), places=4)


class TestBootstrapEngine(unittest.TestCase):
    """Testes para o BootstrapEngine."""
    
    def setUp(self):
        """Dados de teste com 24 meses."""
        # Simular 24 meses de retornos
        np.random.seed(42)
        self.periods = []
        for year in [2017, 2018]:
            for month in ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']:
                self.periods.append(f'{month}/{year}')
        
        # Retornos com alguma autocorrelação
        self.returns = np.array([
            1.5, 1.8, 2.0, 2.2, 1.9, 1.5,  # Tendência de alta
            -0.5, -0.8, -0.3, 0.5, 1.0, 1.5,  # Recuperação
            2.0, 2.5, 3.0, 2.8, 2.5, 2.0,  # Alta novamente
            1.5, 1.0, 0.5, 0.8, 1.2, 1.8   # Estabilização
        ])
        
        self.data = MonthlyReturnData(periods=self.periods, returns=self.returns)
        self.engine = BootstrapEngine(self.data)
    
    def test_acf_calculation(self):
        """Teste de cálculo de ACF."""
        acf = self.engine.calculate_acf(max_lag=5)
        
        self.assertEqual(len(acf), 6)  # lag 0 a 5
        self.assertEqual(acf[0], 1.0)  # ACF(0) sempre = 1
        self.assertTrue(all(-1 <= a <= 1 for a in acf))
    
    def test_optimal_block_size(self):
        """Teste de cálculo de tamanho ótimo de bloco."""
        block_size = self.engine.calculate_optimal_block_size()
        
        self.assertGreaterEqual(block_size, 1)
        self.assertLessEqual(block_size, 6)
    
    def test_acf_diagnosis(self):
        """Teste de diagnóstico de ACF."""
        diagnosis = self.engine.get_acf_diagnosis()
        
        self.assertIn('acf_lag1', diagnosis)
        self.assertIn('optimal_block_size', diagnosis)
        self.assertIn('interpretation', diagnosis)
        self.assertIn('recommendation', diagnosis)
        self.assertIn('use_block_bootstrap', diagnosis)
    
    def test_simple_bootstrap_generation(self):
        """Teste de geração via Bootstrap Simples."""
        result = self.engine.generate_simple_bootstrap(
            n_scenarios=1000,
            seed=42
        )
        
        self.assertIsInstance(result, SyntheticScenariosResult)
        self.assertEqual(result.n_scenarios, 1000)
        self.assertEqual(result.method, 'bootstrap')
        self.assertIsNone(result.block_size)
        self.assertEqual(len(result.annual_returns), 1000)
    
    def test_block_bootstrap_generation(self):
        """Teste de geração via Block Bootstrap."""
        result = self.engine.generate_block_bootstrap(
            n_scenarios=1000,
            block_size=3,
            seed=42
        )
        
        self.assertIsInstance(result, SyntheticScenariosResult)
        self.assertEqual(result.n_scenarios, 1000)
        self.assertEqual(result.method, 'block_bootstrap')
        self.assertEqual(result.block_size, 3)
    
    def test_unified_generate_method(self):
        """Teste do método unificado generate()."""
        result_simple = self.engine.generate(
            method=BootstrapMethod.SIMPLE,
            n_scenarios=500,
            seed=42
        )
        
        result_block = self.engine.generate(
            method=BootstrapMethod.BLOCK,
            n_scenarios=500,
            block_size=3,
            seed=42
        )
        
        self.assertEqual(result_simple.method, 'bootstrap')
        self.assertEqual(result_block.method, 'block_bootstrap')
    
    def test_reproducibility_with_seed(self):
        """Teste de reprodutibilidade com seed."""
        result1 = self.engine.generate_simple_bootstrap(n_scenarios=100, seed=12345)
        result2 = self.engine.generate_simple_bootstrap(n_scenarios=100, seed=12345)
        
        np.testing.assert_array_equal(result1.annual_returns, result2.annual_returns)
    
    def test_statistics_calculation(self):
        """Teste de cálculo de estatísticas no resultado."""
        result = self.engine.generate_simple_bootstrap(n_scenarios=5000, seed=42)
        
        # Verificar que estatísticas foram calculadas
        self.assertNotEqual(result.mean, 0.0)
        self.assertNotEqual(result.std, 0.0)
        self.assertTrue(result.p5 < result.p50 < result.p95)
        self.assertTrue(result.min_val <= result.p5)
        self.assertTrue(result.max_val >= result.p95)
    
    def test_annual_return_composition(self):
        """Teste de composição correta de retornos anuais."""
        # Criar dados simples para verificar composição
        simple_returns = np.array([10.0] * 12)  # 10% ao mês
        simple_data = MonthlyReturnData(
            periods=self.periods[:12],
            returns=simple_returns
        )
        simple_engine = BootstrapEngine(simple_data)
        
        # Com 10% ao mês, esperamos ~214% ao ano ((1.1)^12 - 1)
        result = simple_engine.generate_simple_bootstrap(n_scenarios=100, seed=42)
        
        # Todos os cenários devem ter o mesmo retorno (mesmos dados)
        expected_annual = (1.10 ** 12 - 1) * 100  # ~213.84%
        
        # Como sorteamos com reposição do mesmo valor, todos são iguais
        np.testing.assert_array_almost_equal(
            result.annual_returns, 
            np.full(100, expected_annual),
            decimal=2
        )
    
    def test_progress_callback(self):
        """Teste de callback de progresso."""
        progress_values = []
        
        def callback(progress):
            progress_values.append(progress)
        
        self.engine.generate_simple_bootstrap(
            n_scenarios=1000,
            seed=42,
            progress_callback=callback
        )
        
        # Deve ter recebido múltiplos updates
        self.assertGreater(len(progress_values), 0)
        # Último deve ser 100 ou próximo
        self.assertGreaterEqual(progress_values[-1], 95)


class TestCSVFunctions(unittest.TestCase):
    """Testes para funções de CSV."""
    
    def test_generate_template(self):
        """Teste de geração de template CSV."""
        template = generate_monthly_template_csv()
        
        self.assertIn('Período', template)
        self.assertIn('Retorno (%)', template)
        self.assertIn('Jan/2017', template)
        self.assertIn('Dez/2025', template)
        
        # Verificar número de linhas (header + 108 meses)
        lines = template.strip().split('\n')
        self.assertEqual(len(lines), 109)
    
    def test_parse_csv(self):
        """Teste de parse de CSV."""
        csv_content = """Período;Retorno (%);Notas
Jan/2017;5.66;Primeiro mês
Fev/2017;2.30;
Mar/2017;-1.50;
Abr/2017;3.20;
Mai/2017;1.80;
Jun/2017;2.50;
Jul/2017;1.20;
Ago/2017;-0.80;
Set/2017;2.10;
Out/2017;3.00;
Nov/2017;1.50;
Dez/2017;2.80;"""
        
        data = parse_monthly_csv(csv_content)
        
        self.assertEqual(data.n_months, 12)
        self.assertEqual(data.periods[0], 'Jan/2017')
        self.assertAlmostEqual(data.returns[0], 5.66, places=2)
    
    def test_parse_csv_with_comma_decimal(self):
        """Teste de parse com vírgula como decimal."""
        csv_content = """Período;Retorno (%);Notas
Jan/2017;5,66;
Fev/2017;2,30;
Mar/2017;-1,50;
Abr/2017;3,20;
Mai/2017;1,80;
Jun/2017;2,50;
Jul/2017;1,20;
Ago/2017;-0,80;
Set/2017;2,10;
Out/2017;3,00;
Nov/2017;1,50;
Dez/2017;2,80;"""
        
        data = parse_monthly_csv(csv_content)
        
        self.assertAlmostEqual(data.returns[0], 5.66, places=2)
    
    def test_export_and_import_scenarios(self):
        """Teste de exportação e reimportação de cenários."""
        # Criar cenários
        np.random.seed(42)
        periods = [f'Jan/2017', 'Fev/2017', 'Mar/2017', 'Abr/2017',
                  'Mai/2017', 'Jun/2017', 'Jul/2017', 'Ago/2017',
                  'Set/2017', 'Out/2017', 'Nov/2017', 'Dez/2017']
        returns = np.random.randn(12) * 5 + 10
        
        data = MonthlyReturnData(periods=periods, returns=returns)
        engine = BootstrapEngine(data)
        result = engine.generate_simple_bootstrap(n_scenarios=500, seed=42)
        
        # Exportar
        csv_content = export_scenarios_csv(result, include_metadata=True)
        
        # Verificar metadados
        self.assertIn('# Método:', csv_content)
        self.assertIn('# Nº Cenários:', csv_content)
        
        # Reimportar
        imported_returns, metadata = import_scenarios_csv(csv_content)
        
        self.assertEqual(len(imported_returns), 500)
        np.testing.assert_array_almost_equal(
            imported_returns, 
            result.annual_returns,
            decimal=3
        )


class TestUtilityFunctions(unittest.TestCase):
    """Testes para funções utilitárias."""
    
    def test_estimate_generation_time(self):
        """Teste de estimativa de tempo."""
        time_1k = estimate_generation_time(1000)
        time_10k = estimate_generation_time(10000)
        time_100k = estimate_generation_time(100000)
        
        self.assertLess(time_1k, time_10k)
        self.assertLess(time_10k, time_100k)
    
    def test_format_time_estimate(self):
        """Teste de formatação de tempo."""
        self.assertEqual(format_time_estimate(0.5), '<1s')
        self.assertEqual(format_time_estimate(5), '~5s')
        self.assertEqual(format_time_estimate(65), '~1min')


class TestSyntheticDataConfig(unittest.TestCase):
    """Testes para SyntheticDataConfig."""
    
    def test_from_result(self):
        """Teste de criação a partir de resultado."""
        # Criar resultado
        np.random.seed(42)
        periods = [f'{m}/{y}' for y in [2017] for m in 
                  ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']]
        returns = np.random.randn(12) * 5 + 10
        
        data = MonthlyReturnData(periods=periods, returns=returns)
        engine = BootstrapEngine(data)
        result = engine.generate_simple_bootstrap(n_scenarios=100, seed=42)
        
        # Criar config
        config = SyntheticDataConfig.from_result(result)
        
        self.assertEqual(config.n_scenarios, 100)
        self.assertEqual(config.method, 'Bootstrap Histórico')
        self.assertIn('mean', config.statistics)


class TestIntegration(unittest.TestCase):
    """Testes de integração completa."""
    
    def test_full_workflow(self):
        """Teste do fluxo completo: dados → bootstrap → estatísticas."""
        # 1. Criar dados mensais (simulando 2017-2018)
        np.random.seed(42)
        periods = []
        for year in [2017, 2018]:
            for month in ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']:
                periods.append(f'{month}/{year}')
        
        # Retornos mensais realistas
        returns = np.random.randn(24) * 3 + 1  # ~1% média, ~3% std
        
        # 2. Criar estrutura de dados
        data = MonthlyReturnData(periods=periods, returns=returns)
        
        # 3. Validar
        is_valid, errors = data.validate()
        self.assertTrue(is_valid)
        
        # 4. Criar engine e diagnosticar
        engine = BootstrapEngine(data)
        diagnosis = engine.get_acf_diagnosis()
        
        # 5. Gerar cenários (método baseado no diagnóstico)
        if diagnosis['use_block_bootstrap']:
            result = engine.generate_block_bootstrap(
                n_scenarios=5000,
                block_size=diagnosis['optimal_block_size'],
                seed=42
            )
        else:
            result = engine.generate_simple_bootstrap(
                n_scenarios=5000,
                seed=42
            )
        
        # 6. Verificar resultado
        self.assertEqual(result.n_scenarios, 5000)
        self.assertIsNotNone(result.mean)
        self.assertTrue(result.p5 < result.median < result.p95)
        
        # 7. Exportar e verificar
        csv = export_scenarios_csv(result)
        self.assertIn('Cenário', csv)
        
        # 8. Criar config para Monte Carlo
        config = SyntheticDataConfig.from_result(result)
        self.assertEqual(len(config.annual_returns), 5000)
        
        print("\n" + "="*60)
        print("TESTE DE INTEGRAÇÃO COMPLETO")
        print("="*60)
        print(f"Período fonte: {data.period_range}")
        print(f"Meses: {data.n_months}")
        print(f"ACF(1): {diagnosis['acf_lag1']:.4f}")
        print(f"Método usado: {result.get_method_display_name()}")
        print(f"Cenários gerados: {result.n_scenarios:,}")
        print(f"Tempo: {result.generation_time:.2f}s")
        print(f"\nEstatísticas dos Cenários Anuais:")
        print(f"  Média: {result.mean:.2f}%")
        print(f"  Desvio: {result.std:.2f}%")
        print(f"  P5: {result.p5:.2f}% | P95: {result.p95:.2f}%")
        print(f"  Min: {result.min_val:.2f}% | Max: {result.max_val:.2f}%")
        print("="*60)


def run_tests():
    """Executa todos os testes com output detalhado."""
    print("\n" + "="*70)
    print("🧪 TESTES UNITÁRIOS - MÓDULO BOOTSTRAP")
    print("="*70 + "\n")
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar todas as classes de teste
    suite.addTests(loader.loadTestsFromTestCase(TestMonthlyReturnData))
    suite.addTests(loader.loadTestsFromTestCase(TestBootstrapEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestCSVFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestSyntheticDataConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Executar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO DOS TESTES")
    print("="*70)
    print(f"  Testes executados: {result.testsRun}")
    print(f"  ✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  ❌ Falhas: {len(result.failures)}")
    print(f"  ⚠️ Erros: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result


if __name__ == '__main__':
    run_tests()

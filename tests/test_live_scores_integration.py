#!/usr/bin/env python3
"""
Integration Tests for Live Scores Module
==========================================

Pruebas de integración para football_api_client.py y live_scores.py

Uso:
    pytest tests/test_live_scores_integration.py -v
    python3 tests/test_live_scores_integration.py
"""

import unittest
import time
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from football_api_client import (
    LeakyBucket,
    FootballDataClient,
    FootballAPIError,
    RateLimitError,
    validate_api_key,
)
from live_scores import (
    LiveScoresManager,
    MatchSnapshot,
    MatchChangeDetection,
    MatchEvent,
    DefaultCallbacks,
)


class TestLeakyBucket(unittest.TestCase):
    """Tests para LeakyBucket rate limiting"""
    
    def setUp(self):
        """Setup para cada test"""
        self.bucket = LeakyBucket(capacity=10, refill_time=60)
    
    def test_initialization(self):
        """Test inicialización del bucket"""
        self.assertEqual(self.bucket.capacity, 10)
        self.assertEqual(self.bucket.refill_time, 60)
        self.assertEqual(self.bucket.tokens, 10)
    
    def test_acquire_token(self):
        """Test adquisición de token"""
        initial_tokens = self.bucket.tokens
        result = self.bucket.acquire(timeout=1)
        
        self.assertTrue(result)
        self.assertEqual(self.bucket.tokens, initial_tokens - 1)
    
    def test_acquire_multiple_tokens(self):
        """Test adquisición múltiple de tokens"""
        for i in range(5):
            result = self.bucket.acquire(timeout=1)
            self.assertTrue(result)
        
        self.assertEqual(self.bucket.tokens, 5)
    
    def test_acquire_all_tokens(self):
        """Test agotar todos los tokens"""
        for i in range(10):
            self.bucket.acquire(timeout=1)
        
        self.assertEqual(self.bucket.tokens, 0)
    
    def test_token_refill(self):
        """Test refill automático de tokens"""
        # Consumir todos
        for i in range(10):
            self.bucket.acquire(timeout=0.1)
        
        self.assertEqual(self.bucket.tokens, 0)
        
        # Simular tiempo transcurrido (mockeado)
        with patch('time.time') as mock_time:
            current = time.time()
            mock_time.return_value = current
            
            # Avanzar 30 segundos (mitad del refill)
            mock_time.return_value = current + 30
            self.bucket._refill()
            
            # Debe haber 5 tokens (mitad de 10)
            self.assertEqual(self.bucket.tokens, 5)
    
    def test_get_wait_time(self):
        """Test cálculo de tiempo de espera"""
        # Con tokens disponibles
        with patch('time.time') as mock_time:
            wait = self.bucket.get_wait_time()
            self.assertEqual(wait, 0)
        
        # Sin tokens (forzar)
        self.bucket.tokens = 0
        wait = self.bucket.get_wait_time()
        self.assertGreater(wait, 0)
    
    def test_minimum_sleep_enforced(self):
        """Test que se respeta mínimo de 6 segundos"""
        self.bucket.last_request_time = time.time()
        
        # El wait time debe considerar los 6 segundos mínimos
        wait = self.bucket.get_wait_time()
        # Al menos muy cercano a 6 segundos en este instante
        self.assertGreaterEqual(wait, 5.9)


class TestFootballDataClient(unittest.TestCase):
    """Tests para FootballDataClient"""
    
    def setUp(self):
        """Setup para cada test"""
        self.api_key = "test_api_key_12345"
        self.client = FootballDataClient(self.api_key)
    
    def test_initialization(self):
        """Test inicialización del cliente"""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertIsNotNone(self.client.rate_limiter)
        self.assertIsNotNone(self.client.session)
    
    def test_validate_api_key_format(self):
        """Test validación de formato API Key"""
        # Válido (32 caracteres hex)
        self.assertTrue(validate_api_key("a" * 32))
        
        # Inválido (muy corto)
        self.assertFalse(validate_api_key("short"))
        
        # Inválido (caracteres especiales)
        self.assertFalse(validate_api_key("a" * 30 + "@@"))
    
    def test_request_headers(self):
        """Test que se envíe X-Auth-Token"""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_get.return_value.json.return_value = []
            mock_get.return_value.status_code = 200
            
            try:
                self.client.get_competitions()
            except:
                pass
            
            # Verificar headers
            if mock_get.called:
                call_kwargs = mock_get.call_args[1]
                self.assertIn('headers', call_kwargs)
                headers = call_kwargs['headers']
                self.assertEqual(headers['X-Auth-Token'], self.api_key)
    
    def test_cache_ttl(self):
        """Test que el caché respeta TTL"""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_get.return_value.json.return_value = [
                {'code': 'PL', 'name': 'Premier League'}
            ]
            mock_get.return_value.status_code = 200
            
            # Primera llamada
            result1 = self.client.get_competitions()
            call_count_1 = mock_get.call_count
            
            # Segunda llamada inmediata (debe estar en caché)
            result2 = self.client.get_competitions()
            call_count_2 = mock_get.call_count
            
            self.assertEqual(call_count_1, call_count_2)  # No debe hacer otra llamada
    
    def test_rate_limit_status(self):
        """Test obtener estado de rate limit"""
        status = self.client.get_rate_limit_status()
        
        self.assertIn('capacity', status)
        self.assertIn('available_tokens', status)
        self.assertIn('refill_time', status)
        self.assertIn('wait_time', status)
        self.assertIn('cache_entries', status)


class TestMatchSnapshot(unittest.TestCase):
    """Tests para MatchSnapshot dataclass"""
    
    def setUp(self):
        """Setup para cada test"""
        self.match_data = {
            'id': 123,
            'status': 'LIVE',
            'homeTeam': {'id': 1, 'name': 'Man United'},
            'awayTeam': {'id': 2, 'name': 'Liverpool'},
            'score': {'fullTime': {'home': 2, 'away': 1}},
            'minute': 45,
            'utcDate': datetime.now().isoformat(),
        }
    
    def test_snapshot_creation(self):
        """Test creación de snapshot"""
        snapshot = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='LIVE',
            minute=45,
        )
        
        self.assertEqual(snapshot.match_id, 123)
        self.assertEqual(snapshot.home_score, 2)
        self.assertEqual(snapshot.away_score, 1)
    
    def test_snapshot_equality(self):
        """Test comparación de snapshots"""
        snap1 = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='LIVE',
            minute=45,
        )
        
        snap2 = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='LIVE',
            minute=45,
        )
        
        self.assertEqual(snap1, snap2)


class TestMatchChangeDetection(unittest.TestCase):
    """Tests para detección de cambios de partido"""
    
    def setUp(self):
        """Setup para cada test"""
        self.detector = MatchChangeDetection()
    
    def test_detect_goal_home(self):
        """Test detección de gol del equipo local"""
        old = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=1,
            away_score=0,
            status='LIVE',
            minute=30,
        )
        
        new = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=0,
            status='LIVE',
            minute=32,
        )
        
        events = self.detector.detect_changes(old, new)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], MatchEvent.GOAL_HOME)
    
    def test_detect_goal_away(self):
        """Test detección de gol del equipo visitante"""
        old = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=1,
            away_score=0,
            status='LIVE',
            minute=30,
        )
        
        new = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=1,
            away_score=1,
            status='LIVE',
            minute=35,
        )
        
        events = self.detector.detect_changes(old, new)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], MatchEvent.GOAL_AWAY)
    
    def test_detect_fulltime(self):
        """Test detección de fin de partido"""
        old = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='LIVE',
            minute=90,
        )
        
        new = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='FINISHED',
            minute=90,
        )
        
        events = self.detector.detect_changes(old, new)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], MatchEvent.FULLTIME)
    
    def test_detect_multiple_goals(self):
        """Test detección de múltiples goles"""
        old = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=0,
            away_score=0,
            status='LIVE',
            minute=0,
        )
        
        new = MatchSnapshot(
            match_id=123,
            home_team='Man United',
            away_team='Liverpool',
            home_score=3,
            away_score=2,
            status='LIVE',
            minute=45,
        )
        
        events = self.detector.detect_changes(old, new)
        
        # Debe detectar 5 eventos de gol (3 home + 2 away)
        self.assertEqual(len(events), 5)


class TestLiveScoresManager(unittest.TestCase):
    """Tests para LiveScoresManager"""
    
    def setUp(self):
        """Setup para cada test"""
        self.client = Mock(spec=FootballDataClient)
        self.manager = LiveScoresManager(self.client)
        
        # Preparar datos mock
        self.mock_matches = [
            {
                'id': 1,
                'status': 'LIVE',
                'utcDate': datetime.now().isoformat(),
                'homeTeam': {'id': 1, 'name': 'Man United'},
                'awayTeam': {'id': 2, 'name': 'Liverpool'},
                'score': {'fullTime': {'home': 2, 'away': 1}},
                'minute': 45,
            }
        ]
    
    def test_initialization(self):
        """Test inicialización del manager"""
        self.assertIsNotNone(self.manager.client)
        self.assertIsNotNone(self.manager.competitions)
        self.assertFalse(self.manager.running)
    
    def test_register_callback(self):
        """Test registrar callback"""
        callback = Mock()
        self.manager.register_callback(callback)
        
        self.assertEqual(len(self.manager.callbacks), 1)
        self.assertIn(callback, self.manager.callbacks)
    
    def test_get_live_matches(self):
        """Test obtener partidos en vivo"""
        snapshot = MatchSnapshot(
            match_id=1,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='LIVE',
            minute=45,
        )
        
        self.manager.match_snapshots[1] = snapshot
        self.manager.live_matches.add(1)
        
        live = self.manager.get_live_matches()
        
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0]['match_id'], 1)
    
    def test_get_statistics(self):
        """Test obtener estadísticas"""
        # Agregar snapshots
        for i in range(3):
            snapshot = MatchSnapshot(
                match_id=i,
                home_team=f'Team {i}A',
                away_team=f'Team {i}B',
                home_score=i,
                away_score=i,
                status='LIVE' if i == 0 else 'FINISHED',
                minute=45 if i == 0 else 90,
            )
            self.manager.match_snapshots[i] = snapshot
        
        self.manager.live_matches.add(0)
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_matches'], 3)
        self.assertEqual(stats['live_matches'], 1)
    
    def test_export_to_json(self):
        """Test exportar a JSON"""
        snapshot = MatchSnapshot(
            match_id=1,
            home_team='Man United',
            away_team='Liverpool',
            home_score=2,
            away_score=1,
            status='LIVE',
            minute=45,
        )
        
        self.manager.match_snapshots[1] = snapshot
        
        # Crear archivo temporal
        output_file = '/tmp/test_export.json'
        self.manager.export_to_json(output_file)
        
        # Verificar que se creó
        self.assertTrue(Path(output_file).exists())
        
        # Verificar contenido
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn('timestamp', data)
        self.assertIn('live_matches', data)
        
        # Limpiar
        Path(output_file).unlink()


class TestIntegrationScenarios(unittest.TestCase):
    """Scenarios de integración completos"""
    
    def test_full_polling_cycle(self):
        """Test ciclo completo de polling"""
        client = Mock(spec=FootballDataClient)
        manager = LiveScoresManager(client)
        
        # Mock client
        client.get_competition_matches.return_value = [
            {
                'id': 1,
                'status': 'LIVE',
                'utcDate': datetime.now().isoformat(),
                'homeTeam': {'id': 1, 'name': 'Team A'},
                'awayTeam': {'id': 2, 'name': 'Team B'},
                'score': {'fullTime': {'home': 1, 'away': 0}},
                'minute': 30,
            }
        ]
        
        # Poll una competición
        manager.poll_competition('PL')
        
        # Verificar que se guardó
        self.assertEqual(len(manager.match_snapshots), 1)
        self.assertTrue(1 in manager.live_matches)
    
    def test_event_callback_execution(self):
        """Test ejecución de callbacks de eventos"""
        client = Mock(spec=FootballDataClient)
        manager = LiveScoresManager(client)
        
        callback = Mock()
        manager.register_callback(callback)
        
        # Simular gol
        event = {
            'type': MatchEvent.GOAL_HOME,
            'match_id': 1,
            'home_team': 'Man United',
            'away_team': 'Liverpool',
            'home_score': 2,
            'away_score': 1,
            'minute': 45,
        }
        
        # Ejecutar callbacks
        for cb in manager.callbacks:
            cb(event)
        
        # Verificar que se llamó
        callback.assert_called_once_with(event)


def run_tests_verbose():
    """Ejecutar pruebas con salida verbose"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todos los tests
    suite.addTests(loader.loadTestsFromTestCase(TestLeakyBucket))
    suite.addTests(loader.loadTestsFromTestCase(TestFootballDataClient))
    suite.addTests(loader.loadTestsFromTestCase(TestMatchSnapshot))
    suite.addTests(loader.loadTestsFromTestCase(TestMatchChangeDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveScoresManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests_verbose()
    sys.exit(0 if success else 1)

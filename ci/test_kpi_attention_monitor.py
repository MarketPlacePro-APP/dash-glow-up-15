import unittest
from datetime import datetime, timedelta, timezone
from kpi_attention_monitor import decide, due_cycle

class AttentionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 14, 2, 45, tzinfo=timezone.utc)
        self.good = {'reachable': True, 'completed_at': self.now.isoformat(), 'result': 'deployed'}
        self.bad = dict(self.good, result='failed')

    def test_healthy_silent(self):
        s = decide(self.good, {}, self.now)
        self.assertEqual(s['health'], 'healthy')
        self.assertFalse(s['notify'])

    def test_routine_failure_retains_failure_without_email(self):
        s = decide(self.bad, {}, self.now)
        self.assertEqual(s['health'], 'degraded')
        self.assertEqual(s['observation']['result'], 'failed')
        self.assertFalse(s['notify'])

    def test_repeated_source_failure_silent(self):
        s = decide(self.bad, {}, self.now)
        for h in range(1, 24):
            s = decide(self.bad, s, self.now + timedelta(hours=h))
            self.assertFalse(s['notify'])

    def test_prolonged_failure_once(self):
        s = decide(self.bad, {}, self.now)
        s = decide(self.bad, s, self.now + timedelta(hours=24))
        self.assertTrue(s['notify'])
        for h in (25, 26, 48, 72):
            s = decide(self.bad, s, self.now + timedelta(hours=h))
            self.assertFalse(s['notify'])
            self.assertEqual(s['health'], 'degraded')

    def test_access_loss_ninety_minutes_once(self):
        bad = {'reachable': False, 'error': 'HTTPError'}
        s = decide(bad, {}, self.now)
        self.assertFalse(s['notify'])
        s = decide(bad, s, self.now + timedelta(minutes=89))
        self.assertFalse(s['notify'])
        s = decide(bad, s, self.now + timedelta(minutes=90))
        self.assertTrue(s['notify'])
        s = decide(bad, s, self.now + timedelta(minutes=120))
        self.assertFalse(s['notify'])

    def test_real_recovery_rearms(self):
        s = decide(self.bad, {}, self.now)
        s = decide(self.bad, s, self.now + timedelta(days=1))
        self.assertTrue(s['notify'])
        later = self.now + timedelta(days=1, hours=1)
        s = decide(dict(self.good, completed_at=later.isoformat()), s, later)
        self.assertFalse(s['notify'])
        self.assertEqual(s['notified'], [])
        s = decide(self.bad, s, later + timedelta(hours=1))
        s = decide(self.bad, s, later + timedelta(hours=25))
        self.assertTrue(s['notify'])

    def test_stale_success_is_not_recovery(self):
        old = dict(self.good, completed_at=(self.now-timedelta(days=1)).isoformat())
        self.assertEqual(decide(old, {}, self.now)['health'], 'degraded')

    def test_no_change_is_healthy(self):
        self.assertEqual(decide(dict(self.good, result='no_change'), {}, self.now)['health'], 'healthy')

    def test_future_or_naive_timestamp_rejected(self):
        for ts in ((self.now+timedelta(days=1)).isoformat(), '2026-09-14T02:45:00', 'bad'):
            self.assertEqual(decide(dict(self.good, completed_at=ts), {}, self.now)['health'], 'degraded')

    def test_offline_after_stale_is_new_severity(self):
        s = decide(self.bad, {}, self.now)
        s = decide(self.bad, s, self.now+timedelta(hours=24))
        s = decide({'reachable': False}, s, self.now+timedelta(hours=25))
        s = decide({'reachable': False}, s, self.now+timedelta(hours=27))
        self.assertTrue(s['notify'])
        self.assertEqual(set(s['notified']), {'access', 'freshness'})

    def test_schedule_grace(self):
        self.assertEqual(due_cycle(self.now).hour, 16)
        self.assertEqual(due_cycle(self.now+timedelta(hours=1)).hour, 20)

if __name__ == '__main__':
    unittest.main()

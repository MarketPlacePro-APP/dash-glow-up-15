#!/usr/bin/env python3
"""Channel identity must survive renames without silently trusting reused names."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import slack_channel_history as collector

ID = 'C09Q2B8SNTX'


class ChannelIdentityTests(unittest.TestCase):
    def test_rename_and_name_reuse_preserve_identity(self):
        for channels, expected in [
            ({'teamwollaston': ID}, ID),
            ({'teamdent': ID}, ID),
            ({'teamdent': 'C_WRONG', 'teamwollaston': ID}, ID),
            ({'teamdent': 'C_WRONG'}, None),
            ({'eventstats': 'C_OTHER'}, None),
        ]:
            with self.subTest(channels=channels):
                source = dict(channels)
                resolved = collector.apply_known_channel_identities(source)
                self.assertEqual(resolved.get('teamdent'), expected)
                self.assertEqual(source, channels)
                for name, value in channels.items():
                    if name != 'teamdent':
                        self.assertEqual(resolved[name], value)

    def test_paginated_lookup_preserves_legacy_records_and_failure_gate(self):
        for available, can_read in [(True, True), (False, True), (True, False)]:
            with self.subTest(available=available, can_read=can_read), tempfile.TemporaryDirectory() as tmp:
                calls = []
                def api(method, token, params):
                    calls.append((method, dict(params)))
                    if method == 'conversations.list':
                        self.assertEqual(params['exclude_archived'], 'true')
                        if not params.get('cursor'):
                            return {'ok': True, 'channels': [{'name': 'teamdent', 'id': 'C_WRONG'}], 'response_metadata': {'next_cursor': 'page2'}}
                        return {'ok': True, 'channels': [{'name': 'teamwollaston', 'id': ID}] if available else []}
                    self.assertEqual(params['channel'], ID)
                    if not can_read:
                        return {'ok': False, 'error': 'not_in_channel'}
                    return {'ok': True, 'messages': [{'ts': '1750000000.000001', 'text': 'Verified source fixture'}]}
                out, status = Path(tmp) / 'bundle.txt', Path(tmp) / 'status.json'
                argv = ['collector', 'teamdent', '--out', str(out), '--status-out', str(status)]
                with patch.object(collector, 'slack_get', api), patch.dict(os.environ, {'SLACK_BOT_TOKEN': 'fixture'}), patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                    code = collector.main()
                row = json.loads(status.read_text())['channels']['teamdent']
                self.assertTrue(row['required'])
                if available and can_read:
                    self.assertEqual(code, 0)
                    self.assertEqual(row['status'], 'ok_fresh')
                    self.assertIn('--- #teamdent ', out.read_text())
                    self.assertNotIn('--- #teamwollaston ', out.read_text())
                else:
                    self.assertEqual(code, 2)
                    self.assertEqual(row['status'], 'failed')
                self.assertEqual(calls[1][1]['cursor'], 'page2')


if __name__ == '__main__':
    unittest.main()

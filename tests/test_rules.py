import unittest
from unittest.mock import MagicMock, patch

from fpermenf import rules

class RulesTestCase(unittest.TestCase):
    def test_load_builds_rules(self):
        obj = [{
            'description': 'test rule',
            'match': [{'file_type': 'regular'}],
            'state': [{'owner': 'marshall'}]
        }]
        with patch('builtins.open'), \
             patch('json.load', MagicMock(return_value=obj)):
            r = rules.load('')
            self.assertEqual(r[0].description, 'test rule')
            self.assertEqual(r[0].match, [{'file_type': 'regular'}])
            self.assertEqual(r[0].state, [{'owner': 'marshall'}])

    def test_applicable_matches_correctly(self):
        self.assertTrue(rules.applicable('/usr/media/video', '/usr/media/video'))
        self.assertTrue(rules.applicable('/usr/media', '/usr/media/video'))
        self.assertFalse(rules.applicable('/usr/media/books', '/usr/media/video'))
        self.assertFalse(rules.applicable('/usr/media/video/sub', '/usr/media/video'))

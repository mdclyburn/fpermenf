import unittest
from unittest.mock import MagicMock, Mock, patch

from fpermenf import attr, rules

class RulesTestCase(unittest.TestCase):
    def test_Rule_matches_checks_criteria(self):
        r = rules.Rule('a rule', {'file_type': 'regular'})
        with patch('fpermenf.attr.fileType', return_value=True):
            self.assertTrue(r.matches('/a'))
            attr.fileType.assert_called_with('/a', 'regular')

        with patch('fpermenf.attr.fileType', return_value=False):
            self.assertFalse(r.matches('/b'))
            attr.fileType.assert_called_with('/b', 'regular')

    def test_Rule_matches_empty_criteria(self):
        r = rules.Rule('rule/no matches')
        self.assertTrue(r.matches('/a'))

    def test_Rule_matches_invalid_exception(self):
        r = rules.Rule('invalid match rule', {'bad-match': ''})
        # self.assertRaises(Exception, lambda: r.matches('/a'))
        with self.assertRaises(Exception,
                               msg="'bad-match' is not a valid match option.") as c:
            r.matches('/a')

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

    def test_merge_state_combines_states(self):
        rules_to_merge = \
            [rules.Rule('Rule A', {"file_type": "regular"}, {"mode": "444"}),
             rules.Rule('Rule B', {"file_type": "regular"}, {"owner": "root"}),
             rules.Rule('Rule C', {"file_type": "regular"}, {"group": "wheel"})]

        self.assertEqual(rules.merge_state(rules_to_merge),
                         {"mode": "444",
                          "owner": "root",
                          "group": "wheel"})

    def test_merge_state_overrides_previous_states(self):
        rules_to_merge = \
            [rules.Rule('Rule A', {"file_type": "regular"}, {"owner": "media"}),
             rules.Rule('Rule B', {"file_type": "regular"}, {"owner": "root"}),
             rules.Rule('Rule C', {"file_type": "regular"}, {"group": "wheel"})]

        self.assertEqual(rules.merge_state(rules_to_merge),
                         {"owner": "root",
                          "group": "wheel"})

    def test_apply_applies_changes(self):
        r = rules.Rule('rule-1', {'file_type': 'regular'}, {'owner': 'root'})
        paths = ['/a', '/b', '/c']
        r.matches = Mock(return_value=True)

        with patch('builtins.print'), \
             patch('fpermenf.attr.isOwner', return_value=False), \
             patch('fpermenf.attr.setOwner'):
            rules.apply([r], paths, False)
            attr.isOwner.assert_any_call('/a', 'root')
            attr.setOwner.assert_any_call('/a', 'root')
            attr.isOwner.assert_any_call('/b', 'root')
            attr.setOwner.assert_any_call('/b', 'root')
            attr.isOwner.assert_any_call('/c', 'root')
            attr.setOwner.assert_any_call('/c', 'root')

        r.matches.assert_any_call('/a')
        r.matches.assert_any_call('/b')
        r.matches.assert_any_call('/c')

    def test_apply_respects_dry_run(self):
        r = rules.Rule('rule-1', {'file_type': 'regular'}, {'owner': 'root'})
        r.matches = Mock(return_value=True)

        with patch('builtins.print'), \
             patch('fpermenf.attr.isOwner', return_value=False), \
             patch('fpermenf.attr.setOwner'):
            rules.apply([r], ['/a'], True)
            attr.isOwner.assert_called_with('/a', 'root')
            attr.setOwner.assert_not_called()

    def test_apply_ignores_unsupported_state(self):
        r = rules.Rule('rule-1', {'file_type': 'regular'}, {'bad-state': 'val'})
        r.matches = Mock(return_value=True)

        with patch('builtins.print'):
            rules.apply([r], ['/a'], True)
            print.assert_called_with('  bad-state: warning: not recognized')

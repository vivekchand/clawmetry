"""Keep hosted Linux verification on a qualified image across workflow growth."""
from pathlib import Path
import re
import unittest


class HostedLinuxImage(unittest.TestCase):
    def test_linux_hosted_runner_selection_is_pinned(self):
        workflows = Path(__file__).parents[2] / '.github/workflows'
        unpinned = []
        for path in workflows.glob('*.yml'):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                uses_alias = ('ubuntu-latest' in line or
                              re.search(r'matrix\.(os|runner)\b', line))
                if re.match(r'\s*runs-on:', line) and uses_alias:
                    # Matrix aliases may retain stable check identities only
                    # when actual runner selection pins the qualified image.
                    if "&& 'ubuntu-24.04'" not in line:
                        unpinned.append(f'{path.name}:{number}')
        self.assertEqual(unpinned, [],
                         'Unqualified Linux image can remove Python/browser coverage')

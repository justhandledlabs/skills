import subprocess
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / 'scripts' / 'generate_env_example.py'
MARKER = 'SYNTHETIC_SECRET_938274'


class EnvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / '.env'
        self.output = self.root / '.env.example'

    def tearDown(self):
        self.temp.cleanup()

    def run_helper(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.source), *args],
                              capture_output=True, text=True)

    def check_case(self, value, accepted):
        self.source.write_bytes(value)
        for write in (False, True):
            with self.subTest(write=write):
                result = self.run_helper(*(['--write', '--output', str(self.output)] if write else []))
                self.assertEqual(accepted, result.returncode == 0, result.stderr)
                visible = result.stdout + result.stderr
                if self.output.exists():
                    visible += self.output.read_text()
                self.assertNotIn(MARKER, visible)
                self.assertEqual(value, self.source.read_bytes())
                if not accepted:
                    self.assertFalse(self.output.exists())

    def test_supported_forms(self):
        self.check_case((f'# {MARKER}\n  # {MARKER}\nexport KEY = "{MARKER}"\nURL=x # {MARKER}\nEMPTY=\n\n').encode(), True)
        self.assertEqual('KEY=\nURL=\nEMPTY=\n\n# Secret-looking keys to review: KEY\n', self.output.read_text())

    def test_multiline_rejected(self):
        self.check_case(f'KEY="begin\n{MARKER}\nend"\n'.encode(), False)

    def test_malformed_rejected(self):
        self.check_case(f'KEY=ok\n{MARKER}\n'.encode(), False)

    def test_invalid_encoding_rejected(self):
        self.check_case(b'KEY=\xff'+MARKER.encode(), False)

    def test_value_fragments_cannot_become_keys(self):
        for separator in ('\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029', '\r'):
            with self.subTest(separator=repr(separator)):
                self.check_case(('VALUE=first'+separator+MARKER+'=tail\n').encode('utf8'), False)

    def test_crlf_supported(self):
        self.check_case(('VALUE='+MARKER+'\r\nOTHER=example\r\n').encode(), True)
        self.assertEqual('VALUE=\nOTHER=\n', self.output.read_text())

    def test_bom_supported(self):
        self.check_case(b'\xef\xbb\xbfVALUE='+MARKER.encode()+b'\n', True)

    def test_backtick_multiline_rejected(self):
        self.check_case(('VALUE=`first\n'+MARKER+'=tail\nEND=last`\n').encode(), False)

    def test_single_quoted_trailing_backslash(self):
        self.check_case(("VALUE='"+MARKER+"\\'\n").encode(), True)

    def test_unrelated_hardlink_not_overwritten(self):
        self.source.write_text('VALUE='+MARKER)
        target = self.root / 'unrelated.txt'
        target.write_text('PRESERVE')
        try:
            self.output.hardlink_to(target)
        except OSError as exc:
            self.skipTest('Hard-link fixture unavailable: '+type(exc).__name__)
        result = self.run_helper('--write', '--force', '--output', str(self.output))
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('PRESERVE', target.read_text())

    def test_output_parent_link_rejected(self):
        self.source.write_text('VALUE='+MARKER)
        target = self.root / 'target'
        target.mkdir()
        link = self.root / 'linked'
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest('Symlink fixture unavailable: '+type(exc).__name__)
        result = self.run_helper('--write', '--output', str(link/'example'))
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((target/'example').exists())

    def test_output_errors_do_not_traceback(self):
        self.source.write_text('VALUE='+MARKER)
        for target in (self.root, self.root/'missing'/'example'):
            with self.subTest(target=target):
                result = self.run_helper('--write', '--force', '--output', str(target))
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn('Traceback', result.stderr)
                self.assertNotIn(MARKER, result.stderr)

    def test_existing_output_preserved_on_input_failure(self):
        self.source.write_text('invalid')
        self.output.write_text('PRESERVE')
        result = self.run_helper('--write', '--force', '--output', str(self.output))
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('PRESERVE', self.output.read_text())

    def test_source_alias_rejected(self):
        self.source.write_text('KEY='+MARKER)
        result = self.run_helper('--write', '--force', '--output', str(self.source))
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('KEY='+MARKER, self.source.read_text())

    def test_existing_output_requires_force(self):
        self.source.write_text('KEY='+MARKER)
        self.output.write_text('PRESERVE')
        self.assertNotEqual(0, self.run_helper('--write', '--output', str(self.output)).returncode)
        self.assertEqual('PRESERVE', self.output.read_text())
        self.assertEqual(0, self.run_helper('--write', '--force', '--output', str(self.output)).returncode)
        self.assertNotIn(MARKER, self.output.read_text())

    def test_hardlink_source_rejected(self):
        self.source.write_text('KEY='+MARKER)
        try:
            self.output.hardlink_to(self.source)
        except OSError as exc:
            self.skipTest('Fixture creation unavailable: '+type(exc).__name__)
        self.assertNotEqual(0, self.run_helper('--write', '--force', '--output', str(self.output)).returncode)
        self.assertEqual('KEY='+MARKER, self.source.read_text())

    def test_symlink_output_rejected(self):
        self.source.write_text('KEY='+MARKER)
        target = self.root / 'target.txt'
        target.write_text('PRESERVE')
        try:
            self.output.symlink_to(target)
        except OSError as exc:
            self.skipTest('Fixture creation unavailable: '+type(exc).__name__)
        self.assertNotEqual(0, self.run_helper('--write', '--force', '--output', str(self.output)).returncode)
        self.assertEqual('PRESERVE', target.read_text())

    def test_directory_input_rejected(self):
        self.source.mkdir()
        result = self.run_helper()
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn('Traceback', result.stderr)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO requires Unix')
    def test_fifo_input_rejected_without_blocking(self):
        os.mkfifo(self.source)
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.source)],
                                capture_output=True, text=True, timeout=5)
        self.assertNotEqual(0, result.returncode)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO requires Unix')
    def test_fifo_output_rejected_without_blocking(self):
        self.source.write_text('KEY='+MARKER)
        os.mkfifo(self.output)
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.source), '--write', '--force', '--output', str(self.output)],
                                capture_output=True, text=True, timeout=5)
        self.assertNotEqual(0, result.returncode)


if __name__ == '__main__':
    unittest.main()

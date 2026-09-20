import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec=importlib.util.spec_from_file_location('checker',Path(__file__).resolve().parents[1]/'scripts/check_package.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.z=self.root/'package.zip';self.m=self.root/'expected.json'
        self.expected={'skill/SKILL.md':b'fixture instructions','skill/run.py':b'raise RuntimeError("MUST NOT EXECUTE")'}
        self.manifest({'schema_version':1,'files':{k:c.sha(v) for k,v in self.expected.items()}})
        self.archive(self.expected)
    def manifest(self,obj):
        self.m.write_text(json.dumps(obj),encoding='utf-8');self.digest=c.sha(self.m.read_bytes())
    def archive(self,files):
        with zipfile.ZipFile(self.z,'w') as z:
            for k,v in files.items():z.writestr(k,v)
    def result(self):return c.compare(self.z,self.m,self.digest)
    def test_match_without_execution(self):
        r=self.result();self.assertEqual(r['status'],'MATCH');self.assertFalse(r['trust_source_authenticated']);self.assertEqual(r['content_safety'],'NOT_ASSESSED')
    def test_modified(self):
        self.archive({**self.expected,'skill/run.py':b'tampered'});self.assertEqual(self.result()['modified'],['skill/run.py'])
    def test_missing(self):
        self.archive({'skill/SKILL.md':self.expected['skill/SKILL.md']});self.assertEqual(self.result()['missing'],['skill/run.py'])
    def test_untracked_executable(self):
        self.archive({**self.expected,'skill/extra.exe':b'not executed'});self.assertEqual(self.result()['extra'],['skill/extra.exe'])
    def test_no_trust_anchor(self):self.assertEqual(c.compare(self.z,self.m,'')['status'],'CANNOT_ASSESS')
    def test_wrong_anchor(self):self.assertEqual(c.compare(self.z,self.m,'0'*64)['reason'],'manifest_digest_mismatch')
    def test_traversal(self):
        self.archive({'../outside.txt':b'x'});self.assertEqual(self.result()['reason'],'unsafe_path');self.assertFalse((self.root.parent/'outside.txt').exists())
    def test_portability(self):
        for name in ['C:/a','/abs','a/CON.txt','a/x.','a//b']:
            with self.subTest(name=name):
                self.archive({name:b'x'});self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_raw_backslash_member(self):
        self.archive({'a/b':b'x'})
        self.z.write_bytes(self.z.read_bytes().replace(b'a/b',b'a\\b'))
        self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_case_collision(self):
        self.archive({'a':b'1','A':b'2'});self.assertEqual(self.result()['reason'],'path_collision')
    def test_parent_case_collision(self):
        self.archive({'a':b'1','A/b':b'2'});self.assertEqual(self.result()['reason'],'path_collision')
    def test_unicode_collision(self):
        self.archive({'é':b'1','e\u0301':b'2'});self.assertEqual(self.result()['reason'],'path_collision')
    def test_symlink_member(self):
        i=zipfile.ZipInfo('link');i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16
        with zipfile.ZipFile(self.z,'w') as z:z.writestr(i,'../../private')
        self.assertEqual(self.result()['reason'],'linked_or_special_entry')
    def test_missing_input(self):
        self.assertEqual(c.compare(self.root/'absent.zip',self.m,self.digest)['status'],'CANNOT_ASSESS')
    def test_invalid_zip(self):
        self.z.write_bytes(b'not zip');self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_empty_zip(self):
        self.archive({});self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_duplicate_manifest_key(self):
        self.m.write_bytes(b'{"schema_version":1,"schema_version":1,"files":{}}');self.digest=c.sha(self.m.read_bytes());self.assertEqual(self.result()['reason'],'duplicate_manifest_key')
    def test_schema_bool_rejected(self):
        self.manifest({'schema_version':True,'files':{'a':'0'*64}});self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_deep_manifest_refused_without_crash(self):
        self.m.write_bytes(b'['*2000+b'0'+b']'*2000)
        self.digest=c.sha(self.m.read_bytes())
        self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_manifest_file_parent_conflict(self):
        self.manifest({'schema_version':1,'files':{'a':'0'*64,'A/b':'1'*64}})
        self.assertEqual(self.result()['status'],'CANNOT_ASSESS')
    def test_empty_directory_under_file(self):
        self.manifest({'schema_version':1,'files':{'a':c.sha(b'x')}})
        self.archive({'a':b'x','a/b/':b''})
        self.assertEqual(self.result()['reason'],'path_collision')
    def test_implicit_directory_alias(self):
        self.archive({'Tool/a':b'x','tool/b':b'y'})
        self.assertEqual(self.result()['reason'],'path_collision')
    def test_manifest_implicit_directory_alias(self):
        self.manifest({'schema_version':1,'files':{'Tool/a':'0'*64,'tool/b':'1'*64}})
        self.assertEqual(self.result()['reason'],'path_collision')
    def test_superscript_windows_device(self):
        self.archive({'COM¹.txt':b'x'})
        self.assertEqual(self.result()['reason'],'unsafe_path')
    def test_file_size_cap(self):
        with patch.object(c,'FILE_MAX',2):self.assertEqual(self.result()['reason'],'expanded_size_limit')
    def test_compression_bomb(self):
        with zipfile.ZipFile(self.z,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('data',b'0'*100000)
        self.assertEqual(self.result()['reason'],'expanded_size_limit')
    def test_no_source_leak(self):
        self.archive({'skill/SKILL.md':b'synthetic-secret-DO-NOT-PRINT'});self.assertNotIn('synthetic-secret',json.dumps(self.result()))
    def test_read_error(self):
        with patch.object(c,'read_local',side_effect=PermissionError('PRIVATE_PATH')):
            r=self.result();self.assertEqual(r['status'],'CANNOT_ASSESS');self.assertNotIn('PRIVATE_PATH',json.dumps(r))
    def test_changed_file(self):
        real=c.identity;calls=[0]
        def changed(s):
            calls[0]+=1
            return real(s)+(calls[0],)
        with patch.object(c,'identity',side_effect=changed):self.assertEqual(self.result()['reason'],'input_changed')

if __name__=='__main__':unittest.main()

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
builder, checker = module('build'), module('check_site')

class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'episodes').mkdir()
        for name in ['style.css','reader.js']:
            (self.root/name).write_text('',encoding='utf-8')
        (self.root/'originals-lock.json').write_text('{}')
        (self.root/'site-config.json').write_text(json.dumps({'default_gap':55,'episodes':{}}))
    def image(self, ep, name, color='white'):
        path = self.root/'episodes'/ep/name
        path.parent.mkdir(exist_ok=True)
        Image.new('RGB',(25,41),color).save(path)
        return path
    def build(self): return builder.build(self.root,self.root/'_site',self.root/'.cache')
    def test_natural_gaps_future_episodes_and_navigation(self):
        for ep in ['01','02','03','100','101']:
            for name in ['10.png','2.png','001.png']: self.image(ep,name)
        result = self.build()
        self.assertEqual([e['number'] for e in result['episodes']],[1,2,3,100,101])
        self.assertEqual([i['file'] for i in result['episodes'][0]['images']],['001.png','2.png','10.png'])
        checker.check(self.root/'_site')
        self.assertTrue((self.root/'_site/episode-100.html').exists())
    def test_original_correction_and_addition_publish_but_missing_cut_fails(self):
        path = self.image('01','001.png')
        (self.root/'originals-lock.json').write_text(json.dumps({'01':[{'file':path.name,'sha256':builder.digest(path)}]}))
        old = self.build()['episodes'][0]['images'][0]
        self.image('01','001.png','red')
        self.image('01','002.png','blue')
        episode = self.build()['episodes'][0]
        new = episode['images'][0]
        self.assertEqual(episode['count'],2)
        self.assertEqual(episode['revised_originals'],['001.png'])
        self.assertNotEqual(old['variants'][0]['url'],new['variants'][0]['url'])
        self.assertNotEqual(old['original_url'],new['original_url'])
        self.assertEqual(new['sha256'],builder.digest(path))
        with Image.open(self.root/'_site'/new['variants'][0]['url']) as im:
            self.assertEqual(im.convert('RGB').getpixel((0,0)),(255,0,0))
        checker.check(self.root/'_site')
        path.unlink()
        with self.assertRaisesRegex(ValueError,'기존 컷 누락'): self.build()
    def test_lossless_cache_and_source_unchanged(self):
        path = self.image('01','한글 2.png')
        before = builder.digest(path)
        directory, info, hit = builder.optimize(path,self.root/'.cache')
        self.assertFalse(hit)
        self.assertTrue(info['native_pixel_exact'])
        _, _, hit = builder.optimize(path,self.root/'.cache')
        self.assertTrue(hit)
        # Corrupt cache must regenerate, not silently publish a broken image.
        (directory/info['variants'][0]['name']).write_bytes(b'broken')
        _, _, hit = builder.optimize(path,self.root/'.cache')
        self.assertFalse(hit)
        self.assertEqual(builder.digest(path),before)
        self.build(); checker.check(self.root/'_site')
    def test_reject_empty_and_duplicate_episode(self):
        (self.root/'episodes/03').mkdir()
        with self.assertRaisesRegex(ValueError,'없는 회차'): self.build()
        self.image('03','1.png'); self.image('3','1.png')
        with self.assertRaisesRegex(ValueError,'회차 번호 중복'): self.build()
    def test_reject_duplicate_numeric_cut_names(self):
        self.image('01','01.png'); self.image('01','1.jpg')
        with self.assertRaisesRegex(ValueError,'컷 번호'): self.build()
    def test_duplicate_content_warns_but_does_not_delete(self):
        self.image('01','1.png'); self.image('01','2.png')
        episode = self.build()['episodes'][0]
        self.assertEqual(episode['count'],2)
        self.assertEqual(len(episode['warnings']),1)

if __name__ == '__main__': unittest.main()

"""Verify the published sample files match the catalog and robot removal is real."""
import csv
import hashlib
import json
from pathlib import Path
import unittest
from import_market import import_stereo_datasets
ROOT=Path(__file__).resolve().parents[1]

class MarketSampleTests(unittest.TestCase):
    def test_sources_and_catalog_share_the_same_retained_robot_ids(self):
        source=json.loads((ROOT/'data/maniformer_data_market.json').read_text())
        catalog=json.loads((ROOT/'data/market_catalog.json').read_text())
        with (ROOT/'data/maniformer_data_market.csv').open(encoding='utf-8-sig') as f:
            csv_ids={int(r['id']) for r in csv.DictReader(f)}
        ids={r['id'] for r in source['records']}
        self.assertEqual(csv_ids,ids)
        self.assertEqual(ids,{r['id'] for r in catalog['records'] if r['source_id']=='maniformer'})
        self.assertEqual(catalog['collections'],{'human_stereo':4,'robot_real':60,'robot_sim':55})
        self.assertEqual(len(catalog['records']),119)
        self.assertEqual(sum(r['data_type']!='仿真' for r in source['records']),60)

    def test_sample_summary_counts_and_download_hashes_match_real_files(self):
        payload=json.loads((ROOT/'data/eyecatcher_stereo_datasets.json').read_text())
        for dataset in payload['datasets']:
            with self.subTest(dataset=dataset['dataset_id']):
                summary=json.loads((ROOT/dataset['sample_data_url']).read_text())
                for file in summary['files']:
                    p=ROOT/file['url']
                    self.assertEqual(p.stat().st_size,file['bytes'])
                    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),file['sha256'])
                    if file['path'].endswith('.csv'):
                        with p.open() as f: rows=list(csv.DictReader(f))
                        expected=summary['imu_samples'] if file['path']=='imu/imu.csv' else summary['frames']['left']
                        self.assertEqual(len(rows),expected)
                self.assertFalse(summary['intrinsics']['accepted_for_delivery'])
                self.assertFalse(summary['extrinsics']['accepted_for_delivery'])
                self.assertEqual(summary['tables']['imu']['rows'][0]['gyro_x'],'')

    def test_local_sample_urls_are_supported_without_allowing_file_paths(self):
        dataset=json.loads((ROOT/'data/eyecatcher_stereo_datasets.json').read_text())['datasets'][0]
        record=import_stereo_datasets({'schema_version':1,'datasets':[dataset]})[0]
        self.assertTrue(record['sample_data_url'].startswith('media/stereo/'))
        dataset['sample_data_url']='file:///private/session.json'
        with self.assertRaises(ValueError):import_stereo_datasets({'schema_version':1,'datasets':[dataset]})

if __name__=='__main__':unittest.main()

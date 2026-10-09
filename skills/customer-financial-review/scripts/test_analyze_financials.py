import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from analyze_financials import analyze, validate

ROOT = Path(__file__).resolve().parents[1]


class FinancialTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'assets'/'example-input.json').read_text(encoding='utf-8'))

    def latest(self, data=None):
        return analyze(data or self.data)['periods'][-1]

    def test_known_financial_outcomes(self):
        p=self.latest(); m=p['metrics']
        self.assertAlmostEqual(m['net_margin']['value'],30/1100)
        self.assertAlmostEqual(m['quick_ratio']['value'],270/650)
        self.assertAlmostEqual(m['revenue_growth']['value'],0.1)
        self.assertEqual(m['free_cash_flow']['value'],-20000)
        self.assertEqual(m['net_debt']['value'],80000)
        self.assertTrue(all(c['status']=='pass' for c in p['checks'].values()))
        self.assertIn('locator',m['net_margin']['inputs'][0]['source'])

    def test_missing_is_not_zero(self):
        f=self.data['periods'][1]['facts']['operating_cash_flow']
        f.update(value=None,status='not_provided')
        p=self.latest()
        self.assertEqual(p['metrics']['free_cash_flow']['status'],'unavailable')
        self.assertEqual(p['checks']['cash_bridge']['status'],'unavailable')

    def test_missing_prior_income_not_inferred_from_balance_sheet(self):
        self.data['periods'][0]['facts'].pop('revenue')
        self.assertEqual(self.latest()['metrics']['revenue_growth']['status'],'unavailable')

    def test_zero_is_preserved(self):
        self.data['periods'][1]['facts']['net_income']['value']=0
        p=self.latest()
        self.assertEqual(p['metrics']['net_margin']['value'],0)
        self.assertIsNone(p['metrics']['operating_cash_to_profit']['value'])

    def test_negative_prior_profit_no_growth_percent(self):
        self.data['periods'][0]['facts']['net_income']['value']=-20
        self.assertIsNone(self.latest()['metrics']['net_income_growth']['value'])

    def test_negative_equity_no_negative_leverage_ratio(self):
        self.data['periods'][1]['facts']['equity']['value']=-10
        self.assertIsNone(self.latest()['metrics']['liabilities_to_equity']['value'])
        self.assertEqual(self.latest()['checks']['balance_sheet']['status'],'fail')

    def test_unit_changes_do_not_change_comparison(self):
        p=self.data['periods'][0]; p['unit_multiplier']=1; p['tolerance']*=1000
        for f in p['facts'].values(): f['value']*=1000
        self.assertAlmostEqual(self.latest()['metrics']['revenue_growth']['value'],0.1)

    def test_incomparable_metadata_and_period_lengths(self):
        for key,val in [('currency','USD'),('scope','consolidated'),('basis','different'),('end','2025-06-30')]:
            with self.subTest(key=key):
                d=copy.deepcopy(self.data);d['periods'][1][key]=val
                self.assertIsNone(self.latest(d)['metrics']['revenue_growth']['value'])

    def test_undisclosed_prepaid_not_assumed_zero(self):
        self.data['periods'][1]['facts'].pop('prepayments')
        self.assertIsNone(self.latest()['metrics']['quick_ratio']['value'])

    def test_cash_difference_is_not_plugged(self):
        self.data['periods'][1]['facts']['cash_end']['value']=121
        p=self.latest()
        self.assertEqual(p['checks']['cash_bridge']['residual'],-1000)
        self.assertEqual(p['checks']['cash_bridge']['status'],'fail')
        self.assertEqual(p['checks']['cash_to_balance_sheet']['status'],'fail')

    def test_retained_scope_required(self):
        self.data['periods'][1].pop('retained_profit_basis')
        self.assertEqual(self.latest()['checks']['retained_earnings']['status'],'unavailable')

    def test_invalid_facts_are_rejected(self):
        cases=[('value','1.100,00'),('value',True),('value',float('inf')),('status','guessed'),('source',{})]
        for key,val in cases:
            with self.subTest(key=key,val=val):
                d=copy.deepcopy(self.data); d['periods'][1]['facts']['revenue'][key]=val
                with self.assertRaises(ValueError):validate(d)

    def test_duplicate_period_rejected(self):
        self.data['periods'][1]['id']='2024'
        with self.assertRaises(ValueError):validate(self.data)

    def test_cli_fail_exit_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
            p=Path(temp); src=p/'input.json'; out=p/'result'
            self.data['periods'][1]['facts']['cash_end']['value']=121
            src.write_text(json.dumps(self.data),encoding='utf-8')
            cmd=[sys.executable,str(ROOT/'scripts'/'analyze_financials.py'),str(src),'--out-dir',str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
            before=(out/'financial-metrics.json').read_bytes()
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,1)
            self.assertEqual(before,(out/'financial-metrics.json').read_bytes())


if __name__=='__main__': unittest.main()

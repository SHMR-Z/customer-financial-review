"""Compute evidence-linked metrics from reviewed facts; no extraction or credit approval."""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import sys

KNOWN = {'reported', 'derived', 'not_disclosed', 'not_provided', 'unreadable'}
NONNEGATIVE = {'total_assets', 'current_assets', 'total_liabilities', 'current_liabilities',
               'cash', 'unrestricted_cash', 'inventory', 'prepayments',
               'other_nonquick_assets', 'interest_bearing_debt', 'cost_of_sales',
               'cash_capex', 'dividends', 'cash_begin', 'cash_end'}


def number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label}: expected a finite JSON number')
    if positive and value <= 0:
        raise ValueError(f'{label}: must be positive')
    return value


def validate(data):
    if data.get('schema_version') != 1 or isinstance(data.get('schema_version'), bool):
        raise ValueError('schema_version must be 1')
    if not isinstance(data.get('entity'), str) or not data['entity'].strip():
        raise ValueError('entity is required')
    if not isinstance(data.get('periods'), list) or not data['periods']:
        raise ValueError('periods must be a nonempty list')
    seen, last_end = set(), None
    for p in data['periods']:
        for key in ('id', 'currency', 'scope', 'basis', 'start', 'end'):
            if not isinstance(p.get(key), str) or not p[key].strip():
                raise ValueError(f'period {key} must be a nonempty string')
        if p['id'] in seen:
            raise ValueError('duplicate period id')
        seen.add(p['id'])
        start, end = date.fromisoformat(p['start']), date.fromisoformat(p['end'])
        if end < start or (last_end is not None and start <= last_end):
            raise ValueError('periods must be ordered and must not overlap')
        last_end = end
        multiplier = number(p.get('unit_multiplier'), 'unit_multiplier', positive=True)
        tolerance = number(p.get('tolerance'), 'tolerance')
        if tolerance < 0:
            raise ValueError('tolerance must be nonnegative')
        if not isinstance(p.get('comparable_to_previous', False), bool):
            raise ValueError('comparable_to_previous must be boolean')
        if not isinstance(p.get('facts'), dict):
            raise ValueError('facts must be a dictionary')
        for key, fact in p['facts'].items():
            if not isinstance(fact, dict) or fact.get('status') not in KNOWN:
                raise ValueError(f'{key}: invalid fact status')
            source = fact.get('source')
            if not isinstance(source, dict) or not all(isinstance(source.get(k), str) and source[k].strip() for k in ('file', 'locator')):
                raise ValueError(f'{key}: source file and locator required')
            if fact['status'] in ('reported', 'derived'):
                val = number(fact.get('value'), key)
                number(val * multiplier, f'{key} normalized value')
                if key in NONNEGATIVE and val < 0:
                    raise ValueError(f'{key}: expected nonnegative standardized value')
                if fact['status'] == 'derived' and not str(fact.get('derivation', '')).strip():
                    raise ValueError(f'{key}: derived value requires derivation')
            elif fact.get('value') is not None:
                raise ValueError(f'{key}: unknown fact must have null value')
    return data


def value(p, key):
    fact = p['facts'].get(key, {})
    return fact['value'] * p['unit_multiplier'] if fact.get('status') in ('reported', 'derived') else None


def evidence(p, keys):
    return [{'period': p['id'], 'field': key, **p['facts'].get(key, {'status': 'missing'})} for key in keys]


def metric(p, keys, formula, fn, denominator=None):
    vals = [value(p, key) for key in keys]
    out = {'value': None, 'status': 'unavailable', 'formula': formula, 'inputs': evidence(p, keys)}
    missing = [f"{k} ({p['facts'].get(k, {}).get('status', 'missing')})" for k, v in zip(keys, vals) if v is None]
    if missing:
        out['reason'] = 'Missing evidence: ' + ', '.join(missing)
    elif denominator is not None and vals[denominator] <= 0:
        out['reason'] = f'{keys[denominator]} must be positive for this ratio'
    else:
        out.update(value=number(fn(*vals), formula), status='computed')
    return out


def check(p, keys, formula, fn):
    out = metric(p, keys, formula, fn)
    if out['status'] == 'computed':
        residual = out.pop('value')
        tol = p['tolerance'] * p['unit_multiplier']
        out.update(residual=residual, tolerance=tol,
                   status='pass' if abs(residual) <= tol else 'fail')
    return out


def comparable(p, prev):
    if not prev or not p.get('comparable_to_previous'):
        return False
    days = lambda q: (date.fromisoformat(q['end']) - date.fromisoformat(q['start'])).days + 1
    return all(p[k] == prev[k] for k in ('currency', 'scope', 'basis')) and abs(days(p)-days(prev)) <= 1


def analyze(data):
    validate(data)
    result = {'schema_version': 1, 'entity': data['entity'], 'amount_unit': 'base currency units',
              'limitations': 'Reviewed input only; arithmetic checks do not verify originals or approve credit.', 'periods': []}
    for i, p in enumerate(data['periods']):
        m, checks = {}, {}
        ratios = {
            'gross_margin': ('gross_profit', 'revenue'),
            'net_margin': ('net_income', 'revenue'),
            'operating_margin': ('operating_profit', 'revenue'),
            'current_ratio': ('current_assets', 'current_liabilities'),
            'cash_to_current_liabilities': ('unrestricted_cash', 'current_liabilities'),
            'liabilities_to_assets': ('total_liabilities', 'total_assets'),
            'liabilities_to_equity': ('total_liabilities', 'equity'),
            'operating_cash_to_profit': ('operating_cash_flow', 'net_income')}
        for name, keys in ratios.items():
            m[name] = metric(p, keys, ' / '.join(keys), lambda a, b: a/b, denominator=1)
        m['quick_ratio'] = metric(p, ('current_assets', 'inventory', 'prepayments', 'other_nonquick_assets', 'current_liabilities'),
            '(current_assets - inventory - prepayments - other_nonquick_assets) / current_liabilities',
            lambda a, b, c, d, e: (a-b-c-d)/e, denominator=4)
        for name, keys in {'working_capital': ('current_assets', 'current_liabilities'),
                           'free_cash_flow': ('operating_cash_flow', 'cash_capex'),
                           'net_debt': ('interest_bearing_debt', 'unrestricted_cash')}.items():
            m[name] = metric(p, keys, ' - '.join(keys), lambda a, b: a-b)
        if not p.get('debt_definition'):
            m['net_debt'].update(value=None, status='unavailable', reason='debt_definition required')
        else:
            m['net_debt']['debt_definition'] = p['debt_definition']
        prev = data['periods'][i-1] if i else None
        for key in ('revenue', 'net_income'):
            out = {'value': None, 'status': 'unavailable', 'formula': f'{key}_current / {key}_previous - 1',
                   'inputs': evidence(p, [key]) + (evidence(prev, [key]) if prev else [])}
            if not comparable(p, prev):
                out['reason'] = 'Comparable prior period not confirmed or metadata differs'
            elif value(p, key) is None or value(prev, key) is None:
                out['reason'] = 'Current or prior value unavailable'
            elif value(prev, key) <= 0:
                out['reason'] = 'Prior base is zero or negative; describe change without ordinary growth percent'
            else:
                out.update(value=number(value(p, key)/value(prev, key)-1, key), status='computed')
            m[key+'_growth'] = out
        checks['balance_sheet'] = check(p, ('total_assets', 'total_liabilities', 'equity'),
            'total_assets - total_liabilities - equity', lambda a,b,c:a-b-c)
        checks['gross_profit'] = check(p, ('revenue', 'cost_of_sales', 'gross_profit'),
            'revenue - cost_of_sales - gross_profit', lambda a,b,c:a-b-c)
        checks['cash_bridge'] = check(p, ('cash_begin', 'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'cash_fx_other', 'cash_end'),
            'cash_begin + operating + investing + financing + fx_other - cash_end', lambda a,b,c,d,e,f:a+b+c+d+e-f)
        checks['cash_to_balance_sheet'] = check(p, ('cash_end', 'cash'), 'cash_end - cash', lambda a,b:a-b)
        checks['retained_earnings'] = check(p, ('retained_earnings_begin', 'retained_profit', 'dividends', 'retained_other_adjustments', 'retained_earnings_end'),
            'retained_begin + retained_profit - dividends + other_adjustments - retained_end', lambda a,b,c,d,e:a+b-c+d-e)
        if not p.get('retained_profit_basis'):
            checks['retained_earnings'] = {'status': 'unavailable', 'reason': 'retained_profit_basis required',
                'inputs': checks['retained_earnings']['inputs']}
        result['periods'].append({k:p[k] for k in ('id','start','end','currency','scope','basis')} |
            {'metrics':m, 'checks':checks, 'facts':p['facts'], 'unit_multiplier':p['unit_multiplier']})
    return result


def markdown(result):
    safe = lambda v: str(v).replace('|', '\\|').replace('\n', ' ')
    lines = [f"# {safe(result['entity'])} — 财务计算", '',
             '金额：基本货币单位；比率为倍数，小数比例乘100才为百分比。算术检查不等于原件核验或信用审批。', '']
    for p in result['periods']:
        lines += [f"## {safe(p['id'])} / {safe(p['currency'])}", '', '| 指标 | 数值 | 状态/限制 |', '|---|---:|---|']
        for key, m in p['metrics'].items():
            val = '—' if m['value'] is None else f"{m['value']:,.6f}"
            lines.append(f"| {key} | {val} | {safe(m.get('reason', m['status']))} |")
        lines += ['', '| 勾稽 | 差额 | 状态/限制 |', '|---|---:|---|']
        for key, c in p['checks'].items():
            lines.append(f"| {key} | {c.get('residual', '—')} | {safe(c.get('reason', c['status']))} |")
        lines += ['', '公式及每项输入的来源见同目录 financial-metrics.json。', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        result = analyze(json.loads(args.input.read_text(encoding='utf-8-sig')))
        targets = [args.out_dir/'financial-metrics.json', args.out_dir/'financial-metrics.md']
        if not args.overwrite and any(p.exists() for p in targets):
            raise ValueError('output exists; use another directory or --overwrite')
        args.out_dir.mkdir(parents=True, exist_ok=True)
        targets[0].write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        targets[1].write_text(markdown(result), encoding='utf-8')
        failed = sum(c['status']=='fail' for p in result['periods'] for c in p['checks'].values())
        print(f'Wrote {len(result["periods"])} periods; {failed} reconciliation failures')
        return 2 if failed else 0
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

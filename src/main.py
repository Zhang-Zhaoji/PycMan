"""Run from any working directory: python path/to/src/main.py."""
from gui import GUI
from config import PROJECT_ROOT, load_config
from rules import STAGES
import argparse
import json
from pathlib import Path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a cumulative Pyc Man task stage')
    parser.add_argument('--config', help='Path to a map JSON profile')
    parser.add_argument('--map', help='Optional text map')
    parser.add_argument('--stage', choices=STAGES, help='Run the selected S1-S5 stage')
    parser.add_argument('--advanced', nargs='+', choices=('A1', 'A2', 'B1', 'B2', 'C1', 'C2'),
                        help='Run selected advanced tasks over S5')
    parser.add_argument('--feature-config', help='JSON file with parameters for --advanced')
    parser.add_argument('--scenario', help='Load a named advanced map and configuration')
    args = parser.parse_args()
    config = load_config(args.config) if args.config else None
    if args.scenario:
        if args.stage or args.advanced or args.map or args.feature_config:
            parser.error('--scenario cannot be combined with other task selectors')
        cases = json.loads((PROJECT_ROOT / 'assets/scenarios/advanced/cases.json').read_text(
            encoding='utf-8'))
        if args.scenario not in cases:
            parser.error(f'unknown scenario: {args.scenario}')
        case = cases[args.scenario]
        path = (PROJECT_ROOT / 'assets/maps/advanced' / case['map']
                if 'map' in case else None)
        GUI.for_advanced(tuple(case['features']), path=path, config=config,
                         feature_config=case.get('config', {})).run()
    elif args.advanced:
        if args.stage:
            parser.error('--stage and --advanced cannot be used together')
        if 'C1' in args.advanced and args.map:
            parser.error('C1 generates its own map; omit --map')
        if not args.feature_config and any(
                task in ('A1', 'A2', 'B1', 'C1', 'C2') for task in args.advanced):
            parser.error('these advanced tasks need --feature-config or --scenario')
        options = (json.loads(Path(args.feature_config).read_text(encoding='utf-8'))
                   if args.feature_config else {})
        GUI.for_advanced(tuple(args.advanced), path=args.map, config=config,
                         feature_config=options).run()
    else:
        if args.feature_config:
            parser.error('--feature-config requires --advanced')
        GUI.for_stage(args.stage or 'S1', path=args.map, config=config).run()

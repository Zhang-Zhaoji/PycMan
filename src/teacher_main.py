"""Run the teacher reference game; omit this file from student releases."""

import argparse

from config import TERMINAL_CONFIG, load_config
from game import Game
from gui import GUI
from teacher_reference import reference_rules


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the teacher reference game')
    parser.add_argument('--config', help='Path to a map JSON profile')
    parser.add_argument('--map', help='Optional text map')
    parser.add_argument('--terminal', action='store_true', help='Use the terminal demo')
    args = parser.parse_args()
    rules = reference_rules()
    if args.terminal:
        config = load_config(args.config or TERMINAL_CONFIG)
        Game(path=args.map, config=config, rules=rules).run()
    else:
        config = load_config(args.config) if args.config else None
        GUI(path=args.map, config=config, rules=rules).run()


if __name__ == '__main__':
    main()

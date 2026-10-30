"""Create a student zip without teacher reference code or private materials."""

import argparse
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from build_docs import build_docs

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist/PycMan-student.zip'


def package_files() -> dict[str, Path]:
    files = {
        'README.md': ROOT / 'student-assignment.md',
        'AGENTS.md': ROOT / 'StudentAgents.md',
        'Background.md': ROOT / 'Background.md',
        'student-assignment.md': ROOT / 'student-assignment.md',
        'requirements.txt': ROOT / 'requirements.txt',
    }
    source_names = (
        'codebook.py', 'config.py', 'controller.py', 'game.py',
        'gui.py', 'main.py', 'rules.py', 'utils.py',
    )
    for name in source_names:
        path = ROOT / 'src' / name
        files[str(path.relative_to(ROOT))] = path
    task_names = ('src/tasks/__init__.py', 'src/tasks/basic/__init__.py',
                  'src/tasks/advanced/__init__.py') + tuple(
        f'src/tasks/basic/s{number}.py' for number in range(1, 6)) + tuple(
        f'src/tasks/advanced/{category}{number}.py'
        for category in 'abc' for number in (1, 2))
    for name in task_names:
        path = ROOT / name
        files[str(path.relative_to(ROOT))] = path
    for pattern in ('configs/*.json', 'assets/maps/**/*.txt',
                    'assets/scenarios/**/*.json',
                    'assets/sprites/*.png', 'imgs/*.png', 'imgs/*.webp'):
        for path in ROOT.glob(pattern):
            files[str(path.relative_to(ROOT))] = path
    for name in ('__init__.py', '__main__.py', 'test_basic.py',
                 'test_framework.py', 'test_advanced.py', 'scenarios.py'):
        files[f'tests/{name}'] = ROOT / 'tests' / name
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-pdf', action='store_true',
                        help='Package Markdown only, without PDF build dependencies')
    args = parser.parse_args()
    files = package_files()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pycman-package-', dir=OUTPUT.parent) as temporary:
        staging = Path(temporary)
        if not args.skip_pdf:
            try:
                files.update(build_docs(staging / 'pdf'))
            except RuntimeError as error:
                parser.exit(1, f'{error}\n')
        temporary_zip = staging / OUTPUT.name
        with ZipFile(temporary_zip, 'w', compression=ZIP_DEFLATED) as archive:
            for name, path in sorted(files.items()):
                archive.write(path, name)
        temporary_zip.replace(OUTPUT)
    print(f'Created {OUTPUT.relative_to(ROOT)} ({len(files)} files)')


if __name__ == '__main__':
    main()

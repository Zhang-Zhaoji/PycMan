"""Create a student zip without teacher reference code or private materials."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist/PycMan-student.zip'


def package_files() -> dict[str, Path]:
    files = {
        'README.md': ROOT / 'student-assignment.md',
        'AGENTS.md': ROOT / 'AGENTS.md',
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
                    'assets/sprites/*.png'):
        for path in ROOT.glob(pattern):
            files[str(path.relative_to(ROOT))] = path
    for name in ('__init__.py', '__main__.py', 'test_basic.py',
                 'test_framework.py', 'test_advanced.py', 'scenarios.py'):
        files[f'tests/{name}'] = ROOT / 'tests' / name
    return files


def main() -> None:
    files = package_files()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, 'w', compression=ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, name)
    print(f'Created {OUTPUT.relative_to(ROOT)} ({len(files)} files)')


if __name__ == '__main__':
    main()

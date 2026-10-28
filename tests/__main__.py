"""Gate and score cumulative basic stages or selected advanced tasks."""

import argparse
import sys
import unittest

from . import test_framework

# Points per stage.
STAGE_POINTS = {'S1': 14, 'S2': 12, 'S3': 14, 'S4': 8, 'S5': 12}
ADVANCED_POINTS = {name: 15 for name in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')}
COMBINATION_TESTS = {
    frozenset(('A2', 'C2')): 'test_combo_a2_c2',
    frozenset(('B1', 'B2')): 'test_combo_b1_b2',
    frozenset(('C1', 'C2')): 'test_combo_c1_c2',
}


def run_suite(suite: unittest.TestSuite) -> unittest.TestResult:
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)


def stage_suite(stage: str) -> unittest.TestSuite:
    from . import test_basic

    loader = unittest.TestLoader()
    names = [name for name in loader.getTestCaseNames(test_basic.PublicTaskTest)
             if name.startswith(f'test_{stage.lower()}_')]
    if not names:
        raise RuntimeError(f'No public tests found for {stage}')
    return unittest.TestSuite(test_basic.PublicTaskTest(name) for name in names)


def integration_suite(stage: str) -> unittest.TestSuite:
    from . import test_basic

    return unittest.TestSuite([
        test_basic.BasicIntegrationTest(f'test_integration_{stage.lower()}')
    ])


def advanced_suite(task: str) -> unittest.TestSuite:
    from . import test_advanced

    loader = unittest.TestLoader()
    names = [name for name in loader.getTestCaseNames(test_advanced.AdvancedTaskTest)
             if name.startswith(f'test_{task.lower()}_')]
    if not names:
        raise RuntimeError(f'No advanced tests found for {task}')
    return unittest.TestSuite(test_advanced.AdvancedTaskTest(name) for name in names)


def advanced_integration_suite(task: str) -> unittest.TestSuite:
    from . import test_advanced

    return unittest.TestSuite([
        test_advanced.AdvancedIntegrationTest(f'test_integration_{task.lower()}')
    ])


def combination_suite(name: str) -> unittest.TestSuite:
    from . import test_advanced

    return unittest.TestSuite([test_advanced.AdvancedCombinationTest(name)])


def complete(result: unittest.TestResult, expected: int) -> bool:
    return result.testsRun == expected and result.wasSuccessful() and not result.skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Check and score PycMan tasks')
    parser.add_argument('targets', nargs='*', default=['all'],
                        help='framework, all, S1-S5, or selected A1-C2 tasks')
    args = parser.parse_args(argv)
    targets = [target.upper() for target in args.targets] or ['ALL']
    if not (len(targets) == 1 and targets[0] in ('FRAMEWORK', 'ALL', *STAGE_POINTS)
            or len(set(targets)) == len(targets)
            and all(target in ADVANCED_POINTS for target in targets)):
        parser.error('use framework, all, S1-S5, or distinct A1-C2 task names')

    print('Framework integrity tests')
    framework_suite = unittest.defaultTestLoader.loadTestsFromModule(test_framework)
    framework_count = framework_suite.countTestCases()
    if framework_count == 0:
        print('No framework tests found. Student tests were not run.')
        return 2
    framework_result = run_suite(framework_suite)
    if not complete(framework_result, framework_count):
        print('Framework tests failed. Student tests were not run; no score was assigned.')
        return 2
    if targets == ['FRAMEWORK']:
        return 0

    if all(target in ADVANCED_POINTS for target in targets):
        from . import test_basic

        print('\nBasic game prerequisite tests')
        prerequisite = unittest.defaultTestLoader.loadTestsFromModule(test_basic)
        prerequisite_result = run_suite(prerequisite)
        if not complete(prerequisite_result, prerequisite.countTestCases()):
            print('Basic game checks failed. Advanced tests were not run.')
            return 2
        passed = {}
        for task in targets:
            suite = advanced_suite(task)
            print(f'\n{task} scenario tests')
            result = run_suite(suite)
            behavior_passed = complete(result, suite.countTestCases())
            integration_passed = False
            if behavior_passed:
                print(f'\n{task} game integration check')
                integrated = advanced_integration_suite(task)
                outcome = run_suite(integrated)
                integration_passed = complete(outcome, integrated.countTestCases())
            passed[task] = behavior_passed and integration_passed
        for pair, test_name in COMBINATION_TESTS.items():
            if pair.issubset(targets) and all(passed[task] for task in pair):
                label = '+'.join(sorted(pair))
                print(f'\n{label} combination check')
                suite = combination_suite(test_name)
                outcome = run_suite(suite)
                if not complete(outcome, suite.countTestCases()):
                    for task in pair:
                        passed[task] = False
        earned = sum(ADVANCED_POINTS[task] for task in targets if passed[task])
        for task in targets:
            points = ADVANCED_POINTS[task] if passed[task] else 0
            print(f'{task}: {points}/{ADVANCED_POINTS[task]} points')
        maximum = min(30, 15 * len(targets))
        print(f'\nAdvanced task score: {min(earned, 30)}/{maximum}')
        return 0 if all(passed.values()) else 1

    stages = list(STAGE_POINTS)
    if targets != ['ALL']:
        stages = stages[:stages.index(targets[0]) + 1]

    earned = 0
    maximum = sum(STAGE_POINTS[stage] for stage in stages)
    all_passed = True
    for stage in stages:
        suite = stage_suite(stage)
        expected = suite.countTestCases()
        print(f'\n{stage} student tests')
        result = run_suite(suite)
        public_passed = complete(result, expected)
        integration_passed = False
        integration_status = 'skipped'
        if public_passed:
            print(f'\n{stage} cumulative game check')
            cumulative = integration_suite(stage)
            cumulative_result = run_suite(cumulative)
            integration_passed = complete(cumulative_result, cumulative.countTestCases())
            integration_status = 'passed' if integration_passed else 'failed'
        passed = public_passed and integration_passed
        points = STAGE_POINTS[stage] if passed else 0
        earned += points
        all_passed &= passed
        print(f'{stage}: {points}/{STAGE_POINTS[stage]} points '
              f'({expected - len(result.failures) - len(result.errors) - len(result.skipped)}/{expected} '
              f'public tests passed; cumulative check {integration_status})')

    print(f'\nBasic task score: {earned}/{maximum}')
    return 0 if all_passed else 1


if __name__ == '__main__':
    raise SystemExit(main())

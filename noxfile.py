import nox


@nox.session
def tests(session: nox.Session) -> None:
    session.install('-e', '.','pytest')
    session.run('pytest', '-q')


@nox.session
def coverage(session: nox.Session) -> None:
    session.install('-e', '.', 'pytest', 'pytest-cov')
    session.run('pytest', '--cov=the_alchemiser', '--cov-report=term-missing', '--cov-report=xml:reports/coverage.xml')


@nox.session
def mutation(session: nox.Session) -> None:
    session.install('-e', '.', 'pytest', 'mutmut')
    session.run('mutmut', 'run', '--paths-to-mutate', 'the_alchemiser', '--runner', 'pytest -q')


@nox.session
def lint_tests(session: nox.Session) -> None:
    session.install('ruff')
    session.run('ruff', 'check', 'tests')

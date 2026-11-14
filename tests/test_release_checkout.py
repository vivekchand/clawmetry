"""The release needs the exact merge tree, not archived screenshot branches."""
import os
from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).parents[1]


def test_release_checkout_is_bounded_and_keeps_the_exact_merge_ref():
    workflow = yaml.safe_load((ROOT / '.github/workflows/release-on-merge.yml').read_text())
    steps = workflow['jobs']['release']['steps']
    checkout = next(s for s in steps if s.get('uses', '').startswith('actions/checkout@'))
    assert checkout['with']['fetch-depth'] == 1
    assert checkout['with']['ref'] == '${{ github.event.pull_request.merge_commit_sha }}'
    assert checkout['with']['persist-credentials'] is True
    assert any(s.get('run') == 'df -h "$RUNNER_TEMP"' for s in steps[:steps.index(checkout)])


def test_shallow_merge_checkout_can_push_release_tag_and_version_branch(tmp_path):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='Release test', GIT_AUTHOR_EMAIL='release@example.invalid',
               GIT_COMMITTER_NAME='Release test', GIT_COMMITTER_EMAIL='release@example.invalid')

    def git(path, *args, check=True):
        return subprocess.run(['git', '-C', str(path), *args], env=env,
                              capture_output=True, text=True, check=check, timeout=20)

    source = tmp_path / 'source'
    source.mkdir()
    git(source, 'init', '-b', 'main')
    (source / 'dashboard.py').write_text('__version__ = "0.0.1"\n')
    (source / 'old-screenshot.bin').write_bytes(b'archived capture' * 1000)
    git(source, 'add', '.')
    git(source, 'commit', '-m', 'original tree')
    old_blob = git(source, 'rev-parse', 'HEAD:old-screenshot.bin').stdout.strip()
    git(source, 'switch', '-c', 'feature')
    (source / 'old-screenshot.bin').unlink()
    (source / 'feature.txt').write_text('Reviewed feature bytes\n')
    git(source, 'add', '.')
    git(source, 'commit', '-m', 'feature')
    git(source, 'switch', 'main')
    (source / 'main.txt').write_text('Main branch bytes\n')
    git(source, 'add', '.')
    git(source, 'commit', '-m', 'main change')
    git(source, 'merge', '--no-ff', 'feature', '-m', 'merge reviewed feature')
    merge_sha = git(source, 'rev-parse', 'HEAD').stdout.strip()
    origin = tmp_path / 'origin.git'
    subprocess.run(['git', 'clone', '--bare', str(source), str(origin)], env=env,
                   capture_output=True, check=True, timeout=20)

    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    git(checkout, 'init')
    git(checkout, 'remote', 'add', 'origin', origin.as_uri())
    git(checkout, 'fetch', '--depth=1', '--no-tags', 'origin', merge_sha)
    git(checkout, 'checkout', '--detach', 'FETCH_HEAD')
    assert git(checkout, 'rev-parse', 'HEAD').stdout.strip() == merge_sha
    assert git(checkout, 'rev-list', '--count', 'HEAD').stdout.strip() == '1'
    assert (checkout / 'feature.txt').read_text() == 'Reviewed feature bytes\n'
    assert git(checkout, 'cat-file', '-e', old_blob, check=False).returncode != 0

    # Same operations as the release: tag the pinned merge, then publish the
    # version write-back on its own branch. Only the disposable origin is used.
    git(checkout, 'tag', 'release-test')
    git(checkout, 'push', 'origin', 'refs/tags/release-test')
    assert git(origin, 'rev-parse', 'refs/tags/release-test').stdout.strip() == merge_sha
    git(checkout, 'switch', '-c', 'auto-bump/test-release')
    (checkout / 'dashboard.py').write_text('__version__ = "0.0.2"\n')
    git(checkout, 'add', 'dashboard.py')
    git(checkout, 'commit', '-m', 'version write-back')
    git(checkout, 'push', 'origin', 'auto-bump/test-release')
    assert git(origin, 'show', 'refs/heads/auto-bump/test-release:dashboard.py').stdout == \
        '__version__ = "0.0.2"\n'

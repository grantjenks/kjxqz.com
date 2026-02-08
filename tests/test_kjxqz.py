import inspect
import json

import pytest

import kjxqz
from kjxqz import __main__ as cli


def test_build():
    assert kjxqz.__build__ > 0


def is_word_in_dawg(dawg, word):
    state = '0'
    for letter in word:
        branches = dawg.get(state, {})
        if letter not in branches:
            return False
        state = branches[letter]
    return '$' in dawg.get(state, {})


def test_build_dawg():
    words = ['ate', 'eat', 'tea', 'eta', 'at']
    dawg = kjxqz.build_dawg(words)

    for word in words:
        assert is_word_in_dawg(dawg, word)

    assert not is_word_in_dawg(dawg, 'tae')
    assert not is_word_in_dawg(dawg, 'teas')


def test_make_dawg(tmp_path):
    words_path = tmp_path / 'words.txt'
    words_path.write_text('ate\ntea\nat\n', encoding='utf-8')

    output_path = tmp_path / 'dawg.js'
    data = kjxqz.make_dawg(filename=output_path, words_filename=words_path)

    text = output_path.read_text(encoding='utf-8')
    assert text.startswith('var dawg = ')
    assert text.endswith(';\n')

    payload = text[len('var dawg = ') : -2]
    parsed = json.loads(payload)
    assert parsed == data
    assert is_word_in_dawg(parsed, 'ate')
    assert is_word_in_dawg(parsed, 'tea')


def test_make_service_worker(tmp_path):
    template = tmp_path / 'service-worker-template.js'
    template.write_text("const CACHE_NAME = 'kjxqz-{HASH}';\n", encoding='utf-8')

    inputs = []
    for filename, content in [
        ('index.html', '<h1>kjxqz</h1>'),
        ('words.txt', 'ate\ntea\n'),
    ]:
        path = tmp_path / filename
        path.write_text(content, encoding='utf-8')
        inputs.append(path)

    output_path = tmp_path / 'service-worker.js'
    code = kjxqz.make_service_worker(
        filename=output_path,
        template_filename=template,
        hash_filenames=[*inputs, template],
    )

    assert len(code) == 16
    text = output_path.read_text(encoding='utf-8')
    assert '{HASH}' not in text
    assert code in text


def test_build_assets(tmp_path):
    words_path = tmp_path / 'words.txt'
    words_path.write_text('ate\ntea\nat\n', encoding='utf-8')

    template = tmp_path / 'service-worker-template.js'
    template.write_text("const CACHE_NAME = 'kjxqz-{HASH}';\n", encoding='utf-8')

    website_dawg_path = tmp_path / 'www' / 'dawg.js'
    package_dawg_path = tmp_path / 'package' / 'dawg.js'
    service_worker_path = tmp_path / 'service-worker.js'
    data, code = kjxqz.build(
        dawg=website_dawg_path,
        package_dawg=package_dawg_path,
        service_worker=service_worker_path,
        words_filename=words_path,
        template_filename=template,
        hash_filenames=[words_path, template],
    )

    assert len(code) == 16
    assert website_dawg_path.exists()
    assert package_dawg_path.exists()
    assert service_worker_path.exists()
    assert is_word_in_dawg(data, 'ate')
    assert is_word_in_dawg(data, 'tea')


def test_search_and_isearch(monkeypatch):
    words = ['at', 'ate', 'eat', 'eta', 'tea', 'late', 'plate']
    monkeypatch.setattr(kjxqz, '_DAWG', kjxqz.build_dawg(words))

    assert kjxqz.search('aetl?', 'at') == ['plate', 'late', 'ate', 'eat', 'at']

    results = list(kjxqz.isearch('aetl?', 'at'))
    assert set(results) == {'plate', 'late', 'ate', 'eat', 'at'}
    assert len(results) == len(set(results))


def test_search_requires_load(monkeypatch):
    monkeypatch.setattr(kjxqz, '_DAWG', None)
    with pytest.raises(RuntimeError):
        kjxqz.search('abc')


def test_load(tmp_path, monkeypatch):
    data = {'0': {'a': '1'}, '1': {'$': '0'}}
    path = tmp_path / 'dawg.js'
    path.write_text(f'var dawg = {json.dumps(data)};\n', encoding='utf-8')

    monkeypatch.setattr(kjxqz, '_DAWG', None)
    loaded = kjxqz.load(path)
    assert loaded == data
    assert kjxqz._DAWG == data


def test_isearch_signature_has_no_sorted_arg():
    signature = inspect.signature(kjxqz.isearch)
    assert 'sorted' not in signature.parameters


def test_cli_main_build(monkeypatch):
    calls = []

    def fake_build(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(cli, 'build', fake_build)
    code = cli.main([])

    assert code == 0
    assert calls == [{'dawg': 'www/dawg.js', 'service_worker': 'www/service-worker.js'}]


def test_cli_main_search_shorthand(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(cli, 'load', lambda filename: calls.append(filename))
    monkeypatch.setattr(cli, 'search', lambda **kwargs: ['alpha', 'beta'])

    code = cli.main(['abcdef?', 'hi'])
    assert code == 0
    assert len(calls) == 1
    assert capsys.readouterr().out == 'alpha\nbeta\n'

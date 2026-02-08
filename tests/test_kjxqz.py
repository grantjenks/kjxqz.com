import json

import kjxqz


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

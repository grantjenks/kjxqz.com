var update_timer = 0;
var update_generation = 0;
var update_delay = 75;
var draw_chunk_size = 1000;

function update() {
    var query_value = document.getElementById('query').value;
    var has_query = query_value.trim().length > 0;
    var generation = update_generation + 1;

    update_generation = generation;

    if (update_timer) {
        clearTimeout(update_timer);
    }

    var output = document.getElementById('output');

    if (!has_query) {
        output.innerHTML = '';
        return;
    }

    update_timer = setTimeout(function () {
        run_update(query_value, generation);
    }, update_delay);
}

function run_update(query_value, generation) {
    var input_query = document.getElementById('query');

    if (generation != update_generation || input_query.value != query_value) {
        return;
    }

    gtag('event', 'view_search_results', {'search_term': query_value});
    var options = parse();
    var results = matches(options);
    draw(options, results, generation);
}

function parse() {
    var options = new Map([
        ['letters', ''],
        ['contains', ''],
        ['contains_display', ''],
        ['contains_starts', false],
        ['contains_ends', false],
    ]);
    var input_query = document.getElementById('query');
    var query = input_query.value;
    var lower_query = query.toLowerCase();
    var parts = lower_query.split(/\s+/);
    var letters = parts.shift() || '';
    letters = /^[a-z?]{1,15}$/.test(letters) ? letters : '';
    options.set('letters', letters);
    var contains = parts.shift() || '';

    if (/^\.?[a-z_]{1,15}\.?$/.test(contains)) {
        var starts = contains[0] == '.';
        var ends = contains.length > 1 && contains[contains.length - 1] == '.';
        var pattern = contains;

        if (starts) {
            pattern = pattern.slice(1);
        }

        if (ends) {
            pattern = pattern.slice(0, -1);
        }

        options.set('contains', pattern);
        options.set('contains_display', contains);
        options.set('contains_starts', starts);
        options.set('contains_ends', ends);
    }

    return options;
}

function draw(options, results, generation) {
    var parts = [
        '<p>',
        '<span class="word">',
        'Letters: ' + options.get('letters'),
        '</span>',
    ];

    if (options.get('contains_display').length > 0) {
        parts.push('<br>');
        parts.push('<span class="word">');
        parts.push('Contains: ' + options.get('contains_display'));
        parts.push('</span>');
    }
    parts.push('</p>');

    var output = document.getElementById('output');
    output.innerHTML = parts.join('\n');

    var index = 0;
    var last = -1;

    function draw_chunk() {
        if (generation != update_generation) {
            return;
        }

        var parts = [];
        var stop = Math.min(results.length, index + draw_chunk_size);

        for (; index < stop; index += 1) {
            var word = results[index];

            if (word.length != last || parts.length == 0) {
                if (parts.length > 0) {
                    parts.push('</p>');
                }
                parts.push('<p>');
                last = word.length;
            }

            var link = 'https://www.google.com/search?q=';
            link += encodeURIComponent('define:' + word);
            parts.push('<a class="word" href="' + link + '" target="_blank">'
                       + word + '</a>');
        }

        if (parts.length > 0) {
            parts.push('</p>');
            output.insertAdjacentHTML('beforeend', parts.join('\n'));
        }

        if (index < results.length) {
            requestAnimationFrame(draw_chunk);
        }
    }

    draw_chunk();
}

function matches(options) {
    var value = [];
    var letters = Array.from(options.get('letters'));
    var contains = Array.from(options.get('contains'));
    var contains_starts = options.get('contains_starts');
    var contains_ends = options.get('contains_ends');
    var counts = new Map();
    var blanks = 0;
    var results = [];
    var seen = new Set();

    for (var index = 0; index < letters.length; index += 1) {
        var letter = letters[index];

        if (letter == '?') {
            blanks += 1;
        }
        else {
            counts.set(letter, (counts.get(letter) || 0) + 1);
        }
    }

    function consume(letter, callback) {
        var count = counts.get(letter) || 0;

        if (count > 0) {
            counts.set(letter, count - 1);
            callback();
            counts.set(letter, count);
        }
        else if (blanks > 0) {
            blanks -= 1;
            callback();
            blanks += 1;
        }
    }

    function helper(state, contained) {
        var branches = dawg[state];

        if (contained) {
            if ('$' in branches) {
                var result = value.join('');
                if (!seen.has(result)) {
                    seen.add(result);
                    results.push(result);
                }
            }
            if (!contains_ends) {
                traverse(state, true);
            }
        }
        else {
            if (!contains_starts) {
                traverse(state, false);
            }
            match_contains(state, 0);
        }
    }

    function traverse(state, contained) {
        var branches = dawg[state];
        var choices = Object.keys(branches);

        for (var index = 0; index < choices.length; index += 1) {
            var choice = choices[index];

            if (choice == '$') {
                continue;
            }

            consume(choice, function () {
                value.push(choice);
                helper(branches[choice], contained);
                value.pop();
            });
        }
    }

    function match_contains(state, offset) {
        if (offset == contains.length) {
            helper(state, true);
            return;
        }

        var branches = dawg[state];
        var letter = contains[offset];

        if (letter == '_') {
            var choices = Object.keys(branches);

            for (var index = 0; index < choices.length; index += 1) {
                var choice = choices[index];

                if (choice == '$') {
                    continue;
                }

                consume(choice, function () {
                    value.push(choice);
                    match_contains(branches[choice], offset + 1);
                    value.pop();
                });
            }
        }
        else if (letter in branches) {
            value.push(letter);
            match_contains(branches[letter], offset + 1);
            value.pop();
        }
    }

    helper('0', contains.length == 0);

    results.sort(function(alpha, beta) {
        return (beta.length - alpha.length
                || alpha.localeCompare(beta));
    });

    return results;
}

document.getElementById('query').focus();

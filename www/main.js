function update() {
    var query_value = document.getElementById('query').value;
    gtag('event', 'view_search_results', {'search_term': query_value});
    var options = parse();
    var results = matches(options);
    draw(options, results);
}

function parse() {
    var options = new Map([['letters', ''], ['contains', '']]);
    var input_query = document.getElementById('query');
    var query = input_query.value;
    var lower_query = query.toLowerCase();
    var parts = lower_query.split(/\s+/);
    var letters = parts.shift() || '';
    letters = /^[a-z?]{1,12}$/.test(letters) ? letters : '';
    letters = (letters.match(/\?/g) || []).length <= 2 ? letters : '';
    options.set('letters', letters);
    var contains = parts.shift() || '';
    contains = /^[a-z]{1,12}$/.test(contains) ? contains : '';
    options.set('contains', contains);
    return options;
}

function draw(options, results) {
    var parts = [
        '<p>',
        '<span class="word">',
        'Letters: ' + options.get('letters'),
        '</span>',
    ];

    if (options.get('contains').length > 0) {
        parts.push('<br>');
        parts.push('<span class="word">');
        parts.push('Contains: ' + options.get('contains'));
        parts.push('</span>');
    }
    parts.push('</p>');

    var last = -1;

    for (var index = 0; index < results.length; index += 1) {
        var word = results[index];

        if (word.length != last) {
            if (index > 0) {
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
    parts.push('</p>');

    var output = document.getElementById('output');
    output.innerHTML = parts.join('\n');
}

function matches(options) {
    var value = [];
    var letters = Array.from(options.get('letters'));
    var contains = Array.from(options.get('contains'));
    var alphabet = Array.from('abcdefghijklmnopqrstuvwxyz');
    var results = [];

    function helper(state, contained) {
        var branches = dawg[state];

        if (contained) {
            if ('$' in branches) {
                var result = value.join('');
                results.push(result);
            }
            traverse(state, true);
        }
        else {
            traverse(state, false);

            var contains_length = contains.length;

            for (var index = 0; index < contains_length; index += 1) {
                var letter = contains[index];

                if (letter in branches) {
                    value.push(letter);
                    state = branches[letter];
                    branches = dawg[state]
                }
                else {
                    for (var count = 0; count < index; count += 1) {
                        value.pop();
                    }
                    return;
                }
            }
            helper(state, true);
            for (var count = 0; count < contains_length; count += 1) {
                value.pop();
            }
        }
    }

    function traverse(state, contained) {
        var branches = dawg[state];
        var letters_length = letters.length;

        for (var count = 0; count < letters_length; count += 1) {
            var letter = letters.shift();
            var choices = letter == '?' ? alphabet : [letter];
            var choices_length = choices.length;

            for (var index = 0; index < choices_length; index += 1) {
                var choice = choices[index];

                if (choice in branches) {
                    value.push(choice);
                    state = branches[choice];
                    helper(state, contained);
                    value.pop();
                }
            }
            letters.push(letter);
        }
    }

    helper('0', contains.length == 0);

    results.sort(function(alpha, beta) {
        return (beta.length - alpha.length
                || alpha.localeCompare(beta));
    });

    return results.filter(function (element, index, results) {
        return index == 0 || results[index - 1] != element;
    });
}

document.getElementById('query').focus();

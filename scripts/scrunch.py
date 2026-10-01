#!/usr/bin/env python3
"""Assemble a single-file C submission by pasting listed quoted includes.

Command line::

    venv/bin/python scripts/scrunch.py --input PATH --output PATH \\
        [--include-dir DIR]... [--limit INT]

The main source lists every local quoted header it needs at the top, in the
order they must appear, and this script resolves only those:

    #include "nn.h"
    #include "model.h"
    #include "model_decode.h"

Each listed header is looked up relative to the main file's own directory
first, then in each ``--include-dir`` in the order given, and its text is
pasted at the point of the directive. Inside a pasted header, every quoted
``#include "..."`` directive is **removed** and never opened: the main file is
the only include list, so there is no recursion, no dependency walker and no
resolver. ``#include <...>`` standard headers are left exactly as they are,
because those are resolved by the compiler. Header guards are preserved, file
order is preserved, nothing is sorted and nothing is deduplicated implicitly.
A listed header that cannot be found is an error rather than a silent omission.

Comments are then stripped with a small lexical scan that tracks string and
character literals and their escapes, so comment-looking text inside a literal —
a URL, say — survives. Each comment is replaced by a single space and the
newlines it contained are kept, so tokens on either side cannot merge and
preprocessor directives stay on their own lines. Nothing else is minified: no
whitespace collapsing, no reformatting, no renaming. Original files are never
modified.

Finally the file begins with ``#pragma GCC optimize("O3,inline")``, so the
assembled source is optimized whatever flags the referee uses. Its characters
count toward the reported size. O3 and inlining only: no CPU architecture, no
``-march=native``, no AVX and no fast-math.

This is not a formatter or a build system. It exists to produce one
submittable file and to say plainly how big that file is.
"""

import argparse
import re
import sys
from pathlib import Path

DEFAULT_LIMIT = 100000

#: Prepended to every assembled file, before all includes and functions, so the
#: submitted source is optimized regardless of the flags the referee happens to
#: use. O3 with inlining only: no CPU architecture, no -march/native, no AVX and
#: no fast-math, so the generated file stays portable and numerically identical
#: to a plain build.
OPTIMIZATION_PRAGMA = '#pragma GCC optimize("O3,inline")\n'

#: A quoted, local include: the only directive kind this script acts on.
QUOTED_INCLUDE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*"([^"]+)"[ \t]*$')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='python scripts/scrunch.py',
        description='Paste the main source\'s listed quoted includes in place '
                    'and strip comments, producing one C file.',
    )
    parser.add_argument('--input', required=True, type=Path, metavar='PATH',
                        help='main C source, listing its local headers')
    parser.add_argument('--output', required=True, type=Path, metavar='PATH',
                        help='single-file C source to write')
    parser.add_argument('--include-dir', action='append', default=[],
                        type=Path, metavar='DIR',
                        help='extra directory to search for a listed header; '
                             'repeatable, searched in the order given')
    parser.add_argument('--limit', type=int, default=DEFAULT_LIMIT, metavar='INT',
                        help='character limit to report against (default: %d)'
                             % DEFAULT_LIMIT)
    return parser.parse_args(argv)


def resolve_header(name, main_dir, include_dirs):
    """Return the header's path, or None if it is nowhere to be found."""
    direct = main_dir / name
    if direct.is_file():
        return direct
    for directory in include_dirs:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def strip_quoted_includes(text):
    """Drop every quoted local #include line, leaving the rest untouched."""
    kept = []
    for line in text.splitlines(keepends=True):
        if QUOTED_INCLUDE.match(line.rstrip('\r\n')):
            continue
        kept.append(line)
    return ''.join(kept)


def expand(source, source_path, include_dirs):
    """Return *source* with each listed quoted include replaced by its header."""
    out = []
    for line in source.splitlines(keepends=True):
        match = QUOTED_INCLUDE.match(line.rstrip('\r\n'))
        if match is None:
            out.append(line)
            continue
        name = match.group(1)
        found = resolve_header(name, source_path.parent, include_dirs)
        if found is None:
            searched = [str(source_path.parent)] + [str(d) for d in include_dirs]
            raise ValueError('listed header %r not found; searched %s'
                             % (name, ', '.join(searched)))
        # Only the main file's list is followed: a pasted header has its own
        # quoted includes removed, never opened.
        out.append('/* --- begin %s --- */\n' % name)
        out.append(strip_quoted_includes(found.read_text(encoding='utf-8')))
        if not out[-1].endswith('\n'):
            out.append('\n')
        out.append('/* --- end %s --- */\n' % name)
    return ''.join(out)


def strip_comments(text):
    """Remove C comments with a lexical scan that respects literals.

    States: normal, in a line comment, in a block comment, in a string literal,
    in a character literal. A backslash inside a literal continues it, so a
    literal such as "\\"" or a URL containing "//" cannot end a literal early
    and have the rest of the line treated as a comment.

    A removed comment becomes one space, and every newline inside it is kept so
    that following code stays on its own line and directives keep working —
    except for a line that held comment text and no code at all. Such a line is
    dropped whole, newline included, which covers comment-only lines and the
    interior and closing lines of a multi-line block comment. A line that was
    already blank in the source is left exactly as it was, and spacing and
    newlines on code-bearing lines are untouched: this is not whitespace
    compaction.
    """
    out = []
    line = []
    index = 0
    length = len(text)
    state = 'normal'
    line_has_code = False
    line_has_comment = False

    def end_line():
        """Emit or drop the line just finished."""
        if line_has_comment and not line_has_code:
            return
        out.append(''.join(line))
        out.append('\n')

    while index < length:
        character = text[index]
        following = text[index + 1] if index + 1 < length else ''

        if state == 'normal':
            if character == '/' and following == '/':
                state = 'line_comment'
                line_has_comment = True
                line.append(' ')
                index += 2
                continue
            if character == '/' and following == '*':
                state = 'block_comment'
                line_has_comment = True
                line.append(' ')
                index += 2
                continue
            if character == '"':
                state = 'string'
            elif character == "'":
                state = 'character'
            index += 1
            if character == '\n':
                # end_line() writes the line's own newline; do not also buffer it.
                end_line()
                line = []
                line_has_code = False
                line_has_comment = False
                continue
            if not character.isspace():
                line_has_code = True
            line.append(character)
            continue

        if state == 'line_comment':
            # Marked here as well as at the opening '/', so a // comment
            # continued onto a following line keeps that line marked too.
            line_has_comment = True
            if character == '\n':
                state = 'normal'
                end_line()
                line = []
                line_has_code = False
                line_has_comment = False
                index += 1
                continue
            if character == '\\' and following == '\n':
                # A backslash continues a // comment onto the next line.
                index += 2
                continue
            index += 1
            continue

        if state == 'block_comment':
            # Marked before the closing delimiter and newline are considered:
            # every line a block comment consumes, including an empty one and
            # the closing line, is comment text and must not survive as a blank
            # line. line_has_code is deliberately not set, so any code after the
            # closing '*/' on the same line still keeps that line.
            line_has_comment = True
            if character == '*' and following == '/':
                state = 'normal'
                index += 2
                continue
            if character == '\n':
                # The newline belongs to the line being commented, so the same
                # code-or-comment-only rule applies to it.
                end_line()
                line = []
                line_has_code = False
                line_has_comment = False
                index += 1
                continue
            index += 1
            continue

        # Inside a string or character literal: nothing is a comment here.
        if character == '\\':
            line_has_code = True
            line.append(character)
            if following:
                line.append(following)
            index += 2
            continue
        if (state == 'string' and character == '"') or \
                (state == 'character' and character == "'"):
            state = 'normal'
        line_has_code = True
        line.append(character)
        index += 1

    if state in ('string', 'character'):
        raise ValueError('source ends inside a %s literal' % state)
    # A final line with no trailing newline is kept as it stands.
    if line:
        if line_has_code or not line_has_comment:
            out.append(''.join(line))
    return ''.join(out)


def summary_text(source_path, output_path, characters, byte_count, limit,
                 include_dirs):
    """Return the fixed size report text."""
    lines = [
        'Othello single-file submission size',
        '===================================',
        '',
        'input source: %s' % source_path,
        'output source: %s' % output_path,
        'include dirs: %s' % (', '.join(str(d) for d in include_dirs) or 'none'),
        'character limit: %d' % limit,
        '',
        'characters: %d' % characters,
        'bytes: %d' % byte_count,
        'over limit: %s' % ('YES' if characters > limit else 'no'),
        '',
        'This is the assembled C source size, not just an encoded payload.',
    ]
    if characters > limit:
        lines += [
            '',
            'WARNING: %d characters exceeds the %d character limit by %d.'
            % (characters, limit, characters - limit),
            'The file was still written. Reduce the model payload or ask '
            'whether the limit is measured differently before submitting.',
        ]
    return '\n'.join(lines) + '\n'


def scrunch(input_path, output_path, include_dirs, limit):
    """Assemble, strip comments, write the output and its size report."""
    source_path = input_path.expanduser().resolve()
    if not source_path.is_file():
        raise ValueError('input source does not exist: %s' % source_path)

    resolved_dirs = [d.expanduser().resolve() for d in include_dirs]
    assembled = expand(source_path.read_text(encoding='utf-8'), source_path,
                       resolved_dirs)
    text = OPTIMIZATION_PRAGMA + strip_comments(assembled)

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding='utf-8')

    characters = len(text)
    byte_count = len(text.encode('utf-8'))
    summary_path = output_path.parent / 'size-summary.txt'
    summary_path.write_text(
        summary_text(source_path, output_path, characters, byte_count, limit,
                     resolved_dirs),
        encoding='utf-8')
    return {
        'output_path': output_path,
        'summary_path': summary_path,
        'characters': characters,
        'bytes': byte_count,
        'over_limit': characters > limit,
    }


def main(argv=None):
    args = parse_args(argv)
    try:
        result = scrunch(args.input, args.output, args.include_dir, args.limit)
    except (ValueError, OSError) as exc:
        print('scrunch failed: %s' % exc, file=sys.stderr)
        return 1
    print('input:  %s' % args.input)
    print('output: %s' % result['output_path'])
    print('characters: %d' % result['characters'])
    print('bytes: %d' % result['bytes'])
    print('limit: %d (%s)' % (args.limit,
                              'OVER LIMIT' if result['over_limit'] else 'within limit'))
    if result['over_limit']:
        print('WARNING: the assembled source is %d characters over the limit; '
              'it was still written' % (result['characters'] - args.limit))
    print('summary: %s' % result['summary_path'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

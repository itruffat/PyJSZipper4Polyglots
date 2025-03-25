import sys
import subprocess
import tempfile

check_commands = {
    'py': ["python3", "-m", "py_compile"],
    'ruby':["ruby", "-c"],
    'javascript':["node", "--check"],
    'lua': ["luac", "-p"]
}

def check_syntax(language:str, _filename:str) -> bool:
    return _check_syntax(check_commands[language], _filename)

def _check_syntax(args: list[str], _filename:str) -> bool:
    try:
        subprocess.run([*args, _filename], check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return False
    else:
        return True

def single_replacement_breaks(parts, position, language, token, replacement) :
    suffix = ".js"  if language == "javascript" else '.txt'
    start = token.join(parts[:position+1])
    finish = token.join(parts[position+1:])
    changed = start + replacement  + finish
    with tempfile.NamedTemporaryFile(mode='w+', suffix=suffix, delete=False) as temp_file:
        temp_file.write(changed)
        temp_file.flush()
        # If the syntax is still valid, it was inside a regex or something like that
        _answer = not check_syntax(language, temp_file.name)
    return _answer


def reformat_strings_and_replace_tokens(
        body, language, token, potential_breaker, negative_replacement, positive_replacement, unique_replacement, focused_parts):

    if token == "":
        return body, focused_parts

    parts = body.split(token)
    if len(parts) == 1:
        return body, focused_parts

    part_focused = lambda n: not focused_parts or n in focused_parts

    optional = [not single_replacement_breaks(parts, n, language, token, potential_breaker) and part_focused(n)
                for n in range(len(parts) - 1)]

    if all([o or not part_focused(o) for o in optional]):
        return body.replace(token, negative_replacement), optional

    reformatted_body = ""
    for n,p in enumerate(parts[:-1]):
        reformatted_body += p + (negative_replacement if optional[n] else token)
    reformatted_body += parts[-1]

    while unique_replacement and positive_replacement in reformatted_body:
        positive_replacement += "x"

    new_body = ""
    for n, p in enumerate(parts[:-1]):
        new_body += p + (negative_replacement if optional[n] else positive_replacement)
    new_body += parts[-1]

    return new_body, optional

def generic_token_replacement(body, language, token):
    return reformat_strings_and_replace_tokens(
        body,
        language,
        token,
        "p811p<>",
        token.replace("_", "\\x5f"),
        token[:1] + "_" + token[1:],
        True,
        []
    )[0]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(4)

    mode = sys.argv[1]
    filename = sys.argv[2]

    if mode not in check_commands.keys():
        sys.exit(5)
    try:
        if not check_syntax(mode, filename):
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(3)
    except IOError as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(2)

    sys.exit(0)

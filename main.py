import argparse
import sys

from misc.syntax_checker import generic_token_replacement, reformat_strings_and_replace_tokens

def get_input():
    parser = argparse.ArgumentParser(description="Process two files into one.")
    parser.add_argument("python_file", nargs="?", help="Path to the python file")
    parser.add_argument("js_file", nargs="?", help="Path to the javascript file")
    parser.add_argument("lua_file", nargs="?", help="Path to the python file")
    parser.add_argument("ruby_file", nargs="?", help="Path to the javascript file")
    parser.add_argument("--output", default="", help="Optional output file path")
    args = parser.parse_args()

    _python_file = args.python_file if args.python_file else input("Enter the path for the first file: ").strip()
    _js_file = args.js_file if args.js_file else input("Enter the path for the second file: ").strip()
    _lua_file = args.lua_file if args.lua_file else input("Enter the path for the third file: ").strip()
    _ruby_file = args.ruby_file if args.ruby_file else input("Enter the path for the fourth file: ").strip()
    _output = args.output if args.output else None

    return _python_file, _js_file, _lua_file, _ruby_file, _output


def profile_template(template_file):
    languages = [('python','<PYTHON CODE>'),('lua', '<LUA CODE>'),('javascript','<JS CODE>'), ("ruby","<RUBY CODE>")]
    profile = {}
    with open(template_file, "r") as template:
        template_str = template.read()

    parts = template_str.split("<DIVISION>")
    for n,part in enumerate(parts):
        total = 0
        for lan,tag in languages:
            if tag in part:
                if lan in profile:
                    raise Exception(f'TEMPLATE ERROR: Same tag ({tag}) appears more than once. (Found on {profile[lan]} and {n}))')
                profile[lan] = n
                total += 1
        if total == 0:
            raise Exception(f'TEMPLATE ERROR: Tag-less piece of code. \n (Division number {n})')
        if total > 1:
            raise Exception(f'TEMPLATE ERROR: One division has more than one tag. \n (Division number {n})')

    sorted_profile = [l for _,l in sorted([(n,l) for l,n in profile.items()])]
   
    return sorted_profile


def create_zipper(python_file, js_file, lua_file, ruby_file, template_file):

    profile = profile_template(template_file)

    with open(template_file, "r") as template:
        template_str = template.read()

    ruby_token = "ruby_long_string" if "ruby" in profile else ""
    parts = template_str.split("<DIVISION>")

    code = []

    for n, language in enumerate(profile): 
        current_part = parts[n]
        if language == "python":
            if python_file != '':
                with open(python_file, "r") as _py_file:
                    python_code = _py_file.read()
            else:
                python_code = ''

            python_code = python_code.replace("*/", "\\x2A/")
            python_code = python_code.replace(']===]', ']=\\x3D=]')
            python_code = generic_token_replacement(python_code, "py", ruby_token)
            code.append(current_part.replace("<PYTHON CODE>", python_code))


        elif language == "javascript":
            if js_file != '':
                with open(js_file, "r") as _js_file:
                    js_code = _js_file.read()
            else:
                js_code = ''

            js_code = js_code.replace('"""', '\\x22\\x22\\x22')
            js_code = js_code.replace(']===]', ']=\\x3D=]')
            js_code = generic_token_replacement(js_code, "javascript", ruby_token)
            code.append(current_part.replace("<JS CODE>", js_code))

        elif language == "lua":
            if lua_file != '':
                with open(lua_file, "r") as _lua_file:
                    lua_code = _lua_file.read()
            else:
                lua_code = ''

            lua_code = lua_code.replace('"""', '\\x22\\x22\\x22')
            lua_code = lua_code.replace("*/", "\\x2A/")
            lua_code = generic_token_replacement(lua_code, "lua", ruby_token)
            code.append(current_part.replace("<LUA CODE>", lua_code))

        elif language == "ruby":
            if ruby_file != '':
                with open(ruby_file, "r") as _ruby_file:
                    ruby_code = _ruby_file.read()
            else:
                ruby_code = ''

            # Remove stacked empty comments
            previous_ruby_code = ""
            while previous_ruby_code != ruby_code:
                previous_ruby_code = ruby_code
                # From left
                ruby_code, _ = reformat_strings_and_replace_tokens(
                    ruby_code, "ruby",
                    '"""',
                    '2"""',
                    '"""',
                    '""+"',
                    False,
                    [])

                # From right
                ruby_code, _ = reformat_strings_and_replace_tokens(
                    ruby_code, "ruby",
                    '"""',
                    '"""2',
                    '"""',
                    '"+""',
                    False,
                    [])

            # Remove triple quotes inside single quotes
            ruby_code, _ = reformat_strings_and_replace_tokens(
                    ruby_code, "ruby",
                    '"""',
                    "'",
                    '"""',
                    '\"\'+\'\"\'+\'\"',
                    False,
                    [])

            # Replace triple quotes inside strings
            ruby_code = ruby_code.replace('"""', '\\x22\\x22\\x22')

            # Replace Lua end, inside single quotes
            ruby_code, _ = reformat_strings_and_replace_tokens(
                    ruby_code, "ruby",
                    ']===]',
                    "'",
                    ']===]',
                    ']==\'+\'=]',
                    False,
                    [])

            # Replace Lua end, inside strings
            ruby_code = ruby_code.replace(']===]', ']=\\x3D=]')

            # Replace JS end, inside single quotes
            ruby_code, _ = reformat_strings_and_replace_tokens(
                ruby_code, "ruby",
                '*/',
                "'/",
                '*/',
                '*\'+\'/',
                False,
                [])

            # Replace JS end, at the end of a regex
            # TODO: look for an alternative to this, as this kills equality between 2 equal regexes
            ruby_code, _ = reformat_strings_and_replace_tokens(
                ruby_code, "ruby",
                '*/',
                "*",
                '*/',
                '{0,}/',
                False,
                [])

            # Replace JS end, inside Strings
            ruby_code = ruby_code.replace("*/", "\\x2A/")

            code.append(current_part.replace("<RUBY CODE>", ruby_code))

        else:
            raise Exception(f"ZIPPER ERROR: Invalid language ({language})")

    return ''.join(code)


if __name__ == "__main__":
    py_path, js_path, l_file, r_file, output = get_input()

    if len(l_file) == 0 or l_file in ['""',"''"]:
        answer = create_zipper(py_path, js_path, l_file, r_file,"templates/two.zipped.template")
    elif len(r_file) == 0 or r_file in ['""', "''"]:
        answer = create_zipper(py_path, js_path, l_file, r_file, "templates/three.zipped.template")
    else:
        answer = create_zipper(py_path, js_path, l_file, r_file, "templates/four.zipped.template")

    with open(output, "w") if output else sys.stdout as out_file:
        out_file.write(answer)

    exit(0)


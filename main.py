import argparse
import sys

def get_input():
    parser = argparse.ArgumentParser(description="Process two files into one.")
    parser.add_argument("python_file", nargs="?", help="Path to the python file")
    parser.add_argument("js_file", nargs="?", help="Path to the javascript file")
    parser.add_argument("--output", default="", help="Optional output file path")
    args = parser.parse_args()

    _python_file = args.python_file if args.python_file else input("Enter the path for the first file: ").strip()
    _js_file = args.js_file if args.js_file else input("Enter the path for the second file: ").strip()
    _output = args.output if args.output else None

    return _python_file, _js_file, _output


def profile_template(template_file):
    languages = [('python','<PYTHON CODE>'),('lua', '<LUA CODE>'),('javascript','<JS CODE>')]
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
        

def create_zipper(python_file, js_file, lua_file, template_file):

    profile = profile_template(template_file)

    with open(template_file, "r") as template:
        template_str = template.read()

    parts = template_str.split("<DIVISION>")

    code = []

    for n, language in enumerate(profile): 
        current_part = parts[n]
        if language == "python":
            if python_file != '':
                with open(python_file, "r") as pyfile:
                    python_code = pyfile.read()
            else:
                python_code = ''

            python_code = python_code.replace("*/", "\\x2A/")
            python_code = python_code.replace(']===]', ']=\\x3D=]')
            code.append(current_part.replace("<PYTHON CODE>", python_code))

        elif language == "javascript":
            if js_file != '':
                with open(js_file, "r") as jsfile:
                    js_code = jsfile.read()
            else:
                js_code = ''

            js_code = js_code.replace('"""', '""\\x22')
            js_code = js_code.replace(']===]', ']=\\x3D=]')
            code.append(current_part.replace("<JS CODE>", js_code))

        elif language == "lua":
            if lua_file != '':
                with open(lua_file, "r") as luafile:
                    lua_code = luafile.read()
            else:
                lua_code = ''

            lua_code = lua_code.replace('"""', '""\\x22')
            lua_code = lua_code.replace("*/", "\\x2A/")
            code.append(current_part.replace("<LUA CODE>", lua_code))

        else:
            raise Exception(f"ZIPPER ERROR: Invalid language ({language})")

    return ''.join(code)

if __name__ == "__main__":
    py_path, js_path, output = get_input()
    answer = create_zipper(py_path, js_path, "", "templates/zipped.template.original")
    with open(output, "w") if output else sys.stdout as out_file:
        out_file.write(answer)
    exit(0)


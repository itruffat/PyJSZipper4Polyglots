import os
import subprocess
import sys
import tempfile


if (cwd := os.getcwd()) not in sys.path:
    sys.path.insert(0, cwd) # Ensures that will run from the place the project is being called 
    if (script_path := os.path.dirname(os.path.abspath(__file__))) in sys.path:
            sys.path.remove(script_path)

from main import create_zipper


#
# Quick and Dirty Test Engine
#
# Goes through every file in cases, finds those that have the same name, zips them, runs them and compares outputs.
# Not great, but good as a temporary solution.
#
# Needs `node` and `python3` to run.
#


def get_script_files(directory, extension):
    return {f[:-len(extension)] for f in os.listdir(directory) if f.endswith(extension)}

def run_script(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)


def compare_outputs(test_path, test_lua, test_ruby):
    assert(not test_ruby or test_lua)

    success = []
    failure = {}

    py_files = get_script_files(test_path, ".py")
    js_files = get_script_files(test_path, ".js")
    lua_files = get_script_files(test_path, ".lua")
    ruby_files = get_script_files(test_path, ".rb")

    common_files = py_files.intersection(js_files)

    if test_lua:
        common_files = common_files.intersection(lua_files)

    if test_ruby:
        common_files = common_files.intersection(ruby_files)

    for file in sorted(common_files):
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".txt", delete=False) as temp_file:
            py_path = os.path.join(test_path, file + '.py')
            js_path = os.path.join(test_path, file + '.js')
            lua_path = os.path.join(test_path, file + '.lua') if test_lua else ''
            ruby_path = os.path.join(test_path, file + '.rb') if test_ruby else ''

            template = "templates/"
            if test_ruby:
                template += "four.zipped.template"
            elif test_lua:
                template += "three.zipped.template"
            else:
                template += "two.zipped.template"

            answer = create_zipper(py_path, js_path,lua_path, ruby_path, template)
            temp_file.write(answer)
            temp_file.flush()

            py_output = run_script(f"python3 {py_path}")
            py_output_zipped = run_script(f"python3 {temp_file.name}")
            js_output = run_script(f"node {js_path}")
            js_output_zipped = run_script(f"node {temp_file.name}")
            lua_output = py_output
            lua_output_zipped = py_output
            ruby_output = py_output
            ruby_output_zipped = py_output

            if test_lua:
                lua_output = run_script(f"lua {lua_path}")
                lua_output_zipped = run_script(f"lua {temp_file.name}")

            if test_ruby:
                ruby_output = run_script(f"ruby {ruby_path}")
                ruby_output_zipped = run_script(f"ruby {temp_file.name}")

            truths = [py_output == py_output_zipped,
                      js_output == js_output_zipped,
                      py_output == js_output,
                      lua_output == py_output,
                      lua_output == lua_output_zipped,
                      ruby_output == py_output,
                      ruby_output == ruby_output_zipped
                      ]

        if all(truths):
            success.append(file)
        else:
            failure[file] = ""
            if not truths[0]:
                failure[file] += f"PYTHON MISMATCH FOUND: \nORIGINAL\n\n{py_output}\n\nZIPPED\n\n{py_output_zipped}"
            if not truths[1]:
                failure[file] += "\n" if len(failure[file]) > 0 else ""
                failure[file] += f"JS MISMATCH FOUND: \nORIGINAL\n\n{js_output}\n\nZIPPED\n\n{js_output_zipped}"
            if not truths[2]:
                failure[file] += "\n" if len(failure[file]) > 0 else ""
                failure[file] += f"POLYGLOT MISMATCH FOUND: \nPYTHON\n\n{py_output}\n\nJAVASCRIPT\n\n{js_output}"
            if not truths[3]:
                failure[file] += "\n" if len(failure[file]) > 0 else ""
                failure[file] += f"POLYGLOT MISMATCH FOUND: \nPYTHON\n\n{py_output}\n\nLUA\n\n{lua_output}"
            if not truths[4]:
                failure[file] += "\n" if len(failure[file]) > 0 else ""
                failure[file] += f"LUA MISMATCH FOUND: \nORIGINAL\n\n{lua_output}\n\nZIPPED\n\n{lua_output_zipped}"
            if not truths[5]:
                failure[file] += "\n" if len(failure[file]) > 0 else ""
                failure[file] += f"POLYGLOT MISMATCH FOUND: \nPYTHON\n\n{py_output}\n\nRUBY\n\n{ruby_output}"
            if not truths[6]:
                failure[file] += "\n" if len(failure[file]) > 0 else ""
                failure[file] += f"RUBY MISMATCH FOUND: \nORIGINAL\n\n{ruby_output}\n\nZIPPED\n\n{ruby_output_zipped}"

    return success, failure



def four_language_templates_test():
    error_code = 0
    for with_lua in [False, True]:
        for with_ruby in [False, True]:
            if with_ruby and not with_lua:
                continue
            print(">>>>>>>>>>>>>>>>")
            if with_ruby:
                print("> Testing ruby >")
            elif with_lua:
                print("> Testing Lua >")
            else:
                print("> Testing PY+JS >")
            print(">>>>>>>>>>>>>>>>")
            sys.stdout.write("Starting test\n------------\n")
            success, failure = compare_outputs("test/cases", with_lua, with_ruby)
            if len(success) > 0:
                sys.stdout.write("SUCCESS:\n")
                for case in success:
                    sys.stdout.write(f"* {case}\n")
                sys.stdout.write("...\n")
            sys.stdout.flush()
            if len(failure) > 0:
                sys.stderr.write("FAILURE:\n")
                error_code = 1
                for case in failure:
                    sys.stderr.write(f"* {case}\n")
                    sys.stderr.write(f"{failure[case]}\n")
            sys.stderr.flush()
            sys.stdout.write("------------\nTest finished\n")
    return error_code


def double_test():
    print("::::::::::::::::")
    print(">>>>>>>>>>>>>>>>")
    print("> Testing Double Compilation >")
    new_file = create_zipper(
        "test/cases/edgecases.py",
        "test/cases/edgecases.js",
        "test/cases/edgecases.lua",
        "test/cases/edgecases.rb",
        "templates/four.zipped.template")

    with tempfile.NamedTemporaryFile(mode='w+', suffix=".js", delete=True) as temp_file:
            temp_file.write(new_file)
            temp_file.flush()
            new_file2 = create_zipper(
                temp_file.name,
                temp_file.name,
                temp_file.name,
                temp_file.name,
                "templates/four.zipped.template")

    with tempfile.NamedTemporaryFile(mode='w+', suffix=".js", delete=True) as temp_file:
        temp_file.write(new_file2)
        temp_file.flush()
        py_output = run_script(f"python3 test/cases/edgecases.py")
        py_output_zipped = run_script(f"python3 {temp_file.name}")
        js_output_zipped = run_script(f"node {temp_file.name}")
        lua_output_zipped = run_script(f"lua {temp_file.name}")
        ruby_output_zipped = run_script(f"ruby {temp_file.name}")

        truths = [
            py_output_zipped == py_output,
            js_output_zipped == py_output,
            lua_output_zipped == py_output,
            ruby_output_zipped == py_output
        ]

        if all(truths):
            print("Double compilion successful!")
        else:
            print("Double compiling the solution fails")
            return 3
        print(">>>>>")
        return 0


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        error_code = four_language_templates_test()
        if not error_code:
            error_code = double_test()
        exit(error_code)
    else:
        if sys.argv[1] == "python":
            print(create_zipper("test/cases/edgecases.py","","","","test/faux_templates/python.template"))
        if sys.argv[1] == "javascript":
            print(create_zipper("","test/cases/edgecases.js","","","test/faux_templates/js.template"))
        if sys.argv[1] == "lua":
            print(create_zipper("","","test/cases/edgecases.lua","","test/faux_templates/lua.template"))
        if sys.argv[1] == "ruby":
            print(create_zipper("","","","test/cases/edgecases.rb","test/faux_templates/ruby.template"))
        if sys.argv[1] == "all":
            print(create_zipper("test/cases/edgecases.py",
                                "test/cases/edgecases.js",
                                "test/cases/edgecases.lua",
                                "test/cases/edgecases.rb",
                                "templates/four.zipped.template")
                  )


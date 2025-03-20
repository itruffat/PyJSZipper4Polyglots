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


def compare_outputs(test_path, test_lua):
    success = []
    failure = {}
    py_files = get_script_files(test_path, ".py")
    js_files = get_script_files(test_path, ".js")
    lua_files = get_script_files(test_path, ".lua")

    common_files = py_files.intersection(js_files)

    if test_lua:
        common_files = common_files.intersection(lua_files)

    for file in sorted(common_files):
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".txt", delete=False) as temp_file:
            py_path = os.path.join(test_path, file + '.py')
            js_path = os.path.join(test_path, file + '.js')
            lua_path = os.path.join(test_path, file + '.lua') if test_lua else ''
            template = "templates/" + ("lua_" if test_lua else "" ) + "zipped.template"

            answer = create_zipper(py_path, js_path,lua_path, template)
            temp_file.write(answer)
            temp_file.flush()

            py_output = run_script(f"python3 {py_path}")
            py_output_zipped = run_script(f"python3 {temp_file.name}")
            js_output = run_script(f"node {js_path}")
            js_output_zipped = run_script(f"node {temp_file.name}")
            lua_output = py_output
            lua_output_zipped = py_output

            if test_lua:
                lua_output = run_script(f"lua {lua_path}")
                lua_output_zipped = run_script(f"lua {temp_file.name}")

            truths = [py_output == py_output_zipped,
                      js_output == js_output_zipped,
                      py_output == js_output,
                      lua_output == py_output,
                      lua_output == lua_output_zipped]


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
                failure[file] += f"LUA MISMATCH FOUND: \nORIGINAL\n\n{lua_output}\n\nZIPPED\n\n{lua_output_zipped}"
    return success, failure



if __name__ == "__main__":
    error_code = 0
    for with_lua in [False, True]:
        print(">>>>>>>>>>>>>>>>")
        print("> Testing Lua >" if with_lua else "> Testing PY+JS >")
        print(">>>>>>>>>>>>>>>>")
        sys.stdout.write("Starting test\n------------\n")
        success, failure = compare_outputs("test/cases", with_lua)
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
    exit(error_code)



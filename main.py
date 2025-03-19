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

def create_zipper(python_file, js_file, template_file, python_first ):

    with open(template_file, "r") as template:
        template_str = template.read()
        python_part, js_part = template_str.split("<DIVISION>")
        if not python_first:
            js_part, python_part =  [python_part, js_part]


    with open(python_file, "r") as pyfile:
        python_code = pyfile.read()
        python_code = python_code.replace("*/", "\\x2A/")
        python_part = python_part.replace("<PYTHON CODE>", python_code)

    with open(js_file, "r") as jsfile:
        js_code = jsfile.read()
        js_code = js_code.replace('"""', '""\\x22')
        js_part = js_part.replace("<JS CODE>", js_code)

    return python_part + js_part if python_first else js_part + python_part

if __name__ == "__main__":
    py_path, js_path, output = get_input()
    answer = create_zipper(py_path, js_path, "templates/zipped.template", False)
    with open(output, "w") if output else sys.stdout as out_file:
        out_file.write(answer)
    exit(0)
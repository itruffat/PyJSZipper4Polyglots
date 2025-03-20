# Python/JS/LUA Zipper for Polyglots
(A Zipper tool to create Python/JScript/Lua Polyglots)


# Introduction

Inspired by [this youtube video](https://www.youtube.com/watch?v=dbf9e7okjm8), I decided to tackle the problem of 
encoding one python program + one javascript program in a single file that can be run by the interpreters of both 
languages. 

When the original sources that were encoded happens to do the same thing in both languages, then the result can be
described as a polyglot program. Since comments are used to mask the second implementation (instead of trying to find a
common syntax that would work for both languages and solve the problem using that syntax), this solution is called a
zipper.

In the end I also added LUA to the equation, having 2 different templates.

-----

## Idea behind the PY+JS answer

So, the idea is to use comments to mask the execution. A double `//` is a comment in javascript but a natural division
in Python, so `1 // len("""` is the start of a multi-line string in Python but a comment in Javascript. If we simply
finish with `//""")`, everything in the middle will be ignored by Python.

    1 // len("""

    <JS CODE>

    //""")

On that same note, if we add a `/*` in one of those ignored lines and then add one `*/` at the end, then the code in the
middle will actually be ignored by Javascript. By allowing closing and opening a pair of `"""`, that will create an
space that Python can actually read.

    1 // len("""
    /*""")

    <PYTHON CODE>

    """
    *///"""

So the final answer would be:

    1 // len("""
    /*""")

    <PYTHON CODE>

    """
    *///"""

    <DIVISION>

    1 // len("""

    <JS CODE>

    //""")

Since we are repeating lines there, we can compress this a little bit by adding the Javascript right before the python.

    1 // len("""
    <JS CODE>
    /*""") <DIVISION>
    <PYTHON CODE>
    """
    *///"""

 ------

 ## Edge-case handling for PY+JS

Taking into account we are introducing text into a template, it's important to think about the edge-cases. If the Python 
code contains a `*/` anywhere, then it would break our template. The same goes for the Javascript code, which could 
break things by having a `"""` in it.

As far as I am aware, both combinations of characters are illegal on the syntax of the other language, but they are
still a problem if they appear inside strings or comments. We don't care about comments, but strings are relevant. 
For example,  a Python implemented JS-interpreter would need to have the `*/` string on its Tokenizer to work.

Luckily, both languages allow us to add hex-codes inside strings, so we just need to make sure to replace those. The 
code inside `main.py` takes care of it.


-----

## Idea behind the LUA answer

#### <TODO\>

------

## Edge-case handling for PY+JS

#### <TODO\>

------

## TODO (maybe)

* Add same test cases, replace the test engine for a real one.
* Add documentation for LUA
* Add other languages. (will have to check compatibility)

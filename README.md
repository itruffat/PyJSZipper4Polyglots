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

## Idea behind the original answer (PY+JS)

The idea is to use comments, strings and NOPs (operations that do nothing, like evaluating a number) to mask the 
execution. A double `//` is a comment in javascript but a natural division in Python, so `1 // len("""` is the 
start of a multi-line string in Python but a NOP followed by a comment in Javascript. If we simply finish this with 
`//""")` at then end of the block, everything in the middle will be ignored by Python.

    1 // len("""
    <JS CODE>
    //""")
#### JS solution

On that same note, if we add a `/*` inside one of those ignored lines followed by a `*/` at the end, then the text in 
the middle will also be ignored by Javascript. As a result, by opening and closing a pair of `"""` in the middle, 
that will create a new space that's readable by Python but not Javascript.

    1 // len("""
    /*""")
    <PYTHON CODE>
    """
    *///"""
#### PYTHON solution

Combining both answers will gets us a code that' valid in both interpreter, but twhere each part will be ignored by the
other interpreter.

    1 // len("""
    /*""")
    <PYTHON CODE>
    """
    *///"""
    <DIVISION>
    1 // len("""
    <JS CODE>
    //""")
#### JS + PYTHON solution

Finally, we can compress that solution by taking advantage of the repeated lines.  Adding the Javascript right before 
the python block leads to smaller footprint.

    1 // len("""
    <JS CODE>
    /*""")
    <DIVISION>
    <PYTHON CODE>
    """
    *///"""
#### Compressed JS + Python solution

 ------

 ## Edge-case handling (PY+JS)

Taking into account we are introducing text into a template, it's important to think about the edge-cases. If the Python 
code contains a `*/` anywhere, then it would break our template. The same goes for the Javascript code, which could 
break things by having a `"""` in it.

As far as I am aware, both combinations of characters are illegal on the syntax of the other language, but they are
still a problem if they appear inside strings or comments. We don't care about comments, but strings are relevant. 
For example,  a Python implemented JS-interpreter would need to have the `*/` string on its Tokenizer to work.

Luckily, both languages allow us to add hex-codes inside strings, so we just need to make sure to replace those. The 
code inside `main.py` takes care of it.


-----

## Adding a third language (LUA)

So, first let's try to understand the tools we have at our disposal. 

With LUA we can use comments `--` and different flavours of multiline comments. Generally we would prefer the simplest 
multi-line delimiter, but in this case the `--[[` delimiter ends when it first matches a `]]` token, which could appear 
outside of a string in both Python and Javascript. As such, we will use the second most simple delimiter, the one that 
starts with `--[===[`and ends with `]===]`. This means that `]===]`, an invalid syntax in both languages, will be the 
one we use to handle.

Having to manipulate 3 languages at once, there are some new complexities to take into account. The techniques we were 
using previously are no longer enough, and we need to thread more carefully. While Python would allow a sentence such as 
`1 -- 1 // len("""` , neither LUA nor Javascript can accept such a sentance. 

* LUA requires each sentence to **either be comments or do something**, so we can no longer relay on expressions that 
  evaluate to numbers or strings. 

  * We would need to do something like `_ = 1 -- 1 // len("""` for it to be LUA 
  compatible. ( LUA will interpret it as `_ = 1`, ignoring the comment)


* JAVASCRIPT has no innate operation for `<object> -- <object>` . 
  * `--` is a unary operation that either reduces the value of a variable before or after execution. 
    (the same way it works for C/C++)


Having clarified that, there is still one possibility that is correct in these 3 languages: all of them accept the 
expression `_ = 1` as valid. This means that we can define a variable named `_` for Javascript without breaking 
compatibility with LUA or Python. [*] 

Once we have a named variable defined, we can use `--<variable> ` as a valid expression in Javascript and as comment in 
LUA. Lastly Python interprets `--<variable>` as a multiplication of two negatives (equivalent to `-1*-1*<variable>`), 
so to make the expression also valid in Python while forcing a comment in Javascript we can use the same trick we used 
in the PY+JS solution `--_ // 1`. (or to be precise `--_ // len("""` as we want Python to do an NOP) 

    _ = 1
    --_ // len("""
    --_ /*
    --[===[""")
    del _
    <PYTHON CODE>
    _ = 1
    """]===]
    -- *///"""
#### PYTHON solution


    _ = 1
    --_ // 1 + len("""
    --_ /*
    --[===[ 
    */
    delete _
    { <JS CODE> }
    // ]===]
    --_ //""")
#### JS solution

    _ = 1
    --_ // 1 + len("""
    --_ /*
    _=nil
    <LUA CODE>
    --_ */
    --_  // """)
#### LUA solution


And the combined solution would be smaller than 3 combined.

    _ = 1
    --_ // len("""
    --_ /* 
    _=nil
    <LUA CODE>
    --[===[ */ delete _
    <DIVISION>
    { <JS CODE> } /*""")
    del _
    <DIVISION>
    <PYTHON CODE>
    """ ]===]
    -- */ //"""
#### Compressed JS + Python + Lua solution



[*] The downside of this solution is that we no longer can use strongly typed languages or languages that require 
specific ways to populate variables.

------

## Edge-case handling (LUA)

Since LUA shares the capability of using hex encoding inside strings, the solution is similar to what we've already
one with Javascript and Python. Just replace the `""""` and `*/` for one equivalent string with hex-codes.

Our new edge case is now the delimiter LUA uses to end multiline comments, which in our case is `]===]`. Again, this can
be solved by replacing some of those characters with their equivalent hex-code.

There is also the matter of the variable `_` in all 3 languages. There may be a piece of code that actually uses `_`, 
so having it defined could be a problem. In all 3 programs we deleted the variable before using it.
   * `del` in Python
   * `=nill` in Lua.
   * `delete` in Javascript, as well as placing the code inside `{}`.
      * The latter avoids problems with `consts`.

-----

## Going beyond with a fourth language (Ruby)

### Introduction

This one was harder to do than the previous one by a country-mile. Combining 2 languages was easy-ish, 3 languages was a
head-scratcher, but 4 languages was  challenge. Still, it was worth going through it until we could find a solution.

The risky part is that languages sometimes change, for example python 3.10 removed a lot of 'hack-ish' ways of working 
that would have been really useful for this task. Therefore, this solution is as-is with current versions of 
interpreters (as of 22/3/2025). It may break in the future

    _=1
    __={}
    --_ ; "#{#1+1}" ; 1 // 1 and """
    --_ || //}"
    --_ ; `false && ${/*}`
    _=#__--[===[
    1
    <RUBY CODE>
    =begin
    <DIVISION>
    """
    <PYTHON CODE>
    """
    <DIVISION>
    */1}`;{
    <JS CODE>
    };`${/*
    <DIVISION>
    #]===]
    <LUA CODE>
    --[===[
    =end
    #]===]
    --_; `false && ${_*/1}`
    --_ ; "#{#1+1}" ; 1 //
    _=--_ && //}"""
    1

This solution mostly abuses String-Interpolation, and their different implementations. Since no two languages use the 
same token delimiters to make String-Interpolation, opening string interpolation allows us to write comment markers
(either `#` or `/*`) that will be interpreted by the other language as being part of a string.

One particular hurdle to overcome was that JS does it's String-Interpolation inside backsticks (` `` `), which can not
be used on Python or LUA, and which is interpreted as a SYSTEM-CALL by Ruby. 

* The former can simply be solved by first making sure that neither language are reading the lines with backsticks.
  Not a trivial task, but easy enough with LUA being skippable every line by using `--_;` and Python skipping whole
  paragraphs using multines comments `"""`.


* The latter requires a bit of knowledge of the SYSTEM-CALL itself. Since on my SYSTEM the SYSTEM-CALL tries to run from
  BASH, I simply had to find a way to make the comment part be ignored. Options were adding a comment token (`#`) or 
  doing an statement that will overload (`false && <x>`). Ended up choosing the latter, as it looks more resilient to
  different terminals with different comment tokens.


## Advance ideas


'TBD'

------

## TODO (maybe)

* Add same test cases, replace the test engine for a real one.
* Modify main to also populate ruby.
* Add explanation in details for ruby

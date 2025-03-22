# Python/JS Zipper for Polyglots
(A Zipper tool to create Python/JScript/Lua/Ruby Polyglots)


# Introduction

Inspired by [this youtube video](https://www.youtube.com/watch?v=dbf9e7okjm8), I decided to tackle the problem of 
encoding one python program + one javascript program in a single file that can be run by the interpreters of both 
languages. 

When the original sources that were encoded happens to do the same thing in both languages, then the result can be
described as a polyglot program. Since comments are used to mask the second implementation (instead of trying to find a
common syntax that would work for both languages and solve the problem using that syntax), this solution is called a
zipper.

In the end I also added LUA and Ruby to the equation, having 3 different templates.

-----

## Original answer (PY+JS)

### \> Main idea

The idea is to use comments, strings and NOPs (operations that do nothing, like evaluating a number) to mask the 
execution. A double `//` is a comment in javascript but a natural division in Python, so `1 // len("""` is the 
start of a multi-line string in Python but a NOP followed by a comment in Javascript. If we simply finish this with 
`//""")` at then end of the block, everything in the middle will be ignored by Python.

#### :: JS solution
    1 // len("""
    <JS CODE>
    //""")

On that same note, if we add a `/*` inside one of those ignored lines followed by a `*/` at the end, then the text in 
the middle will also be ignored by Javascript. As a result, by opening and closing a pair of `"""` in the middle, 
that will create a new space that's readable by Python but not Javascript.

#### :: PYTHON solution
    1 // len("""
    /*""")
    <PYTHON CODE>
    """
    *///"""

Combining both answers will gets us a code that' valid in both interpreter, but twhere each part will be ignored by the
other interpreter.

#### :: JS + PYTHON solution
    1 // len("""
    /*""")
    <PYTHON CODE>
    """
    *///"""
    <DIVISION>
    1 // len("""
    <JS CODE>
    //""")

Finally, we can compress that solution by taking advantage of the repeated lines.  Adding the Javascript right before 
the python block leads to smaller footprint.

#### :: Compressed JS + Python solution
    1 // len("""
    <JS CODE>
    /*""")
    <DIVISION>
    <PYTHON CODE>
    """
    *///"""


### \> Edge-case handling (PY+JS)

Taking into account we are introducing text into a template, it's important to think about the edge-cases. If the Python 
code contains a `*/` anywhere, then it would break our template. The same goes for the Javascript code, which could 
break things by having a `"""` in it.

As far as I am aware, both combinations of characters are illegal on the syntax of the other language, but they are
still a problem if they appear inside strings or comments. We don't care about comments, but strings are relevant. 
For example,  a Python implemented JS-interpreter would need to have the `*/` string on its Tokenizer to work.

Luckily, both languages allow us to add hex-codes inside strings. We just need to make sure to replace those. The 
code inside `main.py` takes care of it. 

#### :: Replacement snippets
    python_code = python_code.replace("*/", "\\x2A/")
    [...]
    js_code = js_code.replace('"""', '\\x22\\x22\\x22')


-----

## Adding a third language (LUA)

### \> Initial assestment

So, first let's try to understand the tools we have at our disposal. 

With LUA we can use comments `--` and different flavours of multiline comments. Generally we would prefer the simplest 
multi-line delimiter, but in this case the `--[[` delimiter ends when it first matches a `]]` token, which could appear 
outside of a string in both Python and Javascript. As such, we will use the second most simple delimiter, the one that 
starts with `--[===[`and ends with `]===]`. This means that `]===]`, an invalid syntax in both languages, will be the 
one we use to handle.

Having to manipulate 3 languages at once, there are some new complexities to take into account. The techniques we were 
using previously are no longer enough, as we can not simply use expressions like `1 -- 1 // len("""`.  (That would run 
in Python, but neither LUA nor Javascript can accept such sentence). 

* LUA requires each sentence to **either be comments or do something**, we can no longer relay on expressions that 
  simply evaluates to a numbers or a string. 

  * We would need to do something like `_ = 1 -- 1 // len("""` for it to be LUA compatible. ( LUA will interpret it 
    as `_ = 1`, ignoring the content after the `--` limiter)


* JAVASCRIPT has no innate operation for `<object> -- <object>` . 
  * `--` is a unary operation that either reduces the value of a variable before or after execution. 
    (the same way it works for C/C++) This variable NEEDS to be defined before being reduced.

### \> Solution description

There is still one possibility that is correct in these 3 languages: all of them accept the expression `_ = 1` as valid. 
This means that we can define a variable named `_` for Javascript to reduce without breaking compatibility with LUA or 
Python. The downside of this solution is that we no longer can use strongly typed languages or languages that require 
specific ways to populate variables, but that's a trade-off we should probably take.

Once we have a named variable defined, we can use `--<variable> ` as a valid expression in Javascript and as comment in 
LUA. Lastly Python interprets `--<variable>` as a multiplication of two negatives (equivalent to `-1*-1*<variable>`), 
so to make the expression that's valid in Python while being a comment in Javascript we can use the same trick we used 
in the PY+JS solution `--_ // 1`. (or to be precise `--_ // len("""` as we want Python to do an NOP) 

#### :: PYTHON solution
    _ = 1
    --_ // len("""
    --_ /*
    --[===[""")
    del _
    <PYTHON CODE>
    _ = 1
    """]===]
    -- *///"""

#### :: JS solution
    _ = 1
    --_ // 1 + len("""
    --_ /*
    --[===[ 
    */
    delete _
    { <JS CODE> }
    // ]===]
    --_ //""")

#### :: LUA solution
    _ = 1
    --_ // 1 + len("""
    --_ /*
    _=nil
    <LUA CODE>
    --_ */i
    --_  // """)


And the combined solution would be smaller than 3 combined.

#### :: Compressed JS + Python + Lua solution
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


### \> Edge-case handling (LUA)

Since LUA shares the capability of using hex encoding inside strings, the solution is similar to what we've already
one with Javascript and Python. Just replace the `""""` and `*/` for one equivalent string with hex-codes.

Our new edge case is now the delimiter LUA uses to end multiline comments, which in our case is `]===]`. Again, this can
be solved by replacing some of those characters with their equivalent hex-code.


#### :: New replacement snippet
    python_code = python_code.replace(']===]', ']=\\x3D=]')
    [...]
    js_code = js_code.replace(']===]', ']=\\x3D=]')
    [...]
    lua_code = lua_code.replace('"""', '\\x22\\x22\\x22')
    lua_code = lua_code.replace("*/", "\\x2A/")

There is also the matter of the variable `_` in all 3 languages. There may be a piece of code that actually uses `_`, 
so having it defined could be a problem. In all 3 programs we deleted the variable before using it.
   * `del` in Python
   * `=nill` in Lua.
   * `delete` in Javascript, as well as placing the code inside `{}`.
      * The latter avoids problems with `consts`.

-----

## Going beyond with a fourth language (Ruby)

### \> Introduction

This one was harder to do than the previous one by a country-mile. Combining 2 languages was easy-ish, 3 languages was a
head-scratcher, but 4 languages was  challenge. Still, it was worth going through it until we could find a solution.

The risky part is that languages sometimes change, for example python 3.10 removed a lot of 'hack-ish' ways of working 
that would have been really useful for this task. Therefore, this solution is as-is with current versions of 
interpreters (as of 22/3/2025).  It may break in the future, no promises there.

For this we will go the other way around, start with the solution and trace our way back.

#### :: Final Solution 
    _=1
    __={}
    --_ ; "#{#" ; 1 // 1 and """
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
    --_ ; "#{#" ; 1 //
    _=--_ && //}"""
    1

### \> Understanding the new challenge

Ruby is a fairly straightforward language, similar to the previous 3 we worked with. It also allows `_=1`, which is good
for us as it will allow us to recycle previously used tricks. Additionally, `--{variable}` is interpreted by Ruby in the 
same way as in Python (`-1*-1*{variable}`), meaning that's another trick we can recycle.

However, there are some of the unique syntactical properties of Ruby does make our job harder. In particular, in this 
language `//` is a way to define a regex, not a division or any other operation like that. While regex can be defined 
with a variable name for other languages (such as `//x` or `//i`) there is no way to add a value BEFORE the regex. This 
means that our Python+JS technique of using `1 // 1`  will not be available outside of Ruby comments. 

Comments and Multilines strings in Ruby will also not be trivial to add to our code, as the single line is a `#` symbol, 
which Javascript can not use outside a class contex. Multiline comments require the use of the awkward `=begin`/`=end` 
at the start of the line, making it hard to match with the other languages. Multiline stings are defined by the 
convention `<<-{variable}`, which is compatible with both Python and Javascript if we simply add a character at the 
start `1<<-{variable}`. (*Small spoiler alert: we will not take advantage of this last property*)

Lastly, Ruby has a command interpreted strings which can be run by putting SYSTEM call between backsticks (` `` `). 
This will be relevant, as Javascript also uses backsticks for some string manipulation. Assuming the underlying system
is BASH, this can lead to NOP calls in Ruby by writing the sentence `` <x> `` as a BASH comment (`#<x>`) or making use
of shortcut (`false && <x>`).

### \> Key solution

The current solution we found relays on abusing String-Interpolation, and their different implementations. Since no two 
languages use the  same token delimiters to make String-Interpolation, opening string interpolation allows us to write 
comment markers(either `#` or `/*`) that will be simply interpreted by the other language as being part of a string.

In total we need to make use of 2 String-interpolations, the one in Ruby and the one in Javascript, plus a trick to 
ignore mask a Ruby comment in LUA.

#### :: Ruby interpolation

The idea with Ruby is fairly straight-forward, as interpolation is done inside a regular string by using the 
`"${<value>}"` call. We simply add a comment token in the value to evaluate (`#`)

    "#{# <IGNORED BY RUBY>
    <SOME VALUES>}"

Looking at some of our previous tricks, we can re-use `--_` and `1//1` to comment out LUA and start a Python comment. 
Since Javascript is not commented, the second sentences has to also be legal in it. For it we do a trick with the `||` 
token by adding it before the '//'. 

* In Javascript everything after the `//` will be interpreted as a comment, so if we add ANY value or variable on the 
  next line, Javascript will take it as `--_ || --_`, which is a valid syntax.

* In Ruby the `//` will be taken as a regex, making the syntax `--_ || //` legal. The next line `--_` is also legal and
works as a NOP.

So that will leave us with the following snippets.

    _=1
    --_ ; "#{#" ; 1 // 1 and """
    --_ || //}"
    --_


The end goal of this exploit is that, while still not having started any long-comment/string on any of the 4 languages, 
we get a legal snippet that uses a triple quote marks (`"""`). From Python's perspective, the solution we showed above 
will be read as the following.

    _=1
    --_ ; "#{#" ; 1 // 1 and """
    <IGNORED BY PYTHON>
     """

#### :: Javascript interpolation

One particular hurdle to overcome was that JS does it's String-Interpolation inside backsticks (` `` `), which can not
be used on Python or LUA, and which are interpreted as a SYSTEM-CALL by Ruby. However, we can tackle the former problem 
by making sure we only make this call after both LUA and Python are treating the code as Comments/strings. The latter 
can also be solved by forcing the operation to be a NOP in Bash, using `false && <x>`. 

    `false && ${/* <IGNORED BY JS>
    <IGNORED BY JS>
    `false && ${_*/<SOME VALUE>}`

We can then add the techniques we've been using to make this exploit LUA  compatible (`--_`). We can not actually adapt
it to be compatible with Python syntax, so we will need to do it once Python interprets this as a String. The end result
is similar to the one above.

    _=1
    --_ ; `false && ${/*}`
    <IGNORED BY JS>
    --_; `false && ${_*/1}`


#### :: Multi-line Lua Comment + Ruby 

With the previous two sections we are able to be on NOP sections for both, Python and Javascript. We are easily able to
use a single-line comment in Lua that is compatible in Ruby (`--_`), but starting a multi-line comment is more tricky.

Lua requires the use of `--[===[`, and Ruby the use `=begin`, none of which create a valid syntax on the other language. 
In theory, we could use `<<-{Variable}` , but this adds a huge roadblock as we could never use the name of the variable
in the comments that RUBY is ignoring. Moreover, the code has failed to run properly in some compilers.
There is a better solution we will discuss afterwards.

    {x} = 1
    _ = 1 <<-{x}
    <IGNORED BY RUBY AS LONG AS IT DOESN'T CONTAIN {x}>
    {x}

A single-line comment in Ruby can be invoked by calling a `#`, if we can place one of those in LUA valid syntax, then we
could add the `--[===[` at the end to start a multi-line LUA comment. Luckily, `#` is a valid symbol in LUA, getting the
length of a variable. All languages accept the definition of `__={}`, so we can set that up for the snippet `#__` to 
work with LUA. As Ruby will be missing the rest of the line, we need to include some data below.

    _=1
    __={}
    _=#__--[===[
    1
    <CODE IGNORED BY LUA>
    #]===]

### \> Edge-case handling (LUA)

TBD

------

## TODO (maybe)

* Add same test cases, replace the test engine for a real one.
* It might be possible to remove the ";" for "||" values in the last template. (Check)
* Modify main to also populate ruby.
* Add explanation in details for ruby

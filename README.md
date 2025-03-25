# Python/JS Zipper for Polyglots
(A Zipper tool to create Python/JScript/LUA/Ruby Polyglots)

# Introduction

Inspired by [this youtube video](https://www.youtube.com/watch?v=dbf9e7okjm8), I decided to tackle the problem of 
encoding one python program + one javascript program in a single file that can be run by the interpreters of both 
languages. 

When the original sources that were encoded happens to do the same thing in both languages, then the result can be
described as a polyglot program. Since comments are used to mask the second implementation (instead of trying to find a
common syntax that would work for both languages and solve the problem using that syntax), this solution is called a
zipper.

In the end I also added LUA and Ruby to the equation, having 3 different templates.

# How to Use

    Pythone main.ppy <Python File> <Js File> <Lua File> <RubyFile>

> If you want to run only Python/JS or only Python/Js/Lua you can do the following...

    Pythone main.ppy <Python File> <Js File> <Lua File> ''
    Pythone main.ppy <Python File> <Js File> '' ''

## Goals

The goal of this repo is to be as straight-forward and use as little `eval`/`exec`/`;` as possible. Additionally, the 
code bases should be callable with as little restrictions as possible. 

The creation of the output file should be the one to the care of most edge cases, meaning that most programs should run
ok. Some exceptions are to be expected, for example all self-referencing files are going to fail, and files that use
`exec` or `eval` may fail as well. Additionally, some Ruby regex may fail their identity function after creation. All 
these are considered acceptable looses.


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

#### :: Compressed JS + Python + LUA solution
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
   * `=nill` in LUA.
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
    --_ * "#{#"  * 1 // 1 if False else """"
    --_ || //}".to_i
    --_ || `false && ${/*}`
    _=#__--[===[
    1
    <RUBY CODE>
    <<-ruby_long_string
    <DIVISION>
    """
    <PYTHON CODE>
    """
    <DIVISION>
    */1}`
    { <JS CODE> }
    `${/*
    <DIVISION>
    #]===]
    <LUA CODE>
    --[===[
    ruby_long_string
    #]===]
    --_ || `false && ${_*/1}`
    --_ || "#{#" ; 1 //
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

Finally, we can then improve this answer further by adding a multiplication and a `to_i`, allowing Ruby to understand 
the values as numbers. Since Python will now have problems with precedence, we change the `and` into a `if the else`.
That way, we can remove the `;` from the code.

    _=1
    __={}
    --_ * "#{#"  * 1 // 1 if False else """"
    --_ || //}".to_i
    --_

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


#### :: Multi-line LUA Comment + Ruby 

With the previous two sections we are able to be on NOP sections for both, Python and Javascript. We are easily able to
use a single-line comment in LUA that is compatible in Ruby (`--_`), but starting a multi-line comment is more tricky.

LUA requires the use of `--[===[`, and Ruby the use `=begin`, none of which create a valid syntax on the other language. 
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

### \> Multi-line string/comment for Ruby

In our current template, Ruby is the most deeply zipped language, meaning we are free to use any tool the language can 
provide. However, due to Ruby's multiline comments/strings , our options are surprisingly limited. All of them have 
their own set of drawbacks, and can lead to different issues. 

There is one option we can discard from the get-go. Using the `_ = %q( <a multine>)` multiline line is outright 
unusable for us, as it prohibits the use of `)` on any of our other code-bases. While theoretically possible to do this,
in practice it'd be accepting a herculean task for no good reason. With this in mind,  we can move to the other 2 
options.

#### :: Using '=being/=end' Option
    =being
    <This is a multine comment and will be ignored>
    =end

This one is more realistic than the option of using `%q`, but still has some issues. Not being able to use `=end` on any 
of our other code-bases can be a weird limit to impose. There are cases where a variable name may start with `end`, so 
we would need to change the `end` section at every appearance of that variable.

Moreover, some `=end` may appear inside a string or a regex, so we would need to thread carefully when deciding what to 
change and what not. What's worse, LUA  has `end` as a keyword, so we can not change every `non-string end` in the code 
either.


    endymion=12
    after_endemyion=endymion + 1

    current_position = 1
    while current_position  !== after_endemyion:
                 print(" ==end of the game can only be reach after surpassing endemyion== ")
                 keep_going()

All in all, this is problem we can not realistically tackle without using AST for most languages, which is something
I'd like to avoid in this tool. As such, we should look for an alternative.

#### :: Long String with random name Option
    _ = <<-FLEXIBLE_VARIABLE_NAME
    <This is a multine string and will be ignored>
    FLEXIBLE_VARIABLE_NAME

This option is similar but slightly better than using `end`. Not only is it more implicit that we have to worry about 
the cases where the variable does not start with `=`,  we can also select a specific string to avoid any unwanted 
collisions. (such as the `end` collision with LUA)


* If the string appears in other codes as part of a Sting, we can replace it with some hexcodes, similarly to how we
  solved other edge-cases. This ensures that it will not collision with it.


* If the string appears as a variable name, we can simply rename it to something else. That new something else should be 
  something that's not already on the code. (we can keep iterating until we find a string like that)

Finding which variables need changing and which ones do not can be done is simple, and can be done by making a breaking 
change and checking if the  syntax is still valid. For exampling, turning `test1` into `+t-7est1*`. If the value was 
inside a string or a regex, then the syntax will still be valid. However, if the syntax is a variable, it will break the
code.

In the end we went with `ruby_long_string` as the name of that should not be repeated on other languages. By using a 
simple function, variables that include that name will be changed for `r_uby_long_string`. And if that already exists, it 
will keep appending `x`s until we get to a value that was not on the original code.


### \> Edge-case handling (Ruby)

In the last section we analyzed the edge-cases related to the `multi-line comment format` we choose to use. This lead to 
adding a few lines of code to make sure we handle those edge-cases in the other languages.

    ruby_token = "ruby_long_string" if "ruby" in profile else ""
    [...]
    lua_code = generic_token_replacement(lua_code, "lua", ruby_token)
    [...]
    js_code = generic_token_replacement(js_code, "javascript", ruby_token)
    [...]
    python_code = generic_token_replacement(python_code, "py", ruby_token)

However, the edge-cases in Ruby are harder, due to the fact that we have to deal with 5 different structures:
* Double-quoted Strings
* Single-quoted strings
* Regexes
* Comments
* Terminal Calls

Comments and Terminal Calls are something we are fairly free to ignore, since they will not be a problem for us. Regexes 
are also something we are going to **partially ignore** here. Their level of complexity is a lot higher, and fixing them
properly without an AST is virtually impossible. But what's more, even limiting ourselves to strings we  find ourselves 
with issues.

Mostly because double-quoted and single-quoted strings work differently. While we can re-use our hexencoding trick for
double-quoted strings (and Terminal Calls), this does not work with single-quotes. Instead, we need to tackle both of 
these cases separately.

There is one particularly problematic case, which is that Ruby auto-appends strings. So `""""` (which is a super string of
Python's `"""`) is perfectly valid. The way to fix it depends on wherever this is happening inside a single quote, 
inside a terminal call or as 2 strings in a row.

* We first try to see if it's just 2 strings in a row. For this we use the same replacement-then-check-validity trick we
  used in the previous section. If it's 2 strings in a row, we can reduce it to a single string. `"<content>""<empty>"` 
  or `"<empty>""<content>"` into `"content"` . This is looped until no more 2 strings in a row are found.


* Then we try to check for single-quotes. Since single quotes can be appended, we simply change `'""""'` into the
  equivalent `'"'+'"'+'"'`.


* Lastly, we use the trick of hexecoding the 3 triple-quotes for multi-line comments and Terminal Calls.


For both `]===]` and `*/` we also use a technique similar to the one of `"""`. We devide the string into 2 for single 
strings, and hex-encode for the others. 

Last but not least, one additional case we took care of for regexes is `*/`. Since regexes do not work for  with 
hex-replacements of special chars. Not only that, but ending a regex with `*/` is fairly common. So instead, we replaced
it with `{0,}/`. This should be syntactically equivalent, meaning that the regex should still parse the same strings. 
The only difference is that if you try to compare 2 strings, they will no longer be equivalent. This case was considered
weird enough to consider skipping it.

------

## TODO (maybe)

* Add same test cases, replace the test engine for a real one.
* It might be possible to remove the ";" for "||" values in the last template. (Check)
* Fix Python issues with `"""` inside its own comments.

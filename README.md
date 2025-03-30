# Python/JS Zipper for Polyglots
(A Zipper tool to create Python/JScript/LUA/Ruby Polyglots)

# Introduction

Inspired by [this YouTube video](https://www.youtube.com/watch?v=dbf9e7okjm8), I set out to solve the problem of 
encoding both a Python and a JavaScript program in a single file that can be executed by the interpreters of both 
languages.

The goal behind this technique is to create a program that performs the same function in both languages, resulting in 
what’s known as a 'polyglot' program. Rather than trying to find a common syntax that works for both languages, we 
carefully design the file so that one language's implementation is ignored by the other. This method is referred to as a
"zipper."

As the challenge grew more exciting, I decided to expand the project further, adding LUA and Ruby, which gave us three 
different combinations to work with. (PY+JS, PY+JS+LUA and PY+JS+LUA+RB)

## How to Use

To run:

    Python3 main.py <PythonFile> <JsFile> [<LuaFile>] [<RubyFile>] --output [OutputFile]

 * Both Lua and Ruby files are optional. Lua is only necessary if you wish to run the program with Ruby as well.
 
 * The output file is also optional. If no output file is provided, the output will be redirected to `stdout`.


To test:

    Python3 test/qnd_test_engine.py [<DisplayLanguageOutputInstead>]


* The engine will load and run the scripts present at `test/cases`, then compare the results with the original 
  `unzipped` version. New test can be added, as long as:
  * [A] There is a file for each language in a valid language combination. 
  * [B] They don't require use input and are not infinite loops.


* DisplayLanguageOutputInstead is an optional variable that will run the `edgecases` script for that specific language 
  and print an output. Possible values are `python` / `javascript` / `lua` / `ruby` / `all`. This is mostly useful for 
  development. 

## Goals

The goal of this repository is to keep things as straightforward as possible, minimizing the use of `eval`, `exec`, and 
`;`. Furthermore, the codebases should be callable with minimal restrictions.

The creation of the output file is designed to handle most edge cases, ensuring that most programs run correctly. 
However, some exceptions may occur. For instance, self-referencing files will fail, and files that rely on exec or eval 
might not work. Additionally, certain Ruby regex may fail their identity function after being created. These are all 
considered acceptable trade-offs.

-----

## Original answer (PY+JS)

### \> Main idea


The approach relies on using comments, strings, and NOPs (no-operation expressions, such as evaluating a number) to 
mask execution. For example, `//` is a comment in JavaScript but represents integer division in Python. This allows 
constructs like `1 // len("""` to serve as the start of a multi-line string in Python while being interpreted as a no-op 
followed by a comment in JavaScript. By closing the block with `//""")`, everything in between is ignored by Python, 
effectively hiding one implementation within the other.

#### :: JS solution
    1 // len("""
    <JS CODE>
    //""")

Similarly, if we insert a `/*` inside one of these ignored lines and close it with `*/`, everything in between will also 
be ignored by JavaScript. This means that by strategically placing a pair of `"""` inside this block, we can carve out a 
space that is readable by Python but completely invisible to JavaScript.

#### :: PYTHON solution
    1 // len("""
    /*""")
    <PYTHON CODE>
    """
    *///"""

By combining both techniques, we can create code that is valid in both interpreters, with each part being ignored by the 
other. This allows us to embed multiple implementations within a single file while keeping them functionally isolated.

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

Finally, we can optimize the solution by reducing redundancy. Placing the JavaScript code right before the Python block 
helps minimize the overall footprint while maintaining compatibility across both interpreters.

#### :: Compressed JS + Python solution
    1 // len("""
    <JS CODE>
    /*""")
    <DIVISION>
    <PYTHON CODE>
    """
    *///"""


### \> Edge-case handling (PY+JS)

Since we are inserting text into a template, it's crucial to consider edge cases.

If the Python code contains `*/`, it could prematurely close a JavaScript comment, breaking the template. Similarly, if 
the JavaScript code includes `"""`, it could unintentionally close a Python string, causing errors. These cases must be 
handled carefully to ensure the final output remains valid in both languages.

As far as I know, both problematic character sequences (`*/` in Python and `"""` in JavaScript) are syntactically invalid 
in the other language. However, they can still cause issues if they appear inside strings. While comments don’t matter, 
strings are crucial. For example, a Python-implemented JavaScript interpreter might require the `*/` sequence in its 
tokenizer to function correctly.

Fortunately, both languages support using hex codes inside strings. By replacing these sequences with their hex 
equivalents, we can avoid conflicts. The script in `main.py` handles this transformation automatically.

#### :: Replacement snippets
    python_code = python_code.replace("*/", "\\x2A/")
    [...]
    js_code = js_code.replace('"""', '\\x22\\x22\\x22')


-----

## Adding a third language (LUA)

### \> Initial assessment

Now that we are working with Lua in addition to Python and JavaScript, we need to rethink our approach to handling 
multi-language compatibility.

Lua supports both single-line comments (`--`) and multiple types of multi-line comments. While the simplest delimiter, 
`--[[`, might seem like a good choice, it closes at the first occurrence of `]]`, sequence which could appear naturally 
in both Python and JavaScript. Instead, we will use a safer delimiter: `--[===[` to open and `]===]` to close. The 
sequence `]===]` is invalid syntax in both Python and JavaScript, making it a reliable marker for separating 
Lua-specific sections.

Handling three languages simultaneously introduces new constraints. Some of the techniques we used before won’t work anymore.

  * Lua’s Strict Execution Rules

    * In Lua, every statement must either be a comment or perform some action.

      * We can’t rely on expressions that simply evaluate to numbers or strings.

    * Instead of using `1 -- 1 // len("""`, which would work in Python but fail in both Lua and JavaScript, we must modify it.

        * A valid Lua alternative is: `_ = 1 -- 1 // len("""`

    * Lua interprets `_ = 1` as a valid assignment and ignores everything after `--`.

  * JavaScript’s Handling of `--` ...

    * JavaScript does not have an operation for `<object> -- <object>`.

    * Its `--` is a unary decrement operator, just like in C/C++, meaning it reduces the value of a variable. However,
      this requires the variable to be defined beforehand.

* Python Handling of `--<variable>` is simple, as its equivalent to `-1*-1*<variable>`.


With these additional constraints, we need to refine our approach to ensure compatibility across all three languages.

### \> Solution description

All three languages accept `_ = 1` as valid syntax, allowing us to define a common variable that JavaScript can 
decrement without breaking Lua or Python compatibility. This does come with a trade-off—strongly typed languages or 
those requiring explicit variable declarations won’t work—but it’s a necessary compromise for multi-language 
compatibility.

Once `_` is defined, JavaScript can interpret `--_` as a valid decrement, while Lua treats `--_` as a comment. In 
Python, `--_` is simply `_` due to its handling of double negatives. To ensure this acts as a NOP, we use the same trick 
as in the Python-JavaScript solution: `--_ // len("""`. This makes the expression meaningful in Python while remaining 
a comment in JavaScript.

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

By combining these solutions, we can further reduce redundancy and minimize the overall footprint while maintaining 
compatibility across all three languages.

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

Since Lua also supports hex encoding inside strings, the solution follows the same approach we used for JavaScript and 
Python. We simply replace problematic sequences like `""""` and `*/` with their corresponding hex-encoded equivalents 
within strings.

The new edge case to address is the Lua delimiter used to end multiline comments, which is `]===]`. To prevent this from 
breaking our template, we can similarly replace some of those characters with their hex-encoded equivalents, ensuring 
compatibility across all three languages.

#### :: New replacement snippet
    python_code = python_code.replace(']===]', ']=\\x3D=]')
    [...]
    js_code = js_code.replace(']===]', ']=\\x3D=]')
    [...]
    lua_code = lua_code.replace('"""', '\\x22\\x22\\x22')
    lua_code = lua_code.replace("*/", "\\x2A/")

The issue with using the variable `_` across all three languages is that it might already be in use by the program, 
causing conflicts. To avoid this, we delete the variable before using it in each language:

  * In Python, we can use `del _` to remove the variable before it's used.

  * In Lua, we set `_ = nil` to delete the variable.

  * In JavaScript, we can use `delete _`, and to avoid issues with `const variables`, we place the code inside a block 
    `{}` to scope the variable deletion.

By taking these steps, we ensure the variable `_` doesn’t interfere with any existing code while maintaining the 
functionality of our solution across all languages.

-----

## Going beyond with a fourth language (Ruby)

### \> Introduction

This solution was significantly more challenging than the previous ones. Combining two languages was relatively 
straightforward, three languages required more thought, but adding a fourth language was a real puzzle. Despite the 
difficulties, it was worth pushing through to find a solution.

The risky part of this approach is that programming languages evolve over time. For instance, Python 3.10 removed some 
features that were options we no longer had. They serve as an example of the dangers of relying on this kind of hack-ish
solution. As a result, this answer is tied to the current versions of the interpreters (as of 22/3/2025), and it 
might break in the future. There's no guarantee that it will work indefinitely.

For this explanation, we'll take the reverse approach: starting with the final solution and then tracing our way back 
to see how we arrived there.

#### :: Final Solution 

    _=1
    __={}
    --_ * "#{#"  * 1 // 1 if False else """"
    --_ || //}".to_i
    --_ || `false && ${/*}`
    _=#__--[===[
    1
    _ = nil
    __ = nil
    <RUBY CODE>
    <<-ruby_long_string
    <DIVISION>
    """
    del _
    del __
    <PYTHON CODE>
    """
    <DIVISION>
    */1}`
    { delete _
    delete __
    <JS CODE> }
    `${/*
    <DIVISION>
    #]===]
    _=nil
    __=nil
    <LUA CODE>
    --[===[
    ruby_long_string
    #]===]
    --_ || `false && ${_*/1}`
    --_ || "#{#" ; 1 //
    _=--_ && //}"""
    1

### \> Understanding the new challenge

Ruby is a relatively straightforward language, similar to the previous three we've worked with. It also supports `_=1`, 
which is beneficial for us as it lets us reuse some of the tricks we've used before. Additionally, `--{variable}` 
behaves the same way in Ruby as it does in Python (i.e., `-1 * -1 * {variable}`), meaning this is another trick we can 
recycle.

However, some unique syntactical features in Ruby complicate things. In particular, `//` is used for defining regular 
expressions in Ruby, not for division or any other operation like in Python or JavaScript. While regular expressions can 
be defined with variable names in other languages (e.g., `//x` or `//i`), Ruby doesn't allow adding a value before the 
regex. This means that our Python+JavaScript technique of using `1 // 1` will only work inside Ruby comments and not in 
the code itself.

Comments and multiline strings in Ruby also present challenges. Single-line comments are marked with `#`, but JavaScript 
can't use `#` outside of a class context. Ruby’s multiline comments require the awkward `=begin`/`=end` syntax at the 
beginning and end of the block, which doesn’t easily match up with the other languages. Multiline strings in Ruby use 
the convention `<<-{variable}`, which is compatible with both Python and JavaScript if we add a character at the start 
like `1<<-{variable}`. (_A small spoiler: we won’t actually take advantage of this feature in the solution._)

Lastly, Ruby allows command-interpreted strings, where you can run system calls by enclosing them in backticks (` `` `). 
This feature is relevant because JavaScript also uses backticks for string manipulation. If the underlying system is 
BASH, this can lead to NOP (no-op) calls in Ruby by writing a command as `<x>` and treating it as a BASH comment 
(`#<x>`) or using shortcut logic like `false && <x>`.

### \> Key solution

The current solution we’ve devised relies on abusing **String-Interpolation** and their different implementations across 
languages. Since no two languages use the same token delimiters for String-Interpolation, opening string interpolation 
in one language allows us to write comment markers (such as `#` in Ruby or `/*` in JavaScript) that will be interpreted 
by the other language as part of a string, not as comments.

To make this work, we need to utilize two types of String-Interpolation: one in Ruby and the other in JavaScript. 
Additionally, we’ll employ a trick to mask a Ruby comment in Lua, ensuring the comment is ignored without breaking the 
functionality in either language. This combination of techniques lets us maintain compatibility across Ruby, JavaScript, 
and Lua without running into conflicts from comment markers or string delimiters.

#### :: Ruby interpolation



The idea with Ruby is fairly straightforward, as interpolation is done inside a regular string using the `"#{<value>}"` 
syntax. We simply add a comment token (`#`) inside the value to be evaluated:

    "#{# <IGNORED BY RUBY>
    <SOME VALUES>}"

Looking at some of our previous tricks, we can reuse `--_` and `1 // 1` to comment out Lua and start a Python comment. 
Since JavaScript does not treat `--_` as a comment, the second statement must also be valid in JavaScript. To achieve 
this, we can use the `||` operator before `//`.

 * In JavaScript, everything after `//` is treated as a comment. If we add any variable or value on the next line (such as
 `--_`), JavaScript interprets it as `--_ || --_`, which is valid syntax.


 * In Ruby, `//` is interpreted as a regex delimiter, making `--_ || //` legal. The next line, `--_`, is also valid and 
   acts as a no-op (NOP).

This leads us to the following snippet:

    _=1
    --_ ; "#{#" ; 1 // 1 and """
    --_ || //}"
    --_


The goal of this exploit is to construct a valid snippet that introduces triple quotes (`"""`) while avoiding multiline 
comments or strings in any of the four languages. From Python's perspective, the above code is interpreted as:

    _=1
    --_ ; "#{#" ; 1 // 1 and """
    <IGNORED BY PYTHON>
     """

Finally, we refine the approach by introducing multiplication and `to_i` to ensure Ruby treats values as numbers. Since 
Python would now face precedence issues, we replace `and` with `if False else`, completely eliminating the need for 
semicolons (`;`).

    _=1
    __={}
    --_ * "#{#"  * 1 // 1 if False else """"
    --_ || //}".to_i
    --_

#### :: Javascript interpolation

One particular hurdle to overcome was that JavaScript performs string interpolation inside backticks (` `` `), which 
cannot be used in Python or Lua and are interpreted as a system call in Ruby. However, we can address these issues as 
follows:

  * To handle Python and Lua, we ensure that the backtick expression is only evaluated after both languages already 
    treat the code as a comment or string.


  * To prevent Ruby from interpreting backticks as a system call that does something, we force the operation to be a 
    no-op in Bash using `false && <x>`.

This results in the following snippet:

    `false && ${/* <IGNORED BY JS>
    <IGNORED BY JS>
    `false && ${_*/<SOME VALUE>}`

Next, we incorporate our previous techniques to make this exploit Lua-compatible using `--_`. Since we cannot fully 
adapt it to Python syntax at this stage, we will defer using this until we reach the point where Python treats the code 
as a string. The final result is similar to the previous example:

    _=1
    --_ ; `false && ${/*}`
    <IGNORED BY JS>
    --_; `false && ${_*/1}`


#### :: > Masking Ruby in LUA

With the previous two sections, we have successfully placed ourselves in no-operation (NOP) sections for both Python and
JavaScript. We can easily use a single-line comment in Lua that is also valid in Ruby (`--_`), but starting a multi-line 
comment is more challenging.

Lua requires `--[===[` to begin a multi-line comment, while Ruby uses `=begin`. However, as we will explore in future 
sections, `=begin` and its corresponding `=end` token introduce edge cases that we would rather avoid. Instead, Ruby 
also allows multi-line strings using `<<-{variable}`, but this approach presents its own challenges. Specifically, the 
`{variable}` sequence cannot appear in any of the other targeted languages. The solution to this will be discussed 
further in later sections.    

    <<-{x}
    <IGNORED BY RUBY AS LONG AS IT DOESN'T CONTAIN {x}>
    {x}

Returning to Ruby-Lua integration, we can start a single-line comment in Ruby using #. If we can embed this within valid 
Lua syntax, we can append `--[===[` at the end to initiate a multi-line Lua comment. Fortunately, `#` is a valid symbol 
in Lua, where it serves as the length operator for tables.

Since all target languages accept the definition of `__={}`, we can use `#__` in Lua without issue. However, because 
Ruby will treat `#__` as an incomplete expression, we must include additional content below to maintain valid syntax.

    _=1
    __={}
    _=#__--[===[
    1
    <CODE IGNORED BY LUA>
    #]===]

### \> Multi-line string/comment for Ruby

In our current template, Ruby is the most deeply zipped language, meaning we have the freedom to use any tool the 
language provides. However, due to Ruby’s multiline comments and string limitations, our options are surprisingly 
constrained. Each approach introduces its own set of drawbacks, potentially leading to compatibility issues.

One option we can immediately discard is using Ruby’s `%q()` for multiline strings:

    _ = %q( <a multiline string> )

This is outright unusable for us because it prohibits the use of `)` in any of our other target languages. While it is 
theoretically possible to work around this, doing so would be an unnecessarily complex task with no real benefit. With 
this in mind, we can explore the two remaining options.

#### :: Option 1: Using '=being/=end' Option
    =being
    <This is a multine comment and will be ignored>
    =end

This approach is more viable than `%q()`, but it still has significant issues. The main problem is that `=end` cannot 
appear in any of our other target languages, creating an artificial constraint. Some variable names may start with 
`end`, meaning we'd need to adjust their names whenever they appear in the code.

Additionally, `=end` may appear inside strings or regex patterns, making it difficult to determine where modifications 
should be applied. This is further complicated by Lua, where `end` is a reserved keyword. Since we cannot simply replace
all occurrences of end, we would have to analyze the syntax carefully.

Example of problematic cases:

    endymion = 12
    after_endymion = endymion + 1

    current_position = 1
    while current_position !== after_endymion:
        print(" ==end of the game can only be reached after surpassing endymion== ")
        keep_going()

Handling this issue properly would require using Abstract Syntax Trees (ASTs) for most languages, which is something 
we’d like to avoid in this tool. As such, we should look for a better alternative.

#### :: Option 2: Multiline String with unusual variable name Option
    _ = <<-UNUSUAL_VARIABLE_NAME
    <This is a multine string and will be ignored>
    UNUSUAL_VARIABLE_NAME

This option is similar to using `=end` but slightly better. Not only does it make it more explicit that we need to 
handle cases where the variable does not start with `=`, but it also allows us to choose a specific string to avoid 
unwanted collisions—such as the end conflict in Lua.

  * If the string appears in other languages as part of a string literal, we can replace it with hex codes, similar to 
    how we solved other edge cases. This prevents unintended collisions.


  * If the string appears as a variable name, we can simply rename it to something else that is not already present in 
    the code. We can continue iterating until we find a unique name.

Determining which variables need renaming is straightforward: we introduce a breaking change and check if the syntax 
remains valid. For example, replacing `test1` with `+t-7est1*`:

  *  If the syntax remains valid, the original value was inside a string or regex and does not require modification.


  *  If the syntax breaks, then it was a variable and should be renamed.

Ultimately, we chose `ruby_long_string` as our identifier, as it is unlikely to be repeated in other languages. Using a 
simple replacement function on the sources to ensure its uniqueness:

  *  Variables containing `ruby_long_string` are renamed to `r_uby_long_string`.


  *  If `r_uby_long_string` already exists, we append `x`s (e.g., `r_uby_long_stringx`, `r_uby_long_stringxx`) until we 
     find a unique name.

This method ensures compatibility while minimizing unnecessary complexity and conflicts across different languages.

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

However, handling edge cases in Ruby is more challenging due to the presence of five different structures:

* Double-quoted Strings
* Single-quoted strings
* Regexes
* Comments
* Terminal Calls

Comments and terminal calls can largely be ignored since they do not pose a problem for us. Regexes, on the other hand, 
will be partially ignored due to their complexity. Handling them properly without an Abstract Syntax Tree (AST) is 
nearly impossible. However, even when focusing solely on strings, we still encounter significant issues.

The main challenge arises from the fact that double-quoted and single-quoted strings behave differently. While we can 
reuse our hex-encoding trick for double-quoted strings (and terminal calls), this method does not work for single-quoted 
strings. As a result, we need to address both cases separately.

One particularly problematic case is that Ruby automatically appends adjacent strings. For example, `""""` (which is a 
superset of Python’s `"""`) is valid Ruby syntax. Fixing this behavior depends on whether the issue occurs inside a 
single-quoted string, inside a terminal call, or as two consecutive strings.

Our approach is as follows:

  * 1/ Detect consecutive strings.
    *  We use the same replace-then-validate trick from the previous section.
    *  If two consecutive strings are found (`"<content>""<empty>"` or `"<empty>""<content>"`), we merge them into a 
       single string (`"content"`).
    
       This process repeats until no more consecutive strings are found.
  * 2/ Handle single-quoted strings.
    * Since single quotes can be appended, we convert `'""""'` into the equivalent `'"'+'"'+'"'`.
  * 3/ Apply hex encoding.
    * For multi-line comments and terminal calls, we encode the three consecutive quotes (`"""`) using hex codes.


For `]===]` and `*/`, we apply a technique similar to the one used for `"""`:

   * Single strings are split into two separate parts.

   * Other cases are hex-encoded to avoid conflicts.

Last but not least, Regexes introduce an additional challenge with `*/`. Since regexes do not support hex replacements 
for special characters, and ending a regex with `*/` is fairly common, we take a different approach:

  * Instead of `*/`, we replace it with `{0,}/`.

  * This maintains syntactical correctness, ensuring that the regex still behaves as expected.

However, this does alter string comparison behavior, meaning two seemingly identical regexes may not evaluate as 
equal. This final case was deemed rare enough that we considered it an acceptable compromise.



------

## TODO

* Improve the test engine. (migrate it to PyTest)


* Add a 5th language if feeling brave enough.
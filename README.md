# Kola
Simple python module for KoiLang parsing.

[![License](https://img.shields.io/github/license/Ovizro/Kola.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/KoiLang.svg)](https://pypi.python.org/pypi/KoiLang)
![Python Version](https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8%20|%203.9%20|%203.10-blue.svg)

## Installation
From pip:

    pip install KoiLang

From source code:
    
    python setup.py build_ext --inplace
    python setup.py install

## What is KoiLang

KoiLang is a markup language while is easy to read for people.
There is an simple example.
```
#background Street
    #camera on(Orga)
    #character Orga
        Huh... I'm a pretty good shot, huh?
    #camera on(Ride, Ched)
    #character Ride
        B- boss...
    #character Orga
        #action bleed
    #camera on(object: blood, source: Orga)

    #camera on(Ched, Orga, Ride)
    #character Orga
        How come you're stammering like that... Ride!

    #playsound freesia

    #character Orga
        #action stand_up speed(slowly)

    #character Ride
        But... but!
    #character Orga
        I'm the Boss of Tekkadan, Orga Itsuka, this is nothing to me.
    #character Ride
        #action shed_tear
        No... not for me...

    #camera on(Orga)
    #character Orga
        Protecting my members is my job!
    #character Ched
        #action shed_tear

    #character Ride
        But...!
    #character Orga
        Shut up and let's go!

        #camera on(Orga)
        #action walk direction(front) speed(slowly)
        Everyone's waiting, besides...

        I finally understand now, Mika, we don't need any destinations, we just need to keep moving forward.
        As long as we don't stop, the road will continue!
```
    
In KoiLang, file is divided into 'command' part and 'text' part.
The formation of command part is like C preprocessor directive,
using '#' as starting. And text is surrounding commands.

    #command "This is a command"
    This is a text.

Each command can have several arguments behind the command name.
Valid argument type include integer, float, literal and string.
    
    #arg_int    1 0b101 0x6CF
    #arg_float  1.0 2e-2
    #arg_literal __name__
    #arg_string "A string"

> Here "literal" is a valid python variety name containing letter,digit, underline and not starting with digit. Usually it is same as a string.
 
There is another kind of arguments -- keyword arguments which formation is as this:

    #kwargs key(value)
    
    And another format:
    #keyargs_list key(item0, item1)
    
    And the third:
    #kwargs_dict key(x: 11, y: 45, z: 14)

All the arguments can be put together
    
    #draw Line 2 pos0(x: 0, y: 0) pos1(x: 16, y: 16) \
        thickness(2) color(255, 255, 255)

## What can Kola module do

Kola module provides a fast way to translate KoiLang command
into a python function call.

Above command `#draw` will convert to function call below:

```py
draw(
    "Line", 2,
    pos0={"x": 0, "y": 0},
    pos1={"x": 16, "y": 16},
    thickness=2,
    color=[255, 255, 255]
)
```

Kola mudule just create a bridge from kola file to Python script. The bridge, the main class of Kola module, is `KoiLang` class. There is a simple example.

### Example

Let's image a simple situation, where you want to create some small files. Manual creating is complex and time-consuming. Here is a way to solve that. We can use a single kola file to write all my text. Then use commands to devide these text in to different files.

```
#file "hello.txt" encoding("utf-8")
Hello world!
And there are all my friends.

#space hello

    #file "Bob.txt"
    Hello Bob.

    #file "Alice.txt"
    Hello Alice.

#endspace
```

Then, we make a script to explain how to do with these commands:

```py
import os
from kola import KoiLang, kola_command, kola_text, kola_env


class MultiFileManager(KoiLang):
    @kola_command
    def file(self, path: str, encoding: str = "utf-8") -> None:
        if self._file:
            self._file.close()
        path_dir = os.path.dirname(path)
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)
        self._file = open(path, "w", encoding=encoding)
    
    @kola_command
    def end(self) -> None:
        if self._file:
            self._file.close()
            self._file = None
    
    @kola_text
    def text(self, text: str) -> None:
        if not self._file:
            raise OSError("write texts before the file open")
        self._file.write(text)
    
    def at_start(self) -> None:
        self._file = None
    
    def at_end(self) -> None:
        self.end()
```

And mix them together, just input this in terminal:

> Here we assume the two files above is `kolafile.kola` and `script.py`

```
python -m kola kolafile.kola -s script.py
```

Or directly add in script:
```py
if __name__ = "__main__":
    MultiFileManager().parse_file("kolafile.kola")
```

You will see new files in your work dir.

    <workdir>
    │      
    │  hello.txt
    │      
    └─hello
        Alice.txt
        Bob.txt

### What happened

It seems amusing? Well, if you make a python script as this:

```py
vmobj = MultiFileManager()

vmobj.at_start() # begin parsing
vmobj.file("hello.txt", encoding="utf-8")
vmobj.text("Hello world!")
vmobj.text("And there are all my friends.")

vmobj.space("hello")

vmobj.file("Bob.txt")
vmobj.text("Hello Bob.")

vmobj.file("Alice.txt")
vmobj.text("Hello Alice.")

vmobj.endspace()
vmobj.at_end() # end parsing
```
the same result will be get. This is the python script corresponding to the previous kola file. What we have done is to make KoiLang interpreter know the correspondence between kola commands and python functions.

So let's go back to the script. Here the first we need is a kola command set class. All commands we want to use will be included in the class. The best way is create a subclass of `KoiLang`. That is:
```py
from kola import KoiLang

class MultiFileManager(KoiLang):
    ...
```
The next step is making an exact kola command. So a function is defined:
```py
def space(self, name: str) -> None:
    path = name.replace('.', '/')
    if not os.path.isdir(path):
        os.makedirs(path)
    os.chdir(path)
```
But it is not enough. Use the decorator `@kola_command` to annotate the function can be used in kola files. In default case, the name of kola command will be the same to that of the function's. If another name is expected to use in kola files instead of the raw function name, you can use `@kola_command("new_name")` as the decorator. It wiil look like:
```py
@kola_command("create_space")
def space(self, name: str) -> None:
    ...
```
Than `#create_space hello` will be a new valid command, while using `#space hello` would get a `KoiLangCommandError`.

You may have notice that there is a special decorator `@kola_text`. As we know, the text in kola files is a command, too. This decorator is to annotate the function to use to handle texts. Using `@kola_command("@text")` has the same effect. And another special decorator which is not shown here is `@kola_number`. It can handle commands like `#114` or `#1919`. The first argument wiil be the number in the command.

### File parse
`KoiLang` class provides several method. Use `parse` method to parse a string and `parse_file` to parse a file. It is suggested to use the second way so that KoiLang interpreter can give a traceback to the file when an error occure.

### Advanced techniques
In above example, we define two commands to create and leave the space. While, if users use `#endspace` before creating space, this can cause some problems. To correct user behavior, we can use the environment to restrict the use of some commands. `@kola_env` decorator can be used to define a environment:

```py
@kola_env
def space(self, name: str) -> None:
    ...
```

And register the function `endspace` as the exit command of environment `space`:

```py
@space.exit_command
def endspace(self) -> None:
    ...
```

And other commands wanted to use in the `space` environment can be defined as:

```py
@space.env_command
def foo(self, *args, *kwds) -> Any:
    ...
```

> There is a argument in `@kola_command` `envs`, which is also used to limit command uses. But those is not same. `envs` argument means the top stack of environment must have the same name, while `@env.env_command` means the commands can be used until the environment is pop from the stack, even though the stack top is other environment.

## What is more

The most difference between KoiLang and other markup language like YAML which is data-centric is that KoiLang more pay attention to the command. Yeah, text in Kola file is a special command named `@text` too. In fact, the core idea of Kola is to separate data and instructions. The kola file is the data to execute commands, and the python script is the instructions. Then Kola module just mix they together. It can be considered as a simple virtual machine engine. if you want, you can even build a Python virtual machine (of course, I guess no one like to do that).

On the other hand, text is also an important feature of Kola, which is a separate part, independent of context during parsing. The text is the soul of a Kola file. Any commands just are used to tell the computer what to do with the text. Though you can make a Kola file with only commands, it is not recommended. Instead, you ought to consider switching to another language.

## Bugs/Requests

Please send bug reports and feature requests through [github issue tracker](https://github.com/Ovizro/Kola/issues). Kola is open to any constructive suggestions.
# Kola
Simple python module for KoiLang parsing.

[![License](https://img.shields.io/github/license/Ovizro/Kola.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/KoiLang.svg)](https://pypi.python.org/pypi/KoiLang)
![Python Version](https://img.shields.io/badge/python-3.6|3.7|3.8|3.9|3.10-blue.svg)

## Installation
From pip:

    pip install KoiLang

From source code:
    
    python setup.py build_ext --inplace
    python setup.py install

## What is KoiLang

KoiLang is a markup language while is easy to read for people.
There is an simple example.

    #hello KoiLang
    I am glad to meet you!
    
    
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

> Here "literal" is a valid python variety name containing letter,
 digit, underline and not starting with digit. Usually it is same as a string.
 
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

Kola module provides a fast way to convert KoiLang command
to a python function call.

Above command `#draw` will convert to calling below:

```py
draw(
    "Line", 2,
    pos0={"x": 0, "y": 0},
    pos1={"x": 16, "y": 16},
    thickness=2,
    color=[255, 255, 255]
)
```


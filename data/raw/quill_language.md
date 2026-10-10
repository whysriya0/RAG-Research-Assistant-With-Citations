# The Quill Programming Language

## Overview

Quill is a small scripting language designed for teaching. It was created by Ines Marchetti and first released in 2011. The language uses indentation to mark blocks and has only fourteen keywords.

## Design goals

Marchetti wanted beginners to read code almost like plain English. For that reason, Quill uses the word "say" to print output and "ask" to read input. Variables are declared with the keyword "hold". Error messages are written as full sentences that suggest a fix.

## Types and memory

Quill has four built-in types: number, text, list and flag. All values are checked when the program runs, not before. Memory is managed by reference counting, so a value is freed as soon as nothing uses it.

## Tooling

The standard interpreter is called quillrun. A web playground lets students run code without installing anything. Version 3.0, released in 2019, added a debugger that lets learners step through a program one line at a time.

## Limitations

Quill is slow compared with most languages because it has no compiler. For this reason it is rarely used outside classrooms.

from cpython cimport PyUnicode_FromFormat
from ._helper cimport *
from .lexer cimport Token, BaseLexer


cdef class Parser:
    cdef:
        Token t_cache
        Token stack_top
        uint8_t stat
    cdef readonly:
        BaseLexer lexer
        object command_set

    cpdef void push(self, Token n)
    cpdef Token pop(self)
    cdef void set_error(self, int errorno = *) except *
    cpdef object exec_once(self)
    cpdef void exec_(self) except *
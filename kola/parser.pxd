from ._cutil cimport *
from .lexer cimport Token, BaseLexer


cdef extern from *:
    str PyUnicode_FromFormat(const char*, ...)


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
    cdef void recovery(self)
    cdef void set_error(self, int errorno = *, bint recovery = *) except *
    cpdef tuple parse_args(self)
    cpdef object exec_once(self)
    cpdef void exec(self) except *
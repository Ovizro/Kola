cimport cython
from libc.stdio cimport stdin, FILE, fopen, fclose, EOF
from cpython cimport PyObject

from ._cutil cimport *


cdef extern from *:
    bint PyDescr_IsData(object desc)


cdef class Token:
    cdef:
        Token next     # used in grammar parser
    cdef readonly:
        TokenSyn syn
        object val
        bytes raw_val
        int lineno
    
    cpdef int get_flag(self)


cdef class LexerConfig:
    cdef LexerData* lexer_data
    cdef readonly BaseLexer lexer


@cython.no_gc
cdef class BaseLexer:
    cdef:
        yyscan_t scanner
        LexerData lexer_data
    cdef readonly:
        str encoding

    cpdef void close(self)
    cdef void set_error(self, const char* text) except *
    cdef (int, const char*, Py_ssize_t) next_syn(self) nogil
    cdef Token next_token(self)


cdef class FileLexer(BaseLexer):
    cdef:
        object _filenameo
        bytes _filenameb
        FILE* fp
    
    cpdef void close(self)


@cython.no_gc
cdef class StringLexer(BaseLexer):
    cdef readonly bytes content
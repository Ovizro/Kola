from libc.stdio cimport stdin, FILE, fopen, fclose
from libc.string cimport strchr
from cpython cimport PyObject, PyLong_FromString, PyFloat_FromString, PyUnicode_FromStringAndSize, \
    PyUnicode_FromFormat, PyBytes_FromStringAndSize, PyErr_Format, PY_MINOR_VERSION

from ._helper cimport *
from ._lexer cimport *


cdef class Token:
    cdef Token next     # used in grammar parser
    cdef readonly:
        TokenSyn syn
        object val
        bytes raw_val
        int lineno
    
    cpdef int get_flag(self)
    

cdef class BaseLexer:
    cdef:
        char* _filename
        YY_BUFFER_STATE buffer
    cdef readonly int lineno

    cpdef void ensure(self)
    cpdef void close(self)
    cdef void set_error(self) except *
    cdef Token next_token(self)


cdef class FileLexer(BaseLexer):
    cdef:
        bytes _filenameo
        FILE* fp
    
    cpdef void close(self)


cdef class StringLexer(BaseLexer):
    cdef readonly bytes content
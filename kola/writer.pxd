from libc.stdio cimport FILE
from libc.stdint cimport uint8_t
from ._cutil cimport *


cdef class BaseWriterItem(object):
    cpdef void __kola_write__(self, BaseWriter writer) except *


cdef class FormatItem(BaseWriterItem):
    cdef readonly:
        object value
        str spec
    cpdef void __kola_write__(self, BaseWriter writer) except *


cdef class ComplexItem(BaseWriterItem):
    cdef readonly:
        str name
        object value
    

cdef class BaseWriter:
    cdef Py_ssize_t cur_indent
    cdef readonly uint8_t indent

    cpdef void raw_write(self, str text) except *
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = *) except *
    cdef void raw_write_char(self, char ch) except *
    cpdef void close(self)
    cpdef void inc_indent(self)
    cpdef void dec_indent(self) except *
    cpdef void write_indent(self) except *
    cpdef void newline(self, bint concat_prev = *) except *


cdef class FileWriter(BaseWriter):
    cdef FILE* fp
    cdef readonly:
        object path
        str encoding
    cpdef void close(self)
    cpdef void raw_write(self, str text) except *
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = *) except *
    cdef void raw_write_char(self, char ch) except *

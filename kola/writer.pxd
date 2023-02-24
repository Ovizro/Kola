from libc.stdio cimport FILE
from libc.stdint cimport uint8_t
from ._cutil cimport *


cdef enum ItemLevel:
    BASE_ITEM
    COMPLEX_ITEM
    ARG_ITEM
    FULL_CMD


cdef class BaseWriterItem(object):
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *


cdef class FormatItem(BaseWriterItem):
    cdef readonly:
        object value
        str spec
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *


cdef class ComplexArg(BaseWriterItem):
    cdef readonly:
        str name
        object value
        bint split_line
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *


cdef class NewlineItem(BaseWriterItem):
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *


cdef NewlineItem i_newline


cdef class BaseWriter:
    cdef Py_ssize_t cur_indent
    cdef readonly:
        uint8_t indent
        int command_threshold
    cdef public bint line_beginning

    cpdef void raw_write(self, str text) except *
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = *) except *
    cdef void raw_write_char(self, char ch) except *
    cpdef void close(self)
    cpdef void inc_indent(self)
    cpdef void dec_indent(self) except *
    cdef void _write_indent(self) except *
    cdef void _write_prefix(self, Py_ssize_t length) except *
    cpdef void newline(self, bint concat_prev = *) except *
    cpdef void prepare(self) except *
    cdef void _write_text(self, str text) except *


cdef class FileWriter(BaseWriter):
    cdef FILE* fp
    cdef readonly:
        object path
        str encoding
    cpdef void close(self)
    cpdef void prepare(self) except *
    cpdef void raw_write(self, str text) except *
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = *) except *
    cdef void raw_write_char(self, char ch) except *


cdef class StringWriter(BaseWriter):
    cdef:
        bint _closed
        _PyUnicodeWriter writer
    
    cpdef void close(self)
    cpdef void prepare(self) except *
    cpdef void raw_write(self, str text) except *
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = *) except *
    cdef void raw_write_char(self, char ch) except *
    cpdef str getvalue(self)

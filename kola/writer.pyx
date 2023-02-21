from libc.stdio cimport fopen, fclose, fputc, fputs, sprintf
from libc.string cimport strlen
from cpython cimport PyObject, PySequence_Check, PyMapping_Check, PyErr_Format, PyErr_SetString,\
    PyUnicode_FindChar, PyUnicode_FromStringAndSize, PyUnicode_AsEncodedString

import re
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class WriterItemLike(Protocol):
    def __kola_write__(self, __writer: BaseWriter, __level: int) -> None:
        pass


cdef extern from *:
    """
    #define _MAX_STRING_CACHE 8
    static const char* _indent_string = "        ";
    static const char* _prefix_string = "########";
    """
    Py_ssize_t _MAX_STRING_CACHE
    const char* _indent_string
    const char* _prefix_string


cdef object literal_pattarn = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


cdef inline void _write_writeritemlike(BaseWriter writer, object obj, ItemLevel level) except *:
    if isinstance(obj, BaseWriterItem):
        (<BaseWriterItem>obj).__kola_write__(writer, level)
        return

    cdef PyObject* kw_method = _PyType_Lookup(type(obj), "__kola_write__")
    if kw_method == NULL:
        PyErr_Format(TypeError, "unsupport type '%s'", get_type_qualname(obj))
    (<object>kw_method)(obj, writer, level)

cdef bint _write_base_item(BaseWriter writer, object value) except -1:
    cdef str lt
    if isinstance(value, str):
        if literal_pattarn.match(value) is None:
            lt = <str>repr(<str>value)
            PyUnicode_WriteChar(lt, 0, ord('"'))
            PyUnicode_WriteChar(lt, len(lt) - 1, ord('"'))
        else:
            lt = <str>value
        writer.raw_write(lt)
    elif isinstance(value, bytes):
        writer.raw_write_string(<const char*>(<bytes>value), len(<bytes>value))
    elif isinstance(value, (int, float)):
        writer.raw_write(str(value))
    else:
        return False
    return True

cdef inline void _write_base_item_wrapped(BaseWriter writer, object value) except *:
    if not _write_base_item(writer, value):
        _write_writeritemlike(writer, value, BASE_ITEM)

cdef void _write_complex_item(BaseWriter writer, str key, object value, bint split_line = False) except *:
    cdef bint is_first = True
    writer.raw_write(key)
    writer.raw_write_char(ord('('))
    if split_line:
        writer.inc_indent()
        writer.newline(True)
    try:
        if not _write_base_item(writer, value):
            if isinstance(value, list):
                if not value:
                    raise ValueError("empty list is not a valid kola item")
                _write_base_item_wrapped(writer, (<list>value)[0])
                for i in range(1, len(<list>value)):
                    writer.raw_write_string(", ", 2)
                    if split_line:
                        writer.newline(True)
                    _write_base_item_wrapped(writer, (<list>value)[i])
            elif isinstance(value, dict):
                if not value:
                    raise ValueError("empty dict is not a valid kola item")
                for k, v in (<dict>value).items():
                    if not is_first:
                        writer.raw_write_string(", ", 2)
                        if split_line:
                            writer.newline(True)
                    else:
                        is_first = False
                    _write_base_item_wrapped(writer, k)
                    writer.raw_write_string(": ", 2)
                    _write_base_item_wrapped(writer, v)
            else:
                _write_writeritemlike(writer, value, COMPLEX_ITEM)
    finally:
        if split_line:
            writer.dec_indent()
            writer.newline(True)
    writer.raw_write_char(ord(')'))
    writer.line_beginning = False


cdef class BaseWriterItem(object):
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *:
        raise NotImplementedError
    
    def __repr__(self):
        return PyUnicode_FromFormat("<kola writer item at %p>", <void*>self)


cdef class FormatItem(BaseWriterItem):
    def __init__(self, value, str spec not None):
        self.value = value
        self.spec = spec
    
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *:
        if level == FULL_CMD:
            raise ValueError("format item cannot be usec as a full command")
        writer.raw_write(format(self.value, self.spec))


cdef class ComplexArg(BaseWriterItem):
    def __init__(self, str name not None, value, *, bint split_line = False):
        if not (isinstance(value, (str, int, float)) or PySequence_Check(value) or PyMapping_Check(value)):
            PyErr_Format(TypeError, "unsupport type '%s'", get_type_qualname(value))
        if literal_pattarn.match(name) is None:
            PyErr_Format(ValueError, "'%U' is not a valid item name", <PyObject*>name)
        self.name = name
        self.value = value
        self.split_line = split_line
        
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *:
        if level != ARG_ITEM:
            raise ValueError("complex argument should only be used in argument level")
        _write_complex_item(writer, self.name, self.value, self.split_line)


cdef class NewlineItem(BaseWriterItem):
    cpdef void __kola_write__(self, BaseWriter writer, ItemLevel level) except *:
        if level == FULL_CMD:
            writer.newline()
        else:
            writer.newline(True)


WF_BASE_ITEM = BASE_ITEM
WF_COMPLEX_ITEM = COMPLEX_ITEM
WF_ARG_ITEM = ARG_ITEM
WF_FULL_CMD = FULL_CMD

WI_NEWLINE = i_newline = NewlineItem()
    

cdef class BaseWriter(object):
    def __cinit__(self, *args, uint8_t indent = 4, int command_threshold = 1, **kwds):
        self.indent = indent
        self.cur_indent = 0
        if command_threshold <= 0:
            PyErr_Format(
                ValueError,
                "the command threshold should be an positive number, not %d",
                command_threshold
            )
        self.command_threshold = command_threshold
        self.line_beginning = True
    
    def __init__(self, indent = None, command_threshold = None):
        if type(self) is BaseWriter:
            raise NotImplementedError
    
    def __dealloc__(self):
        self.close()
    
    cpdef void raw_write(self, str text) except *:
        raise NotImplementedError
    
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = -1) except *:
        if length < 0:
            length = <Py_ssize_t>strlen(string)
        self.raw_write(PyUnicode_FromStringAndSize(string, length))
    
    cdef void raw_write_char(self, char ch) except *:
        cdef char cstring[2]
        cstring[0] = ch
        cstring[1] = 0
        self.raw_write_string(cstring, 1)
    
    cpdef void close(self):
        pass
    
    cpdef void inc_indent(self):
        self.cur_indent += self.indent
    
    cpdef void dec_indent(self) except *:
        if self.cur_indent < self.indent:
            raise ValueError("writer indentation should be less than 0")
        self.cur_indent -= self.indent
    
    cdef void _write_indent(self) except *:
        cdef Py_ssize_t i = self.cur_indent
        while i > _MAX_STRING_CACHE:
            self.raw_write_string(_indent_string, _MAX_STRING_CACHE)
            i -= _MAX_STRING_CACHE
        self.raw_write_string(_indent_string + _MAX_STRING_CACHE - i, i)
    
    cdef void _write_prefix(self, Py_ssize_t length) except *:
        cdef Py_ssize_t i = length
        while i > _MAX_STRING_CACHE:
            self.raw_write_string(_prefix_string, _MAX_STRING_CACHE)
            i -= _MAX_STRING_CACHE
        self.raw_write_string(_prefix_string + _MAX_STRING_CACHE - i, i)
    
    cpdef void newline(self, bint concat_prev = False) except *:
        if concat_prev:
            self.raw_write_string("\\\n", 2)
        else:
            self.raw_write_string("\n", 1)
        self._write_indent()
        self.line_beginning = True
    
    cdef void _write_text(self, str text) except *:
        text = text.replace('\n', '\\\n')
        self.raw_write(text)
        self.newline()
    
    def write_text(self, str text not None):
        cdef Py_ssize_t i = 0
        while i < len(text) and PyUnicode_READ_CHAR(text, i) == ord('#'):
            i += 1
        if i >= self.command_threshold:
            PyErr_Format(ValueError, "kola text cannot have '#' prefix longer than %d", self.command_threshold)
        self._write_text(text)
    
    def write_command(self, __name not None, *args, **kwds):
        cdef:
            int number_name
            char cache[11]
        if isinstance(__name, str):
            if literal_pattarn.match(__name) is None:
                PyErr_Format(ValueError, "%U is an invalid command name", <PyObject*>__name)
            self._write_prefix(self.command_threshold)
            self.raw_write(__name)
        elif isinstance(__name, int):
            number_name = <int>__name
            if number_name < 0:
                raise ValueError("the numeric command should be a non-negative integer")
            self._write_prefix(self.command_threshold)
            sprintf(cache, "%d", number_name)
            self.raw_write_string(cache)
        else:
            PyErr_Format(
                TypeError,
                "argumnet '__name' must be a str or an integer, not '%s'",
                get_type_qualname(__name)
            )

        self.line_beginning = False
        self.inc_indent()
        try:
            for i in args:
                if not self.line_beginning:
                    self.raw_write_char(ord(' '))
                else:
                    self.line_beginning = False
                if not _write_base_item(self, i):
                    _write_writeritemlike(self, i, ARG_ITEM)

            for k, v in kwds.items():
                if not self.line_beginning:
                    self.raw_write_char(ord(' '))
                else:
                    self.line_beginning = False
                _write_complex_item(self, k, v)
        finally:
            self.dec_indent()
        self.newline()
    
    def write_annotation(self, str annotation not None):
        self._write_prefix(self.command_threshold + 1)
        self._write_text(annotation)
    
    def write(self, command not None):
        if isinstance(command, str):
            self._write_text(command)
        else:
            _write_writeritemlike(self, command, FULL_CMD)

    @property
    def closed(self):
        return False

    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def __repr__(self):
        cdef const char* format = "<kola writer object closed at %p>" if self.closed else "<kola writer object at %p>"
        return PyUnicode_FromFormat(format, <PyObject*>self)
    

cdef class FileWriter(BaseWriter):
    def __cinit__(
        self,
        __path,
        *args,
        str encoding = "utf-8",
        **kwds
    ):
        self.path = __path
        self.fp = kola_open(__path, NULL, 'w')
        if encoding is None:
            self.encoding = "utf-8"
        else:
            self.encoding = encoding
    
    def __init__(self, __path, encoding = "utf-8", indent = None, command_threshold = None):
        pass
    
    cpdef void raw_write(self, str text) except *:
        cdef:
            const char* encoding = unicode2string(self.encoding, NULL)
            bytes tb = PyUnicode_AsEncodedString(text, encoding, NULL)
        self.raw_write_string(tb)
    
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = -1) except *:
        if self.fp == NULL:
            raise OSError("operation on closed writer")
        with nogil:
            fputs(string, self.fp)

    cdef void raw_write_char(self, char ch) except *:
        if self.fp == NULL:
            raise OSError("operation on closed writer")
        with nogil:
            fputc(ch, self.fp)
    
    cpdef void close(self):
        if self.fp != NULL:
            with nogil:
                fclose(self.fp)
        self.fp = NULL
    
    @property
    def closed(self):
        return self.fp == NULL


cdef class StringWriter(BaseWriter):
    def __cinit__(self, *args, **kwds):
        _PyUnicodeWriter_Init(&self.writer)
        self.writer.overallocate = True
    
    cpdef void raw_write(self, str text) except *:
        if self._closed:
            raise OSError("operation on closed writer")
        _PyUnicodeWriter_WriteStr(&self.writer, text)
    
    cdef void raw_write_string(self, const char* string, Py_ssize_t length = -1) except *:
        if self._closed:
            raise OSError("operation on closed writer")
        if length < 0:
            length = <Py_ssize_t>strlen(string)
        _PyUnicodeWriter_WriteASCIIString(&self.writer, string, length)
    
    cdef void raw_write_char(self, char ch) except *:
        if self._closed:
            raise OSError("operation on closed writer")
        _PyUnicodeWriter_WriteChar(&self.writer, ch)
    
    cpdef void close(self):
        self._closed = True
        _PyUnicodeWriter_Dealloc(&self.writer)
    
    cpdef str getvalue(self):
        if self._closed:
            raise OSError("operation on closed writer")
        cdef str intermediate = _PyUnicodeWriter_Finish(&self.writer)
        self._closed = True

        _PyUnicodeWriter_Init(&self.writer)
        self.writer.overallocate = True
        _PyUnicodeWriter_WriteStr(&self.writer, intermediate)
        self._closed = False
        return intermediate
    
    @property
    def closed(self):
        return self._closed

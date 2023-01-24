from libc.string cimport strlen
from cpython cimport Py_BuildValue, PyUnicode_FSConverter, PyErr_Format, PyErr_SetString, PyUnicode_AsEncodedString


KLW_NEWLINE = '\n'


cdef class KoiLangWriter:
    def __cinit__(
        self,
        __path,
        str encoding not None = "utf-8",
        uint8_t indent = 4
    ):
        self.path = path
        self.encoding = encoding
        self.indent = indent
        self.cur_indent = 0
        self.fp = NULL
    
    def __dealloc__(self):
        if self.fp != NULL:
            fclose(self.fp)
    
    cpdef void open(self) except *:
        path = PyOS_FSPath(__path)
        cdef bytes p = <bytes>path if isinstance(path, bytes) else PyUnicode_EncodeFSDefault(path)
        self.fp = fopen(p, "w")
        if self.fp == NULL:
            PyErr_Format(OSError, "fail to open '%s'", self._filename)
    
    cpdef void close(self):
        fclose(self.fp)
        self.fp = NULL
    
    cpdef Py_ssize_t _raw_write(self, bytes __text not None) except -1:
        if self.fp == NULL:
            PyErr_Format(OSError, "%S is not writable", <void*>self)
        cdef const char* encoding = unicode2string(self.encoding, NULL)
        fputs(self.fp, text)
        
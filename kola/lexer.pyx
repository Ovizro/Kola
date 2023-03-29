# distutils: sources = [kola/unicode_handler.c]
cimport cython
from libc.stdint cimport uint8_t
from libc.string cimport strchr, strcmp
from cpython cimport Py_DECREF, PyLong_FromString, PyFloat_FromString, PyUnicode_FromStringAndSize, \
    PyBytes_FromStringAndSize, PyUnicode_Decode, PyErr_Format, PyErr_SetFromErrno
from ._yylex cimport *

from .exception import KoiLangSyntaxError


DEF BUFFER_SIZE = 1 << 14

# token syn
S_CMD = CMD
S_CMD_N = CMD_N
S_TEXT = TEXT
S_LITERAL = LITERAL
S_STRING = STRING
S_NUM = NUM
S_NUM_H = NUM_H
S_NUM_B = NUM_B
S_NUM_F = NUM_F
S_CLN = CLN
S_CMA = CMA
S_SLP = SLP
S_SRP = SRP
S_ANNOTATION = ANNOTATION


@cython.final
cdef class Token:
    """
    Token used in lexer

    Don't instantiate this class directly unless you make
    sure enough arguments provided.
    """

    def __cinit__(
        self,
        TokenSyn syn,
        val = None,
        *,
        int lineno = 0,
        bytes raw_val = None
    ):
        self.syn = syn
        self.val = val

        self.lineno = lineno
        self.raw_val = bytes(val) if raw_val is None else raw_val
    
    def __eq__(self, other):
        return self is other or self.syn == other
    
    cpdef int get_flag(self):
        if self.syn <= TEXT or self.syn == ANNOTATION:
            return 0
        elif self.syn == LITERAL:
            return 1
        elif self.syn <= NUM_F:
            return 2
        else:
            return self.syn - CLN + 3 
    
    def __repr__(self):
        if self.val is None:
            return PyUnicode_FromFormat("<token %d>", self.syn)
        else:
            return PyUnicode_FromFormat("<token %d: %R>", self.syn, <void*>self.val)
    

cdef class BaseLexer(object):
    """
    KoiLang lexer reading from stdin
    """

    def __cinit__(self, *args, **kwds):
        self.encoding = "utf-8"
        if yylex_init_extra(&self.lexer_data, &self.scanner):
            PyErr_SetFromErrno(RuntimeError)
    
    def __init__(self, *, str encoding not None = "utf-8", uint8_t command_threshold = 1):
        yyrestart(stdin, self.scanner)
        self.lexer_data.filename = "<stdin>"
        self.lexer_data.command_threshold = command_threshold
        self.encoding = encoding
    
    def __dealloc__(self):
        self.close()
        if self.scanner:
            yylex_destroy(self.scanner)
    
    cpdef void close(self):
        yypop_buffer_state(self.scanner)
    
    cdef void set_error(self, const char* text) except *:
        cdef int errno = 1
        
        # correct lineno and set error
        cdef bint c = strchr(text, ord('\n')) != NULL
        cdef int lineno = yyget_lineno(self.scanner)
        if c or text[0] == 0:
            lineno -= c
            errno = 10
        kola_set_error(KoiLangSyntaxError, errno, self.lexer_data.filename, lineno, text)
    
    cdef (int, const char*, Py_ssize_t) next_syn(self):
        cdef int syn = yylex(self.scanner)
        return syn, yyget_text(self.scanner), yyget_leng(self.scanner)
    
    cdef Token next_token(self):
        if not yylex_check(self.scanner):
            raise OSError("operation on closed lexer")

        cdef:
            int syn
            const char* text
            Py_ssize_t text_len
            const char* encoding
        syn, text, text_len = self.next_syn()

        val = None
        if syn == NUM or syn == CMD_N:
            val = PyLong_FromString(text, NULL, 10)
        elif syn == NUM_H:
            val = PyLong_FromString(text, NULL, 16)
        elif syn == NUM_B:
            val = PyLong_FromString(text, NULL, 2)
        elif syn == NUM_F:
            val = PyFloat_FromString(text)
        elif syn == CMD or syn == LITERAL:
            val = PyUnicode_FromStringAndSize(text, text_len)
        elif syn == TEXT or syn == ANNOTATION:
            encoding = unicode2string(self.encoding, NULL)
            s = PyUnicode_Decode(text, text_len, encoding, NULL)
            val = <str>filter_text(s)
        elif syn == STRING:
            encoding = unicode2string(self.encoding, NULL)
            if strcmp(encoding, "utf-8") != 0:
                s = PyUnicode_Decode(text, text_len, encoding, NULL)
                text = unicode2string(s, &text_len)
            try:
                val = decode_escapes(text + 1, text_len - 2)
            except Exception as e:
                kola_set_errcause(KoiLangSyntaxError, 5, self.lexer_data.filename, yyget_lineno(self.scanner), text, e)
        elif syn == 0:
            self.set_error(text)
        elif syn == EOF:
            return None
        return Token(
            syn, val,
            lineno=yyget_lineno(self.scanner),
            raw_val=PyBytes_FromStringAndSize(text, text_len)
        )

    @property
    def filename(self):
        return self.lexer_data.filename.decode()
    
    @property
    def lineno(self):
        return yyget_lineno(self.scanner)
    
    @property
    def column(self):
        return yyget_column(self.scanner)
    
    @property
    def command_threshold(self):
        return self.lexer_data.command_threshold
    
    @property
    def closed(self):
        return not yylex_check(self.scanner)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        token = self.next_token()
        if token is None:
            raise StopIteration
        return token
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def __repr__(self):
        if not yylex_check(self.scanner):
            return PyUnicode_FromFormat("<kola lexer in file \"%s\" closed>")
        else:
            return PyUnicode_FromFormat(
                "<kola lexer in file \"%s\" line %d>",
                self.lexer_data.filename,
                yyget_lineno(self.scanner)
            )


cdef class FileLexer(BaseLexer):
    """
    KoiLang lexer reading from file
    """

    def __init__(
        self, __path not None, *,
        str encoding not None = "utf-8",
        uint8_t command_threshold = 1
    ):
        if self.fp:
            fclose(self.fp)

        self._filenameo = __path
        cdef PyObject* p_addr
        self.fp = kola_open(__path, &p_addr, 'r')
        p = <object>p_addr
        self._filenameb = <bytes>p if isinstance(p, bytes) else (<str>p).encode()
        Py_DECREF(p)

        self.encoding = encoding
        yyrestart(self.fp, self.scanner)
        self.lexer_data.filename = self._filenameb
        self.lexer_data.command_threshold = command_threshold
    
    cpdef void close(self):
        BaseLexer.close(self)
        if self.fp:
            fclose(self.fp)
            self.fp = NULL
    
    @property
    def filename(self):
        return self._filenameo


cdef class StringLexer(BaseLexer):
    """
    KoiLang lexer reading from string provided
    """

    def __init__(
        self, content not None, *,
        str encoding not None = "utf-8",
        uint8_t command_threshold = 1
    ):
        if not self.content is None:
            yypop_buffer_state(self.scanner)

        if isinstance(content, str):
            self.content = (<str>content).encode()
        else:
            self.content = content

        self.encoding = encoding
        yy_scan_bytes(self.content, len(self.content), self.scanner)
        self.lexer_data.filename = "<string>"
        self.lexer_data.command_threshold = command_threshold

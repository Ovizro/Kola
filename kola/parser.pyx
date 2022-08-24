from .exception import KoiLangSyntaxError


cdef class Parser:
    def __init__(self, BaseLexer lexer not None, command_set not None):
        self.lexer = lexer
        self.command_set = command_set
    
    cpdef void push(self, Token n):
        n.next = self.stack_top
        self.stack_top = n
    
    cpdef Token pop(self):
        cdef Token n = self.stack_top
        if n is None:
            self.set_error()
        self.stack_top = n.next
        return n
    
    cdef void set_error(self, const char* format = "unknown syntax") except *:
        cdef:
            int lineno = 1
            int errno = 16
            const char* text = ""
        if not self.t_cache is None:
            lineno = self.t_cache.lineno
            errno = (self.stat << 4) + self.t_cache.syn
            text = <char*>self.t_cache.raw_val
        while not self.t_cache is None and not CMD <= self.t_cache.syn <= TEXT:
            self.t_cache = self.lexer.next_token()
        kola_set_error(KoiLangSyntaxError, errno,
            self.lexer._filename, lineno, text)
    
    cpdef object exec_once(self):
        cdef:
            uint8_t stat = 1, action = 0

            list args = []
            dict kwds = {}
            Token i, t

        t = self.t_cache
        if t is None:
            t = self.lexer.next_token()
            if t is None:
                return
        if t.syn == CMD:
            c = self.command_set[t.val]
        elif t.syn == CMD_N:
            c = self.command_set["@number"]
            args.append(t.val)
        elif t.syn == TEXT:
            c = self.command_set["@text"]
            args.append(t.val)
        else:
            raise KoiLangSyntaxError("invalid command")
        
        while True:
            self.stat = stat
            i = self.lexer.next_token()
            if i is None:
                break
                
            stat = yy_goto[i.get_flag()][stat - 1]
            action = stat >> 4
            stat &= 0x0F

            if action == 1:
                args.append(i.val)
            elif action == 2:
                self.push(i)
            elif action == 3:
                args.append(self.pop().val)
            elif action == 4:
                v = self.pop().val
                i = self.pop()
                if not i.syn == LITERAL:
                    self.set_error("keyword must be a literal")
                kwds[i.val] = v
            elif action == 5:
                i = self.pop()
                if not i.syn == LITERAL:
                    self.set_error("keyword must be a literal")
                kwds[i.val] = v
            elif action == 6:
                v = [self.pop().val]
            elif action == 7:
                (<list>v).append(i.val)
            elif action == 8:
                v = {}
            elif action == 9:
                (<dict>v)[self.pop().val] = i.val
            elif action == 10:
                args.append(self.pop().val)
                self.push(i)

            if stat == 15:
                break
            elif stat == 0:
                self.t_cache = i
                self.set_error()
                
        if not self.stack_top is None:
            self.t_cache = self.stack_top
            self.stack_top = None
            self.set_error()

        self.t_cache = i
        return c(*args, **kwds)
    
    cpdef void exec_(self) except *:
        self.exec_once()
        while not self.t_cache is None:
            self.exec_once()

    def __iter__(self):
        return self
    
    def __next__(self):
        ret = self.exec_once()
        if self.t_cache is None:
            raise StopIteration
        return ret
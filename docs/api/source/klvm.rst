Klvm
----

KoiLang Virtual Machine module

.. toctree::
   :maxdepth: 4
   :caption: klvm:

Command Module
>>>>>>>>>>>>>>>

.. automodule:: kola.klvm.command
   :members:
   :exclude-members: Command

   .. autoclass:: Command
        :special-members:

CommandSet Module
>>>>>>>>>>>>>>>>>>

.. automodule:: kola.klvm.commandset
   :special-members:

   .. autoclass:: CommandSetMeta
      :special-members: __new__, __command_field__
        
      .. py:decoratormethod:: register_command
                              register_command(\
                                 self, __name: Optional[str] = ..., *, alias: Union[Iterable[str], str] = ..., **kwds: Any\
                              )

         declare a function as a KoiLang command in the class
         
         :param __name: the name of the command used in KoiLang, defaults to None
         :type __name: str, optional
         :param envs: a list of valid environment names that can be used for the command
         :type envs: Iterable[str] or str, optional
         :param alias: alias of the command
         :type alias: Iterable[str] or str, optional
         :param any kwds: extra command data
         :return: wrapped function (a Command object)
         :rtype: Command
         
      .. py:decoratormethod:: register_text
                              register_text(\
                                 self, *, alias: Union[Iterable[str], str] = ..., **kwds: Any\
                              )

         declare a function as a KoiLang text handling function in the class
         
         :param envs: a list of valid environment names that can be used for the command
         :type envs: Iterable[str] or str, optional
         :param alias: alias of the command
         :type alias: Iterable[str] or str, optional
         :param any kwds: extra command data
         :return: wrapped function (a Command object)
         :rtype: Command
         
      .. py:decoratormethod:: register_number
                              register_number(\
                                 self, *, alias: Union[Iterable[str], str] = ..., **kwds: Any\
                              )

         declare a function as a KoiLang number command in the class
         
         :param envs: a list of valid environment names that can be used for the command
         :type envs: Iterable[str] or str, optional
         :param alias: alias of the command
         :type alias: Iterable[str] or str, optional
         :param any kwds: extra command data
         :return: wrapped function (a Command object)
         :rtype: Command
         
      .. py:decoratormethod:: register_annotation
                              register_annotation(\
                                 self, *, alias: Union[Iterable[str], str] = ..., **kwds: Any\
                              )

         declare a function as a KoiLang annotation handling function in the class
         
         :param envs: a list of valid environment names that can be used for the command
         :type envs: Iterable[str] or str, optional
         :param alias: alias of the command
         :type alias: Iterable[str] or str, optional
         :param any kwds: extra command data
         :return: wrapped function (a Command object)
         :rtype: Command
   
   .. autoclass:: CommandSet
      :members:
      :special-members: __kola_caller__, __getitem__

Environment Module
>>>>>>>>>>>>>>>>>>

.. automodule:: kola.klvm.environment
   :members:

Writer Module
>>>>>>>>>>>>>

.. automodule:: kola.klvm.writer
   :members:

Main Module
>>>>>>>>>>>>>
   
.. automodule:: kola.klvm.koilang
   :members:
   :exclude-members: KoiLangMeta

   .. autoclass:: KoiLangMeta
      :members:
      :special-members: __new__, __text_encoding__, __text_lstrip__, __command_threshold__

Decorator Module
>>>>>>>>>>>>>>>>>

.. py:module:: kola.klvm.decorator
    
    .. py:decorator:: kola_command
                      kola_command(\
                        func: Optional[str] = None,\
                        *,\
                        envs: Union[Iterable[str], str] = ...,\
                        alias: Union[Iterable[str], str] = ...,\
                        **kwds: Any\
                      )

        declare a function as a KoiLang command

        :param func: the name of the command used in KoiLang
        :type func: str , optional
        :param envs: a list of valid environment names that can be used for the command
        :type envs: Iterable[str] or str
        :param alias: alias of the command
        :type alias: Iterable[str] or str
        :param any kwds: extra command data
        :return: wrapped function (a Command object)
        :rtype: Command

    .. py:decorator:: kola_text
                      kola_text(\
                        *,\
                        envs: Union[Iterable[str], str] = ...,\
                        alias: Union[Iterable[str], str] = ...,\
                        **kwds: Any\
                      )

        declare a function as a KoiLang text handling command

        :param envs: a list of valid environment names where the command can be called
        :type envs: Iterable[str] or str
        :param alias: alias of the command
        :type alias: Iterable[str] or str
        :param any kwds: extra command data
        :return: wrapped function (a Command object)
        :rtype: Command
        
    .. py:decorator:: kola_number
                      kola_number(\
                        *,\
                        envs: Union[Iterable[str], str] = ...,\
                        alias: Union[Iterable[str], str] = ...,\
                        **kwds: Any\
                      )

        declare a function as a KoiLang number command

        :param envs: a list of valid environment names where the command can be called
        :type envs: Iterable[str] or str
        :param alias: alias of the command
        :type alias: Iterable[str] or str
        :param any kwds: extra command data
        :return: wrapped function (a Command object)
        :rtype: Command
        
    .. py:decorator:: kola_annotation
                      kola_annotation(\
                        *,\
                        envs: Union[Iterable[str], str] = ...,\
                        alias: Union[Iterable[str], str] = ...,\
                        **kwds: Any\
                      )

        declare a function as a KoiLang annotation handling command

        :param envs: a list of valid environment names where the command can be called
        :type envs: Iterable[str] or str
        :param alias: alias of the command
        :type alias: Iterable[str] or str
        :param any kwds: extra command data
        :return: wrapped function (a Command object)
        :rtype: Command
        
    .. py:decorator:: kola_env_enter
                      kola_env_enter(\
                        *,\
                        envs: Union[Iterable[str], str] = ...,\
                        alias: Union[Iterable[str], str] = ...,\
                        **kwds: Any\
                      )

        declare a function as a KoiLang environment entry command

        :param envs: a list of valid environment names where the command can be called
        :type envs: Iterable[str] or str
        :param alias: alias of the command
        :type alias: Iterable[str] or str
        :param any kwds: extra command data
        :return: wrapped function (a Command object)
        :rtype: EnvironmentEntry

    .. py:decorator:: kola_env_exit
                      kola_env_exit(\
                        *,\
                        envs: Union[Iterable[str], str] = ...,\
                        alias: Union[Iterable[str], str] = ...,\
                        **kwds: Any\
                      )

        declare a function as a KoiLang environment exit command

        :param envs: a list of valid environment names where the command can be called
        :type envs: Iterable[str] or str
        :param alias: alias of the command
        :type alias: Iterable[str] or str
        :param any kwds: extra command data
        :return: wrapped function (a Command object)
        :rtype: EnvironmentExit
        
    .. py:decorator:: kola_command_set
                      kola_command_set(**kwds: Any)

        transform the class into a CommandSet class

        :param any kwds: class config
        :return: a CommandSet class
        :rtype: CommandSet
        
    .. py:decorator:: kola_environment
                      kola_environment(**kwds: Any)

        transform the class into a Environment class

        :param any kwds: class config
        :return: a Environment class
        :rtype: Environment
        
    .. py:decorator:: kola_main
                      kola_main(**kwds: Any)

        transform the class into a KoiLang class

        :param any kwds: extra command data
        :return: a KoiLang class
        :rtype: KoiLang

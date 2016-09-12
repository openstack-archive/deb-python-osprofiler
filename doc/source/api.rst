======
 API
======

There are a few things that you should know about API before using it.

Four ways to add a new trace point.
-----------------------------------

.. code-block:: python

    from osprofiler import profiler

    def some_func():
        profiler.start("point_name", {"any_key": "with_any_value"})
        # your code
        profiler.stop({"any_info_about_point": "in_this_dict"})


    @profiler.trace("point_name",
                    info={"any_info_about_point": "in_this_dict"},
                    hide_args=False)
    def some_func2(*args, **kwargs):
        # If you need to hide args in profile info, put hide_args=True
        pass

    def some_func3():
        with profiler.Trace("point_name",
                            info={"any_key": "with_any_value"}):
            # some code here

    @profiler.trace_cls("point_name", info={}, hide_args=False,
                        trace_private=False)
    class TracedClass(object):

        def traced_method(self):
            pass

        def _traced_only_if_trace_private_true(self):
             pass

How profiler works?
-------------------

* **@profiler.Trace()** and **profiler.trace()** are just syntax sugar,
  that just calls **profiler.start()** & **profiler.stop()** methods.

* Every call of **profiler.start()** & **profiler.stop()** sends to
  **collector** 1 message. It means that every trace point creates 2 records
  in the collector. *(more about collector & records later)*

* Nested trace points are supported. The sample below produces 2 trace points:

    .. code-block:: python

        profiler.start("parent_point")
        profiler.start("child_point")
        profiler.stop()
        profiler.stop()

    The implementation is quite simple. Profiler has one stack that contains
    ids of all trace points. E.g.:

    .. code-block:: python

        profiler.start("parent_point") # trace_stack.push(<new_uuid>)
                                       # send to collector -> trace_stack[-2:]

        profiler.start("parent_point") # trace_stack.push(<new_uuid>)
                                       # send to collector -> trace_stack[-2:]
        profiler.stop()                # send to collector -> trace_stack[-2:]
                                       # trace_stack.pop()

        profiler.stop()                # send to collector -> trace_stack[-2:]
                                       # trace_stack.pop()

    It's simple to build a tree of nested trace points, having
    **(parent_id, point_id)** of all trace points.

Process of sending to collector.
--------------------------------

Trace points contain 2 messages (start and stop). Messages like below are
sent to a collector:

.. parsed-literal::

  {
      "name": <point_name>-(start|stop)
      "base_id": <uuid>,
      "parent_id": <uuid>,
      "trace_id": <uuid>,
      "info": <dict>
  }

The fields are defined as the following:

* base_id - ``<uuid>`` that is equal for all trace points that belong
  to one trace, this is done to simplify the process of retrieving
  all trace points related to one trace from collector
* parent_id - ``<uuid>`` of parent trace point
* trace_id - ``<uuid>`` of current trace point
* info - the dictionary that contains user information passed when calling
  profiler **start()** & **stop()** methods.

Setting up the collector.
-------------------------

The profiler doesn't include a trace point collector. The user/developer
should instead provide a method that sends messages to a collector. Let's
take a look at a trivial sample, where the collector is just a file:

.. code-block:: python

    import json

    from osprofiler import notifier

    def send_info_to_file_collector(info, context=None):
        with open("traces", "a") as f:
            f.write(json.dumps(info))

    notifier.set(send_info_to_file_collector)

So now on every **profiler.start()** and **profiler.stop()** call we will
write info about the trace point to the end of the **traces** file.

Initialization of profiler.
---------------------------

If profiler is not initialized, all calls to **profiler.start()** and
**profiler.stop()** will be ignored.

Initialization is a quite simple procedure.

.. code-block:: python

    from osprofiler import profiler

    profiler.init("SECRET_HMAC_KEY", base_id=<uuid>, parent_id=<uuid>)

``SECRET_HMAC_KEY`` - will be discussed later, because it's related to the
integration of OSprofiler & OpenStack.

**base_id** and **trace_id** will be used to initialize stack_trace in
profiler, e.g. ``stack_trace = [base_id, trace_id]``.

OSProfiler CLI.
---------------

To make it easier for end users to work with profiler from CLI, osprofiler
has entry point that allows them to retrieve information about traces and
present it in human readable from.

Available commands:

* Help message with all available commands and their arguments:

    .. parsed-literal::

        $ osprofiler -h/--help

* OSProfiler version:

    .. parsed-literal::

        $ osprofiler -v/--version

* Results of profiling can be obtained in JSON (option: ``--json``) and HTML
  (option: ``--html``) formats:

    .. parsed-literal::

        $ osprofiler trace show <trace_id> --json/--html

    hint: option ``--out`` will redirect result of ``osprofiler trace show``
    in specified file:

    .. parsed-literal::

        $ osprofiler trace show <trace_id> --json/--html --out /path/to/file

* Using other storage drivers (e.g. MongoDB, ElasticSearch):

    .. parsed-literal::

       $ osprofiler trace show <trace_id> --connection-str=<URI> --json/--html

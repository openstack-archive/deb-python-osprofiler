===========================================================
 OSProfiler -- Library for cross-project profiling library
===========================================================

.. image:: https://img.shields.io/pypi/v/osprofiler.svg
    :target: https://pypi.python.org/pypi/osprofiler/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/osprofiler.svg
    :target: https://pypi.python.org/pypi/osprofiler/
    :alt: Downloads

OSProfiler provides a tiny but powerful library that is used by
most (soon to be all) OpenStack projects and their python clients. It
provides functionality to be able to generate 1 trace per request, that goes
through all involved services. This trace can then be extracted and used
to build a tree of calls which can be quite handy for a variety of
reasons (for example in isolating cross-project performance issues).

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/osprofiler
* Source: http://git.openstack.org/cgit/openstack/osprofiler
* Bugs: http://bugs.launchpad.net/osprofiler

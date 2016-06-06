============
 Background
============

OpenStack consists of multiple projects. Each project, in turn, is composed of
multiple services. To process some request, e.g. to boot a virtual machine,
OpenStack uses multiple services from different projects. In the case something
works too slowly, it's extremely complicated to understand what exactly goes
wrong and to locate the bottleneck.

To resolve this issue, we introduce a tiny but powerful library,
**osprofiler**, that is going to be used by all OpenStack projects and their
python clients. To be able to generate 1 trace per request, that goes through
all involved services, and builds a tree of calls.

Why not cProfile and etc?
-------------------------

**The scope of this library is quite different:**

* We are interested in getting one trace of points from different service,
  not tracing all python calls inside one process.

* This library should be easy integratable in OpenStack. This means that:

  * It shouldn't require too many changes in code bases of integrating
    projects.

  * We should be able to turn it off fully.

  * We should be able to keep it turned on in lazy mode in production
    (e.g. admin should be able to "trace" on request).

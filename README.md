Quantcast Apex Linter for Salesforce
====================================

At Quantcast we're interested
in promoting the highest coding standards,
and Salesforce is no exception.

This framework provides
a simple and consistent framework
for implementing code checks
using regular expressions.

It automatically identifies
both the line and character,
and allows an annotation
to override the warning as needed.

The initial release
flags the following cases:

* Object types as Map keys or Set members
    * SObject hashes are computed
    from field values.
        * Changes to field values of keys
        make Map values inaccessible.
        * For Sets, it causes Set.contains()
        to return false
    * Object hashes default to memory locations
    * These differences produce subtle bugs,
    so we recommend against the practice
    * However, we do allow it
    with a link to the issue documentation.
* `SeeAllData` in tests
    * Creates situations in which test execution
    can conflict with production data.
    * Encourages DML in tests,
    which slows them down.
    * Row-locking data
    used by production systems
    can cause deployments
    and production processes to fail.
    * `SeeAllData=false` doesn't do anything
    in classes where `SeeAllData=true`!
* No `@future` in test classes
    * Futures are scheduled
    in a small finite queue.
    * If "Disable Parallel Test Execution" is off,
    this queue can get full.
    * We recommend:
        * Use `@testSetup` instead of `@future` to avoid mixed DML issues.
        * Use `Test.startTest()` and `Test.stopTest()` to avoid "Too Many SOQL Queries".
* A check for the obsolete `testMethod` keyword
    * Use the `@isTest` annotation instead.

Using the Apex Linter
----------------

To run the Apex Linter,
you'll need Python 3.7.

To run it over the source tree:

        python3 -m apexlint src/

At Quantcast we run the Apex Linter
on every pull request.

Contributing to the Apex Linter
---------------------------
We welcome contributions to the Apex Linter
in the form of enhancement requests, patches,
additional tests, bug reports, new ideas, and so on.
Use [GitHub issues][issues] to report bugs.
and refer to the [Apex Linter code contribution policy][ccp]
when contributing code.

Have Questions?
---------------
Post comments or questions to <mailto:qc-salesforce-dev@googlegroups.com>

Join Google Group to search archives: <http://groups.google.com/group/qc-salesforce-dev>

License
--------
Quantcast Apex Linter is released under the Apache 2.0 license.

[ccp]: https://github.com/quantcast/apex-linter/CONTRIBUTING.md
[issues]: https://github.com/quantcast/apex-linter/issues
[develop]: https://github.com/quantcast/apex-linter/wiki/Developer-Documentation

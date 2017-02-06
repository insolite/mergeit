=======
merGeIT
=======

GIT auto merge tool

Overview
========

merGeIT allows to handle git push events and do automatic merges
according to configured branch dependencies.

How it works
============

First of all you define branch dependencies in a way *"source-target branches"*.
The *source* branch is defined as regular expression.
All *target* branches are defined as list under *source* branch section.

Optionally filters and hooks can be defined for each dependency.
Filters can cancel merge or change target branch before merge depending on push event info.
Hooks are mostly used to send notifications about merge result,
close tasks in task manager or cancel push merge if i. e. unittests fails.

When push event occurs on some branch, push handler matches name of this branch
across all patterns and runs *merge process* for *source* into *target*.
The *merge process* is completed in 3 steps:

* Executing filters
* Actual GIT merge operation
* Executing hooks
* GIT push operation

Both filters and hooks has ability to cancel *merge process*.

Features
========

 * **Branch dependencies** using regexp for source (push) branch matching and list of target (merge) branches
 * **Filters** to control merging flow with specific logic
 * **Hooks** to notify about success/fail merge events

Config
======

For each project (repo) there should be one YAML config that defines all branch dependencies and filters/hooks definitions/uses.

The following example explains how to set up simple scheme "Keep *develop* branch up-to-date with *master* updates":

.. code-block:: yaml
    dependencies:
      '^master$':
        targets:
            - develop

Custom filters and hooks
========================

merGeIT comes with some helpful filters and hooks for Redmine and GitLab located in **extras** module. You can implement similar things for any other software you use. Also, feel free to make pull request to add them to merGeIT repo ;)

Usage
=====

Run hook handle server:

.. code-block:: bash

    mergeit -H 0.0.0.0 -p 1234 -sh 0.0.0.0 -sp 1235 -c config_samples/full.yaml -l test-repo

Display help:

.. code-block:: bash

    mergeit -h

Run shell (for manual commands):

.. code-block:: bash

    mergeit-shell -c config_samples/full.yaml -l test.log

Connect to server's same shell via telnet (while mergeit server running):

.. code-block:: bash

    telnet localhost 1235

Simplest config example
=======================

Coming soon

Install
=======

Install package:

.. code-block:: bash

    python3 setup.py install

Run tests (optionally):

.. code-block:: bash

    python3 -m unittest discover tests

TODO
====

* Add support for raw git push hooks (not only gitlab)
* Add ability to configure git remotes somehow

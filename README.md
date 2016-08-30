# merGeIT - git auto merge tool

## Overview

merGeIT allows to handle git push events and do automatic merges according to configured branch dependencies.

## Install

Install package:

```bash
python3 setup.py install
```

Run tests (optionally):

```bash
python3 -m unittest discover tests
```

## Run

Run hook handle server:

```bash
mergeit -H 0.0.0.0 -p 1234 -sh 0.0.0.0 -sp 1235 -c config_samples/full.yaml -l test.log
```

Display help:

```bash
mergeit -h
```

Run shell (for manual commands):

```bash
mergeit-shell -c config_samples/full.yaml -l test.log
```

Connect to server's same shell via telnet (while mergeit server running):

```bash
telnet localhost 1235
```

## Features

 * **Branch dependencies** using regexp for source (push) branch matching and list of target (merge) branches
 * **Filters** to control merging flow with specific logic
 * **Hooks** to notify about success/fail merge events

## How it works

First of all you define branch dependencies in a way _"source-target branches"_. The _source_ branch is defined as regular expression. All _target_ branches are defined as list under _source_ branch section.

Optionally filters and hooks can be defined for each dependency. Filters can cancel merge or change target branch before merge depending on push event info. Hooks are mostly used to send notifications about merge result, close tasks in task manager or cancel push merge if i. e. unittests fails.

When push event occurs on some branch, push handler matches name of this branch across all patterns and runs _merge process_ for _source_ into _target_. The _merge process_ is completed in 3 steps:

* Executing filters
* Actual GIT merge operation
* Executing hooks
* GIT push operation

Both filters and hooks has ability to cancel _merge process_.

## Config

For each project (repo) there should be one YAML config that defines all branch dependencies and filters/hooks definitions/uses.

The following example explains how to set up simple scheme "Keep _develop_ branch up-to-date with _master_ updates":

```yaml
dependencies:
  '^master$':
  	targets:
    	- develop
```

## Custom filters and hooks

merGeIT comes with some helpful filters and hooks for Redmine and GitLab located in **extras** module. You can implement similar things for any other software you use. Also, feel free to make pull request to add them to merGeIT repo ;)

## TODO

* Add support for raw git push hooks (not only gitlab)
* Add ability to configure git remotes somehow
* Add more TODO items

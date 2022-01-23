# shfz-flask

![GitHub](https://img.shields.io/github/license/shfz/shfz-flask)
![PyPI](https://img.shields.io/pypi/v/shfzflask)
![PyPI - Downloads](https://img.shields.io/pypi/dm/shfzflask)

A trace library for Python Flask web application

This library records what processing was done by each endpoint's request and uses it to generate fuzz with a genetic algorithm.

This library is supposed to be used with [shfz/shfz](https://github.com/shfz/shfz) and [shfz/shfzlib](https://github.com/shfz/shfzlib).

## Install

```
pip install -U shfzflask
```

## Usage

```python
from flask import Flask
from shfzflask import shfztrace

app = Flask(__name__)
shfztrace(app, debug=False)
```

> ### Options
> - `trace` (True) : Please set to False in the production environment
> - `debug` (False) : Enable debug
> - `debugFrame` (False) : All the acquired Frames are written out sequentially
> - `report` (True) : Report shfz server
> - `fuzzUrl` (http://localhost:53653) : A URL of shfz server

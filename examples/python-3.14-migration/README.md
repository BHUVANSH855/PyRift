# Python 3.14 Compatibility Example

This example demonstrates PyRift detecting a Python 3.14 behavior change.

## Before

`before.py` contains:

```python
loop = asyncio.get_event_loop()
```

Run:

```bash
pyrift scan before.py --runtime cpython --python-min 3.13 --python-max 3.14 --format text
```

PyRift reports CPY038 because `asyncio.get_event_loop()` raises `RuntimeError` in Python 3.14+.

## After

`after.py` uses `asyncio.run()` instead.

```python
asyncio.run(main())
```

PyRift reports no compatibility issue for the migrated code.

## What this demonstrates

```text
Existing Python code
        |
        v
      PyRift
        |
        v
Compatibility finding
        |
        v
   Fix the code
        |
        v
      PyRift
        |
        v
    No finding
```

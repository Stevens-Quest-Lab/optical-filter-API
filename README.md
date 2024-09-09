# optical-filter-API #
## Overview
Python library for Agiltron 1550nm electronically tunable optical filter.

## Getting Started
Install the required Python package
```
pip install pyserial
```

## Example
The following example sets the optical filter to a 1550.4nm:
```
import filter
ser = filter.connect()
filter.set_channel(ser, 1550.4)
```
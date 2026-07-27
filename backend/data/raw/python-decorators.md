# Python Decorators

## Overview
A decorator in Python is a function that takes another function and extends its behavior without explicitly modifying it. Decorators are a form of metaprogramming and enable reusable cross-cutting concerns like logging, timing, and access control.

## Details
Decorators use the @ syntax, which is syntactic sugar for func = decorator(func). Python passes the decorated function to the decorator and rebinds the result to the original name. The functools.wraps decorator should be used to preserve metadata like __name__ and __doc__ from the original function.

### Basic Function Decorator
```python
import functools

def logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result
    return wrapper

@logger
def add(a, b):
    return a + b
```

### Decorators with Arguments
To pass arguments to a decorator, you need three levels of nesting: the outer function accepts the decorator arguments, the middle function accepts the original function, and the inner wrapper accepts the call arguments.

```python
def repeat(n):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello {name}")
```

### Class-based Decorators
Decorators can also be implemented as classes by defining __call__:

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)
```

### Common Use Cases
- Logging and debugging
- Timing and profiling
- Access control and authentication
- Caching and memoization
- Input validation and type checking
- Rate limiting

@CountCalls
def hello():
    print("Hello")

hello()
print(hello.count)  # 1

"""
Visual demonstration of how the decorator pattern works
"""

class SimpleRegistry:
    def __init__(self):
        self.functions = {}

    def register(self, func):
        """This is a decorator - takes a function, returns a function"""
        print(f"📝 Registering: {func.__name__}")

        # Store the function
        self.functions[func.__name__] = func

        # Return the SAME function (unchanged)
        return func


# Create a registry instance
my_registry = SimpleRegistry()


# Method 1: Using as a decorator (common way)
@my_registry.register
def say_hello(name: str):
    """Says hello"""
    return f"Hello, {name}!"


# Method 2: Manual registration (same thing, just explicit)
def say_goodbye(name: str):
    """Says goodbye"""
    return f"Goodbye, {name}!"

say_goodbye = my_registry.register(say_goodbye)  # Same as using @decorator


# Both methods work exactly the same
print("\n" + "="*60)
print("CALLING THE FUNCTIONS")
print("="*60)
print(say_hello("Alice"))      # Works normally!
print(say_goodbye("Bob"))      # Works normally!

print("\n" + "="*60)
print("CHECKING THE REGISTRY")
print("="*60)
print(f"Registered functions: {list(my_registry.functions.keys())}")
print(f"Can call from registry: {my_registry.functions['say_hello']('Charlie')}")

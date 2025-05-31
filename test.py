#  // TODO: Test syntax highlighting

import math

@decorator
class TestClass:
    """This is a docstring"""

    def __init__(self, value=42):
        self.value = value  # Initialize value

    def calculate(self, x, y=3.14):
        if x > y:
            print("x is greater than y")
        elif x == y:
            print('x equals y')
        else:
            # // FIXME: handle other cases
            print("x is less than y")

        result = self.value + x * y - 123.456
        return result

def sample_function(param1, *args, **kwargs):
    print("Function call with param1 =", param1)
    for i in range(5):
        print(f"Loop iteration {i}")

# Call functions and use builtins
obj = TestClass(10)
val = obj.calculate(5)
print(val)
print(abs(-7))

# Numbers
num_int = 123
num_float = 45.67
num_exp = 1.23e-4

# Strings with escapes
str1 = "Hello\nWorld"
str2 = 'Single \'quoted\' string'

# Operators
a = 10 + 20 * 3 / 2 - 5 % 3

# Comments and TODOs
# // NOTE: This is a note comment


# // HACK: Temporary fix



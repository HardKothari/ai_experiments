# sample_module.py

class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            print("Warning: Divisor cannot be zero.")
            return None
        return a / b


def square(x):
    return x ** 2

def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    calc = Calculator()
    result = calc.divide(5, 0)
    print(result)

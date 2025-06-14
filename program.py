def multiply(a, b):
    """Multiply two numbers and return the result."""
    return a * b

def main():
    # Get input from user
    try:
        num1 = float(input("Enter the first number: "))
        num2 = float(input("Enter the second number: "))
        
        # Calculate the product
        result = multiply(num1, num2)
        
        # Display the result
        print(f"{num1} × {num2} = {result}")
        
    except ValueError:
        print("Error: Please enter valid numbers.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
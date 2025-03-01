from manifold3d import *

def execute_code(code: str) -> Manifold:
    # Create a dictionary to serve as a local namespace for exec.
    namespace = {}
    exec(code, namespace)  # Execute the code in the provided namespace.
    
    # Ensure that the expected function is defined.
    if "create_object" not in namespace or not callable(namespace["create_object"]):
        raise ValueError("The code must define a callable 'create_object' function.")
    
    # Call the create_object function and return its result.
    return namespace["create_object"]()



if __name__ == "__main__":
    # Load test string from initial_code.py
    with open("initial_code.py", "r") as f:
        code = f.read()
    print(f"Loaded code {code}")
    manifold_obj = execute_code(code)

    print(f"Created Manifold object with volume {manifold_obj.volume()}")
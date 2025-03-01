from manifold3d import *
def execute_code(code) -> Manifold:
    pass



if __name__ == "__main__":
    # Load test string from initial_code.py
    with open("initial_code.py", "r") as f:
        code = f.read()
    print(f"Loaded code {code}")
    manifold_obj = execute_code(code)
    print(f"Created Manifold object with volume {manifold_obj.volume()}")
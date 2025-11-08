"""
Quick fix script to remove deprecated pinecone-plugin-inference
"""
import subprocess
import sys

def fix_pinecone():
    """Remove deprecated pinecone-plugin-inference package"""
    try:
        print("Removing deprecated pinecone-plugin-inference...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "pinecone-plugin-inference"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Successfully removed pinecone-plugin-inference")
        else:
            print(f"Note: {result.stderr}")
            print("Package may not be installed, continuing...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nPinecone fix complete. You can now run the application.")

if __name__ == "__main__":
    fix_pinecone()


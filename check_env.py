# check_env.py
import torch
import sys

print("=" * 50)
print("Python版本:", sys.version)
print("PyTorch版本:", torch.__version__)
print("CUDA可用:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("CUDA版本:", torch.version.cuda)
    print("GPU数量:", torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  内存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")

print("=" * 50)
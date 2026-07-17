from PIL import Image
import sys

path = sys.argv[1]
max_w = int(sys.argv[2])

img = Image.open(path)
print(f"before: {img.size}")
new_h = round(img.height * max_w / img.width)
resized = img.resize((max_w, new_h), Image.LANCZOS)
resized.save(path, dpi=(150, 150))
print(f"after: {resized.size}")

import os
from PIL import Image

# Paths
images_dir = 'static/images'
templates_dir = 'templates'
webp_quality = 85  # adjust for compression (0-100)

# Step 1: Convert images to WebP and delete originals
for root, dirs, files in os.walk(images_dir):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(root, file)
            webp_path = os.path.splitext(filepath)[0] + '.webp'
            
            with Image.open(filepath) as img:
                img.save(webp_path, 'WEBP', quality=webp_quality)
            
            os.remove(filepath)  # delete original
            print(f'Converted {filepath} -> {webp_path} and deleted original.')

# Step 2: Update HTML templates
for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content_new = content
            for ext in ['.png', '.jpg', '.jpeg']:
                content_new = content_new.replace(ext, '.webp')
            
            if content != content_new:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content_new)
                print(f'Updated {file_path}')

print("All images converted, originals deleted, and templates updated.")

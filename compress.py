import re, os, base64

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

os.makedirs('assets', exist_ok=True)
count = 0

def replace_b64(match):
    global count
    data = match.group(1)
    fname = f'assets/img_{count}.png'
    with open(fname, 'wb') as f:
        f.write(base64.b64decode(data))
    count += 1
    return f'src="{fname}"'

html2 = re.sub(r'src="data:image/png;base64,([^"]+)"', replace_b64, html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html2)

print(f'Done: {count} images extracted')
print(f'New size: {os.path.getsize("index.html")//1024}KB')

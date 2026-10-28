#!/usr/bin/env python3
import re
from pathlib import Path

# Read HTML
html_file = Path("Exposeseite.html")
html_content = html_file.read_text()

# Find the CSS link with relative path
pattern = r'<link rel="stylesheet" href="(\.\./){4}get/script/ressource/combine/[^"]*\.css"'
match = re.search(pattern, html_content)

if match:
    print(f"[*] Found external CSS link: {match.group(0)}")
    
    # The URL path would be: /get/script/ressource/combine/a8b9bd50d16239dac6d88d9e9eda2189_r26_7_2.css
    # We need to download this CSS or embed it
    
    # Extract CSS filename
    css_filename = re.search(r'([a-f0-9]+_r\d+_\d+\.css)', match.group(0))
    if css_filename:
        print(f"[*] CSS filename: {css_filename.group(1)}")
        
        # Try to download it (you'll need to provide the full URL)
        import subprocess
        url = "https://www.regionalimmobilien24.de/get/script/ressource/combine/" + css_filename.group(1)
        print(f"[*] Attempting to download: {url}")
        
        try:
            result = subprocess.run(['curl', '-s', '-o', css_filename.group(1), url], 
                                  timeout=10, capture_output=True)
            if result.returncode == 0:
                print(f"[✓] Downloaded CSS!")
                
                # Update HTML to point to local CSS
                new_html = html_content.replace(
                    match.group(0),
                    f'<link rel="stylesheet" href="{css_filename.group(1)}"'
                )
                html_file.write_text(new_html)
                print("[✓] HTML updated with local CSS path!")
            else:
                print("[✗] Download failed")
        except Exception as e:
            print(f"[✗] Error: {e}")
else:
    print("[!] CSS link pattern not found - checking all CSS links...")
    all_css = re.findall(r'href="([^"]*\.css)"', html_content)
    for css in all_css:
        print(f"  - {css}")


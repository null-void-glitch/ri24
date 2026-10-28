import xml.etree.ElementTree as ET
import sys

INPUT_XML = "immobilien.xml"
OUTPUT_TXT = "urls-immobilien.txt"

def extract_urls(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        return
    except FileNotFoundError:
        print(f"File not found: {input_file}")
        return

    urls = []

    for ad in root.findall(".//ad"):
        url_elem = ad.find("url")
        if url_elem is not None and url_elem.text:
            urls.append(url_elem.text.strip())

    if not urls:
        print("No URLs found.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

    print(f"Extracted {len(urls)} URLs → {output_file}")

if __name__ == "__main__":
    extract_urls(INPUT_XML, OUTPUT_TXT)

import xml.etree.ElementTree as ET
import os

def main():
    if not os.path.exists('urls-immobilien.txt'):
        print("urls.txt not found")
        return

    print("Reading urls.txt...")
    with open('urls-immobilien.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(urls)} URLs.")

    root = ET.Element('urls')
    for url in urls:
        ET.SubElement(root, 'url').text = url

    tree = ET.ElementTree(root)
    ET.indent(tree)
    
    print("Writing to input.xml...")
    tree.write('input2.xml', encoding='utf-8', xml_declaration=True)
    print("Done.")

if __name__ == '__main__':
    main()

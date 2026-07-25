import xml.etree.ElementTree as ET
import urllib.request

url = 'https://daringfireball.net/index.xml'
r = urllib.request.urlopen(url)
tree = ET.parse(r)
root = tree.getroot()

ns = {'atom': 'http://www.w3.org/2005/Atom'}
entries = root.findall('.//atom:entry', ns)

for e in entries:
    title_elem = e.find('atom:title', ns)
    if title_elem is not None and '[Sponsor]' in title_elem.text:
        print('=== Sponsor Article Found ===')
        print('Title:', title_elem.text)
        
        content_elem = e.find('atom:content', ns)
        if content_elem is not None:
            print('\\nContent tag found. Attributes:', content_elem.attrib)
            print('Content text length:', len(content_elem.text) if content_elem.text else 0)
            print('\\nContent preview (first 800 chars):')
            print(content_elem.text[:800] if content_elem.text else 'None')
        else:
            print('\\nNo content tag found!')
            
        summary_elem = e.find('atom:summary', ns)
        if summary_elem is not None:
            print('\\nSummary:', summary_elem.text[:500] if summary_elem.text else 'None')
        
        break

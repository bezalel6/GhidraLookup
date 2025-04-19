import requests
from bs4 import BeautifulSoup

url = "https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-comparestringex"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the syntax section
syntax = soup.find("h2", string="Syntax")
if syntax:
    code_block = syntax.find_next("pre")
    if code_block:
        print("Function Signature:")
        print("=" * 80)
        print(code_block.text)
        print("\nRaw HTML:")
        print("=" * 80)
        print(code_block)
        
        # Print each line with line number and content
        print("\nLine by line analysis:")
        print("=" * 80)
        for i, line in enumerate(code_block.text.split('\n')):
            print(f"{i+1:2d}: {repr(line)}")

# Find all h2 sections
print("All H2 Sections:")
print("=" * 80)
for h2 in soup.find_all("h2"):
    print(f"\nSection: {h2.text}")
    if h2.text == "Parameters":
        print("-" * 40)
        current = h2.find_next_sibling()
        while current and current.name != "h2":
            print(f"Tag: {current.name}")
            if current.name == "p":
                text = current.text.strip()
                if text:
                    print(f"  Text: {text[:100]}...")
            current = current.find_next_sibling()
    elif "Return value" in h2.text:
        print("-" * 40)
        current = h2.find_next_sibling()
        while current and current.name != "h2":
            print(f"Tag: {current.name}")
            if current.name == "table":
                print("  Found table")
                for row in current.find_all("tr")[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        dl = cells[0].find("dl")
                        name = dl.find("dt").text.strip() if dl and dl.find("dt") else cells[0].text.strip()
                        desc = cells[1].text.strip()
                        print(f"    Flag: {name}")
                        print(f"    Description: {desc[:100]}...")
            current = current.find_next_sibling()
            
print("\nLooking for flags table:")
print("=" * 80)
flags_table = soup.find("table", {"class": "table"})
if flags_table:
    print("Found flags table")
    for row in flags_table.find_all("tr")[1:]:  # Skip header
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            dl = cells[0].find("dl")
            name = dl.find("dt").text.strip() if dl and dl.find("dt") else cells[0].text.strip()
            desc = cells[1].text.strip()
            print(f"  Flag: {name}")
            print(f"  Description: {desc[:100]}...")

# Find the parameters section
print("\nParameters Section:")
print("=" * 80)
params = soup.find("h2", string="Parameters")
if params:
    param_table = params.find_next("table")
    if param_table:
        print("\nParameter Table HTML:")
        print(param_table)
        
        print("\nParameter Table Content:")
        for row in param_table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells:
                print("-" * 40)
                for i, cell in enumerate(cells):
                    print(f"Cell {i}: {cell.text.strip()}") 
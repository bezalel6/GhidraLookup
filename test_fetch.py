import requests
from bs4 import BeautifulSoup

def test_fetch():
    url = "https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-comparestringex"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('main')
            if main_content:
                print("Successfully found main content")
                
                # Check for title
                h1 = main_content.find('h1')
                if h1:
                    print(f"Found title: {h1.text}")
                else:
                    print("Could not find h1 tag")
                
                # Check for syntax section
                syntax = main_content.find('h2', string='Syntax')
                if syntax:
                    print("Found syntax section")
                    code_block = syntax.find_next('pre')
                    if code_block:
                        print("Found code block with function signature")
                else:
                    print("Could not find syntax section")
                
                # Check for parameters
                params = main_content.find('h2', string='Parameters')
                if params:
                    print("Found parameters section")
                    param_table = params.find_next('table')
                    if param_table:
                        print(f"Found parameter table with {len(param_table.find_all('tr'))} rows")
                else:
                    print("Could not find parameters section")
                
                # Check for return value
                ret_val = main_content.find('h2', string='Return value')
                if ret_val:
                    print("Found return value section")
                    ret_desc = ret_val.find_next('p')
                    if ret_desc:
                        print("Found return value description")
                else:
                    print("Could not find return value section")
            else:
                print("Could not find main content")
        else:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    test_fetch() 
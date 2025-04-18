#/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from bs4 import element
import json
import sys

domain = "https://learn.microsoft.com"

# update this list and run this script to update .json files
paths = {
	"shellapi" :          "/en-us/windows/win32/api/shellapi/",
	"winuser"  :          "/en-us/windows/win32/api/winuser/",
	"heapapi"  :          "/en-us/windows/win32/api/heapapi/",
	"processthreadsapi" : "/en-us/windows/win32/api/processthreadsapi/",
	"stringapiset" :      "/en-us/windows/win32/api/stringapiset/",  # For MultiByteToWideChar, WideCharToMultiByte, etc.
	"shlwapi" :           "/en-us/windows/win32/api/shlwapi/",       # For StrCpy, StrCat, etc.
	"winbase" :           "/en-us/windows/win32/api/winbase/"        # For lstrlen, lstrcpy, etc.
}

data = {
	"functions" : []
}

def hex_to_int(s):
	assert(s.startswith("0x"))
	return int(s.replace("U", "").replace("L", ""), 16)

def get_suffix_num(s):
	i = len(s) - 1
	while s[i] in '0123456789':
		i -= 1
	return s[i+1:] if i < len(s) - 1 else ""

# as BeautifulSoup does not provide this functionality, we implement this ourselves
def sibling_tag(i):
	i = i.next_sibling
	while i and not isinstance(i, element.Tag):
		i = i.next_sibling
	return i if isinstance(i, element.Tag) else None

def request_site(site):
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
	}
	req = requests.get(site, headers=headers)
	if req.status_code != 200:
		print(f"Error: Failed to fetch {site} (status code: {req.status_code})")
	return BeautifulSoup(req.text, 'html.parser')

# function fetch limit
function_limit = 99990

def fetch_function(site, f_name):
	global function_limit
	if function_limit == 0:
		return
	function_limit -= 1

	func_data = {
		"name" : f_name,
		"return_type" : "",
		"msdn" : site,
		"description" : "",
		"parameters" : []
	}

	try:
		soup = request_site(site)
		m = soup.find("main")
		if not m:
			return None

		# Parse function description
		desc = m.find("h1")
		if desc:
			i = desc.find_next_sibling("p")
			if i:
				func_data["description"] = i.text.strip()

		# Parse return value
		ret_val = m.find("h2", string="Return value")
		if ret_val:
			i = ret_val.find_next_sibling("p")
			if i and "Type:" in i.text:
				func_data["return_type"] = i.text.replace("Type: ", "").strip()

		# Parse function parameters
		params = m.find("h2", string="Parameters")
		if not params:  # function has no parameters
			return func_data

		param_section = params.find_next_sibling("dl")
		if param_section:
			for dt in param_section.find_all("dt"):
				param_data = {
					"name" : "",
					"type" : "",
					"description" : "",
					"possible_constants" : []
				}

				p_name = dt.text.strip()
				param_data["name"] = p_name

				dd = dt.find_next_sibling("dd")
				if dd:
					type_p = dd.find("p", string=lambda x: x and x.startswith("Type:"))
					if type_p:
						param_data["type"] = type_p.text.replace("Type: ", "").strip()

					desc_p = dd.find_all("p")[-1]
					if desc_p:
						param_data["description"] = desc_p.text.strip()

					# Look for possible constants in tables
					tables = dd.find_all("table")
					for table in tables:
						if table.tr and table.tr.th and "Value" in table.tr.th.text:
							rows = table.find_all("tr")[1:]
							for row in rows:
								tds = row.find_all("td")
								if len(tds) >= 2:
									const_name = tds[0].text.strip()
									const_value = -1
									try:
										if const_name.startswith("0x"):
											const_value = hex_to_int(const_name)
										else:
											const_value = int(const_name)
									except:
										pass
									param_data["possible_constants"].append([const_name, const_value])

				func_data["parameters"].append(param_data)

		return func_data
	except Exception as e:
		print(f"Error processing {f_name}: {str(e)}")
		return None

def main():
	total_functions = 0
	total_processed = 0
	total_to_process = 0
	
	# First pass to count total functions
	for file, path in paths.items():
		soup = request_site(domain + path)
		m = soup.find("main")
		if not m:
			continue
		functions_h2 = m.find("h2", string="Functions")
		if not functions_h2:
			continue
		functions_table = functions_h2.find_next("table")
		if not functions_table:
			continue
		total_to_process += len(functions_table.find_all("a"))
	
	print(f"Total functions to process: {total_to_process}")
	
	# Second pass to process functions
	for file, path in paths.items():
		data["functions"] = []  # Reset functions for each file
		
		soup = request_site(domain + path)
		m = soup.find("main")
		if not m:
			continue

		functions_h2 = m.find("h2", string="Functions")
		if not functions_h2:
			continue

		functions_table = functions_h2.find_next("table")
		if not functions_table:
			continue

		for a in functions_table.find_all("a"):
			if a.get('href'):
				func_url = domain + a['href'] if a['href'].startswith('/') else a['href']
				func_data = fetch_function(func_url, a.text.strip())
				if func_data:
					data["functions"].append(func_data)
				total_processed += 1
				sys.stdout.write(f"\rProgress: {total_processed}/{total_to_process} functions processed")
				sys.stdout.flush()

		# Save the data
		output_file = f"./data/{file}.json"
		with open(output_file, "w") as f:
			json.dump(data, f, indent=4)
		total_functions += len(data['functions'])

	print(f"\nCrawl completed. Total functions saved: {total_functions}")

if __name__ == '__main__':
	main()
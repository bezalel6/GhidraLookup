#/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from bs4 import element
import json
import sys
import time
import re
from typing import Optional, Dict, List, Any, Tuple

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

def hex_to_int(s: str) -> int:
	assert(s.startswith("0x"))
	return int(s.replace("U", "").replace("L", ""), 16)

def get_suffix_num(s: str) -> str:
	i = len(s) - 1
	while s[i] in '0123456789':
		i -= 1
	return s[i+1:] if i < len(s) - 1 else ""

def sibling_tag(i: element.Tag) -> Optional[element.Tag]:
	i = i.next_sibling
	while i and not isinstance(i, element.Tag):
		i = i.next_sibling
	return i if isinstance(i, element.Tag) else None

def request_site(site: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
	}
	
	for attempt in range(max_retries):
		try:
			req = requests.get(site, headers=headers)
			if req.status_code == 200:
				return BeautifulSoup(req.text, 'html.parser')
			elif req.status_code == 429:  # Too Many Requests
				wait_time = min(2 ** attempt, 8)  # Exponential backoff
				print(f"Rate limited. Waiting {wait_time} seconds...")
				time.sleep(wait_time)
				continue
			else:
				print(f"Error: Failed to fetch {site} (status code: {req.status_code})")
		except Exception as e:
			print(f"Error during request: {str(e)}")
			if attempt < max_retries - 1:
				time.sleep(1)
				continue
	return None

def parse_function_signature(code_block: str) -> Tuple[str, Dict[str, str]]:
	"""Parse a function signature to extract return type and parameter types."""
	return_type = ""
	param_types = {}
	
	# Clean up the code block and split into lines
	lines = [line.strip() for line in code_block.split('\n') if line.strip()]
	if not lines:
		return return_type, param_types
	
	# First line contains return type and function name
	first_line = lines[0]
	if '(' in first_line:
		return_part = first_line.split('(')[0].strip()
		words = return_part.split()
		if len(words) > 1:  # Return type should be everything before the last word (function name)
			return_type = ' '.join(words[:-1])
	
	# Process parameter lines
	for line in lines[1:]:  # Skip the first line (function name)
		if line.startswith(');'):  # End of function signature
			break
			
		# Remove parameter attributes [in, optional] etc.
		if '[' in line and ']' in line:
			line = line[line.rfind(']')+1:].strip()
			
		# Remove trailing comma if present
		if line.endswith(','):
			line = line[:-1].strip()
			
		# Split remaining line into words, handling multiple spaces
		parts = [p for p in line.split() if p]
		if len(parts) >= 2:
			param_name = parts[-1]  # Last word is the parameter name
			# Join all words before the last one as the type, preserving special attributes
			param_type = ' '.join(parts[:-1])
			# Clean up any remaining parameter attributes
			param_type = re.sub(r'_In_NLS_string_\([^)]+\)', '', param_type).strip()
			param_types[param_name] = param_type
	
	return return_type, param_types

def extract_parameter_info(param_section: element.Tag) -> List[Dict[str, Any]]:
	parameters = []
	
	# Find all parameter rows in the table
	rows = param_section.find_all('tr')
	if not rows:
		return parameters
		
	# Skip header row
	for row in rows[1:]:
		cells = row.find_all(['td', 'th'])
		if len(cells) < 2:
			continue
			
		# Check if this is a parameter or a flag value
		param_name = cells[0].text.strip()
		param_desc = cells[1].text.strip() if len(cells) > 1 else ""
		
		# If the description starts with "Ignore" or "Treat", it's likely a flag value
		if param_desc.lower().startswith(("ignore", "treat", "do not")):
			continue
			
		param_data = {
			"name": param_name,
			"type": "",
			"description": param_desc,
			"possible_constants": []
		}
		
		# Look for possible constants in tables within the description
		tables = cells[1].find_all("table") if len(cells) > 1 else []
		for table in tables:
			if table.tr and table.tr.th and "Value" in table.tr.th.text:
				for const_row in table.find_all("tr")[1:]:
					const_cells = const_row.find_all("td")
					if len(const_cells) >= 2:
						const_name = const_cells[0].text.strip()
						const_value = -1
						try:
							if const_name.startswith("0x"):
								const_value = hex_to_int(const_name)
							else:
								const_value = int(const_name)
						except (ValueError, AssertionError):
							pass
						param_data["possible_constants"].append([const_name, const_value])
		
		parameters.append(param_data)
	
	return parameters

def fetch_function(site: str, f_name: str) -> Optional[Dict[str, Any]]:
	print(f"\nFetching function: {f_name} from {site}")
	
	func_data = {
		"name": f_name,
		"return_type": "",
		"msdn": site,
		"description": "",
		"parameters": [],
		"flags": []
	}
	
	soup = request_site(site)
	if not soup:
		print(f"Failed to fetch page for {f_name}")
		return None
		
	main = soup.find("main")
	if not main:
		print(f"Could not find main content for {f_name}")
		return None
	
	# Extract function description
	h1 = main.find("h1")
	if h1:
		desc = h1.find_next_sibling("p")
		if desc:
			func_data["description"] = desc.text.strip()
	
	# Extract function signature and parameter types
	syntax_section = main.find("h2", string="Syntax")
	if syntax_section:
		code_block = syntax_section.find_next("pre")
		if code_block:
			code_text = code_block.get_text()
			return_type, param_types = parse_function_signature(code_text)
			func_data["return_type"] = return_type
			
			# Create parameter entries for all parameters found in signature
			for name, type_str in param_types.items():
				func_data["parameters"].append({
					"name": name,
					"type": type_str,
					"description": "",
					"possible_constants": []
				})
	
	# Extract parameters descriptions
	params_section = main.find("h2", string="Parameters")
	if params_section:
		# Look for parameter descriptions in paragraphs
		current = params_section.find_next_sibling()
		current_param = None
		param_desc = []
		
		while current and current.name != "h2":
			if current.name == "p":
				text = current.text.strip()
				if text:
					# Check if this paragraph starts with a parameter name
					for param in func_data["parameters"]:
						if text.startswith(f"[in") and param["name"] in text:
							# If we were collecting description for a previous parameter, save it
							if current_param and param_desc:
								current_param["description"] = " ".join(param_desc)
							# Start collecting description for this parameter
							current_param = param
							param_desc = []
							break
						elif text.startswith(param["name"]):
							# If we were collecting description for a previous parameter, save it
							if current_param and param_desc:
								current_param["description"] = " ".join(param_desc)
							# Start collecting description for this parameter
							current_param = param
							param_desc = [text[len(param["name"]):].strip()]
							break
					else:
						# If we're collecting description for a parameter, append this line
						if current_param:
							param_desc.append(text)
			elif current.name == "table":
				# If we find a table, it might be the flags table
				if current.tr and current.tr.th and "Flag" in current.tr.th.text:
					# Process flags table
					for row in current.find_all("tr")[1:]:  # Skip header
						cells = row.find_all(['td', 'th'])
						if len(cells) >= 2:
							dl = cells[0].find("dl")
							name = dl.find("dt").text.strip() if dl and dl.find("dt") else cells[0].text.strip()
							desc = cells[1].text.strip()
							if desc.lower().startswith(("ignore", "treat", "do not", "use", "windows")):
								func_data["flags"].append({
									"name": name,
									"description": desc,
									"value": -1
								})
			current = current.find_next_sibling()
			
		# Save the last parameter description if any
		if current_param and param_desc:
			current_param["description"] = " ".join(param_desc)
	
	return func_data

def main():
	total_functions = 0
	total_processed = 0
	total_to_process = 0
	
	# First pass to count total functions
	for file, path in paths.items():
		soup = request_site(domain + path)
		if not soup:
			continue
			
		functions_h2 = soup.find("h2", string="Functions")
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
		if not soup:
			continue
			
		functions_h2 = soup.find("h2", string="Functions")
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
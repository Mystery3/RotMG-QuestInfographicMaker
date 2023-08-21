import aiohttp, asyncio, json, os, re
import xml.etree.ElementTree as ET

# checks for required folders, returns folders that were missing (need filling)
def check_folders() -> None | list[str]:
    required_folders = ['./bin',
                        './bin/helpers',
                        './bin/xml',
                        './bin/sheets',
                        './bin/json',
                        './bin/icons'
                        ] # order of these is important so bin gets restored first
    folders_made = []

    for folder in required_folders:
        if not os.path.exists(folder):
            os.mkdir(folder)
            folders_made.append(folder)

    if folders_made != []:
        return folders_made
    
# checks for required files, returns files (need reinstalling by user if missing)
def check_files() -> None | list[str]:
    required_files = ['./bin/helpers/render.py',
                      './bin/helpers/ui.py',
                      './bin/config.json',
                      './bin/json/master.json',
                      './bin/title.ttf',
                      './bin/template.png',
                      './bin/icons/Arrow.png',
                      './bin/icons/Chooseable.png',
                      './bin/icons/Repeatable.png',
                      './bin/icons/Once Per Account.png',
                      './bin/icons/Once Per Day.png',
                      './bin/icons/Once Per Week.png'
                      ] # doesn't check for load.py and main.py for obvious reasons
    files_missing = []

    for folder in required_files:
        if not os.path.exists(folder):
            files_missing.append(folder)

    if files_missing != []:
        return files_missing

# for async downloading, takes a session and a url and returns the body of the response
async def fetch(session: aiohttp.ClientSession, url: str) -> bytes:
    async with session.get(url) as response:
        return await response.read()

# fills xml folder with files from config file
async def download_xml_async(session: aiohttp.ClientSession) -> None:
    with open('./bin/config.json', 'r') as f:
        config = json.load(f)
    
    tasks = []

    for url in config['XML URLs']:
        tasks.append(fetch(session, url))
    contents = await asyncio.gather(*tasks)

    for content, url in zip(contents, config['XML URLs']):
        with open(f'./bin/xml/{url.rpartition("/")[2]}', 'wb') as f:
            f.write(content)

# IGNORES 32x32 SKINS (for now)
# one file; generates a json file from an xml file (key is object name, values include file, index, size, quantity). returns the dictionary generated too
def parse_xml(path: str, write = True) -> dict[str:str | int]:
    parsed = {}

    objects = ET.parse(path).getroot()

    for object in objects:
        object_names = []
        if object.find('DisplayId') != None: # include the DisplayId if there is one
            if not object.find('DisplayId').text in parsed.keys(): # for shinies overriding normal items
                object_names.append(object.find('DisplayId').text)

        object_names.append(object.attrib['id'])

        for texture_type in ('Texture', 'AnimatedTexture'): # check if there is a Texture or AnimatedTexture tree, define texture as whichever tree is found
            if (texture := object.find(texture_type)):
                break
        else: # if neither is found, this object shouldn't be parsed (it has no texture)
            continue

        file, index_text = texture[0].text, texture[1].text # texture[0] should contain the sheet name, texture[1] should contain the index

        if index_text.startswith('0x'): # in base 16 IF it starts with 0x
            index = int(index_text[2:], base=16)
        else:
            index = int(index_text)
        
        if file.startswith('player'):
            index = index * 21
        elif 'pets' in file or 'Pets' in file:
            index = index * 7

        if '32' in file:
            size = 32
        elif 'big' in file.lower() or 'divine' in file.lower() or '16' in file: # big or divine (for pet skins) indicates 16x16
            size = 16
        else:
            size = 8
        
        quantity_match = re.search(r' x ?(\d*)$', object_names[0]) # find quantity in first Id (displayId takes priority), matches ' ' then x then optional ' ' then any digits before the end
        if quantity_match:
            quantity = int(quantity_match.group(1))
        else:
            quantity = 0
        
        activate = object.find('Activate')
        contained_items = []
        if activate != None and activate.text == 'UnlockForgeBlueprint':
            contained_items = activate.attrib['id'].split(',')

        for object_name in object_names:
            parsed[object_name] = {}
            parsed[object_name]['File'] = file
            parsed[object_name]['Index'] = index
            parsed[object_name]['Size'] = size
            parsed[object_name]['Quantity'] = quantity
            parsed[object_name]['Contained'] = contained_items
    
    if write:
        with open(f'./bin/json/{path.rpartition("/")[2].removesuffix(".xml")}.json', 'w') as f:
            json.dump(parsed, f, indent=4, ensure_ascii=False)
    
    return parsed

# parses all xml and merges json files into one (master.json)
def parse_all() -> None:
    files = os.listdir('./bin/xml')
    
    master_dict = {}
    
    for file in files:
        parsed = parse_xml(f'./bin/xml/{file}')
        
        master_dict = master_dict | parsed
    
    with open('./bin/json/master.json', 'w') as f:
        json.dump(master_dict, f, indent=4, ensure_ascii=False)   

# fills sheets folder with url from config file and master.json (needs master.json, use after parse_all)
async def download_sheets_async(session: aiohttp.ClientSession) -> None:
    # first part for getting required sheets to not download all of them
    sheets = set() # {} is interpreted as an empty dict before an empty set

    master_dict = get_master_dict()
    
    for key in master_dict:
        sheets.add(master_dict[key]['File'])
    
    if 'custom8x8' in sheets: # exception for custom items
        sheets.remove('custom8x8')
    if 'custom16x16' in sheets:
        sheets.remove('custom16x16')
    if 'custom32x32' in sheets:
        sheets.remove('custom32x32')

    # this part is similar to download_xml()
    with open('./bin/config.json', 'r') as f:
        config = json.load(f)
    
    tasks = []

    for sheet in sheets:
        tasks.append(fetch(session, f'{config["Sheet URL"]}{sheet}.png'))
    contents = await asyncio.gather(*tasks)

    for content, sheet in zip(contents, sheets):
        with open(f'./bin/sheets/{sheet}.png', 'wb') as f:
            f.write(content)

# downloads xml, parses it, downloads sheets
async def setup() -> None:
    async with aiohttp.ClientSession() as session:
        await download_xml_async(session)
        parse_all()
        await download_sheets_async(session)

# returns a dict with keys "File", "Index", "Size", "Quantity"; "File" is a string, the rest are ints
def get_master_dict() -> dict[str:str | int]:
    with open('./bin/json/master.json', 'r') as f:
        master_dict = json.load(f)
    return master_dict

def get_config() -> dict[str: str| int]:
    with open('./bin/config.json', 'r') as f:
        config = json.load(f)
    return config

# updates 1 key with a new value
def update_config(key:str, value: str | int):
    config = get_config()

    config[key] = value

    with open('./bin/config.json', 'w') as f:
        json.dump(config, f, indent = 4, ensure_ascii = False)

# possibly redundant
# for toggling config options between 1 and 0
def toggle_config_option(key: str):
    config = get_config()

    if config[key] == 1: config[key] = 0
    else: config[key] = 1
    
    with open('./bin/config.json', 'w') as f:
        json.dump(config, f, indent = 4, ensure_ascii = False)
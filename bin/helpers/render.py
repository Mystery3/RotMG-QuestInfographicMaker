import PIL.Image as Img
import PIL.ImageFilter as Filter
import PIL.ImageDraw as Draw
import PIL.ImageFont as Font
import json

with open('./bin/config.json', 'r') as f:
    config = json.load(f)

UPSCALE = config['Upscale']
LARGE_SIZE = config['Large Size']
SMALL_SIZE = config['Small Size']
BLUEPRINT_SIZE = config['Blueprint Size']
QUANTITY_FONTSIZE = config['Quantity Font Size']

def get_sprite_from_sheet(sheet_name: str, index: int, size: int) -> Img.Image:
    sheet = Img.open(f'./bin/sheets/{sheet_name}.png')

    column_count = int(sheet.size[0] / size) # should always be divisble w/o remainder
    column = index % column_count
    row = index // column_count

    top_left = (column * size, row * size)
    bottom_right = (column * size + size, row * size + size)

    return sheet.crop((*top_left, *bottom_right)).convert('RGBA')

def create_silhouette(image: Img.Image) -> Img.Image:
    x = image.size[0]
    silhouette = image.copy()

    for i, pixel in enumerate(image.getdata()):
        position = (i % x, i // x) # column, row
        if pixel[3] != 0: # put black pixels on pixels with non-zero alpha values
            silhouette.putpixel(position, (0, 0, 0, 255))

    return silhouette

# upscale, shadow, outline, and quantity; upscale is 1 pixel in original image -> upscale# of pixels in final image
def render_one_sprite(image: Img.Image, quantity: int, upscale=UPSCALE) -> Img.Image:
    width, height = image.size # width and height are in unaltered pixels (ie 8x8 or 16x16)

    base_image = Img.new('RGBA', ((width + 2) * upscale, (height + 2) * upscale), (0, 0, 0, 0)) # transparent bg w/ a 1 pixel margin on all sides

    silhouette = create_silhouette(image).resize((width * upscale, height * upscale), resample = Img.BOX)

    base_image.alpha_composite(silhouette, (upscale, upscale))
    base_image = base_image.filter(Filter.GaussianBlur(radius = upscale / 2)) # blur silhouette to make the shadow
    base_image.alpha_composite(silhouette, (upscale, upscale))
    base_image = base_image.filter(Filter.GaussianBlur(radius = upscale / 4)) # do it twice to make it darker (better  way???) 

    for i in (-1, 1):
        for j in (-1, 1):
            base_image.alpha_composite(silhouette, (upscale + i, upscale + j)) # silhouette
    
    base_image.alpha_composite(image.resize((width * upscale, height * upscale), resample = Img.BOX), (upscale, upscale))

    if not quantity: # return image if quantity is 0
        return base_image
    
    base_image_draw = Draw.Draw(base_image) # adding quantity
    base_image_draw.fontmode = '1'

    # rendering this number before resizing sometimes makes artifacts in the number's outline, but they do not affect readability of the number or the sprite
    image_font = Font.truetype('./bin/quantity.ttf', QUANTITY_FONTSIZE)

    for i in (-1, 1):
        for j in (-1, 1):
            base_image_draw.text(xy = (1 + i, 1 + j), text = str(quantity), font = image_font, fill = 'black') # text outline
    base_image_draw.text(xy = (1, 1), text = str(quantity), font = image_font, fill = 'white')

    return base_image

def paste_contained_item(master_dict: dict[str: str | int], base_image: Img.Image, contained_names: list[str]) -> None:
    for index, contained_name in enumerate(contained_names):
        item_dict = master_dict[contained_name]
        contained_image = render_one_sprite(get_sprite_from_sheet(item_dict['File'], item_dict['Index'], item_dict['Size']), item_dict['Quantity'], upscale = UPSCALE // 2)
        contained_image.resize((BLUEPRINT_SIZE, BLUEPRINT_SIZE))
        base_image.alpha_composite(contained_image, (0,(base_image.size[0] - BLUEPRINT_SIZE) // len(contained_names) * index))

# 160x80 with images centered in rows of 4
def generate_image_group(images: list[Img.Image]) -> Img.Image :
    image_number = len(images)

    if image_number > 8:
        raise Exception(f'Too many values in images: {images}')
    elif image_number < 2:
        render_size = LARGE_SIZE
    else:
        render_size = SMALL_SIZE

    base_image = Img.new('RGBA', (160, 80), (0, 0, 0, 0))
    sized_images = [image.resize((render_size, render_size), resample = Img.BOX) for image in images]

    rows = []
    for i in range(image_number)[::4]: # every fourth -> one iteration per row
        rows.append(sized_images[i:i + 4])
        
    start_position_y = int(40 - 0.5 * len(rows) * render_size) # starting from the middle (40) and moves it up by half of the size of the required images

    for row_number, row_images in enumerate(rows):
        start_position_x = int(80 - 0.5 * len(row_images) * render_size) # starting from the middle (80) and moves it up by half of the size of the required images
        position_y = start_position_y + row_number * render_size
        
        for i, image in enumerate(row_images):
            position_x = start_position_x + i * render_size
            position = (position_x, position_y)
            base_image.alpha_composite(image, position)
            
    return base_image

# ignore margin should be 10 for infographics
def combine_images_vertically(images: list[Img.Image], ignore_margin: int) -> Img.Image:
    base_image_x = max([image.size[0] for image in images]) # highest width is base image width
    base_image_y = sum([image.size[1] for image in images]) - ignore_margin * (len(images) - 1) # total the height, but subtract each overlap
    base_image_size = (base_image_x, base_image_y)
    base_image = Img.new('RGBA', base_image_size, (0, 0, 0, 0))

    height = 0
    for image in images:
        image_position = (0, height)
        base_image.paste(image, image_position) # paste instead of alpha composite here to avoid semi-transparent frame stacking
        height+= image.size[1] - ignore_margin
    
    return base_image

# input should be the master dict and a list of dicts with keys 'Input', 'Output', 'Title', 'Icon', and 'Chooseable'
def generate_infographic(master_dict: dict[str: str | int], entries: list[dict[str: str | bool]]) -> Img.Image:
    template_image = Img.open('./bin/template.png').convert('RGBA')
    
    infographics = []

    for entry in entries:
        input_image_names = entry['Input'] # prefer to keep these separate, though it might look redundant
        output_image_names = entry['Output'] # these are lists of names, the ui module separates them in app.get_quest_info
        
        input_images = []
        output_images = []

        for name in input_image_names:
            item_dict = master_dict[name]
            sprite = render_one_sprite(get_sprite_from_sheet(item_dict['File'], item_dict['Index'], item_dict['Size']), item_dict['Quantity'])
            if item_dict['Contained'] != []:
                paste_contained_item(master_dict, sprite, item_dict['Contained'])
            input_images.append(sprite)
        
        for name in output_image_names:
            item_dict = master_dict[name]
            sprite = render_one_sprite(get_sprite_from_sheet(item_dict['File'], item_dict['Index'], item_dict['Size']), item_dict['Quantity'])
            if item_dict['Contained'] != []:
                paste_contained_item(master_dict, sprite, item_dict['Contained'])
            output_images.append(sprite)

        input_image = generate_image_group(input_images)
        output_image = generate_image_group(output_images)

        infographic_image = template_image.copy()
        infographic_image_draw = Draw.Draw(infographic_image)

        image_font = Font.truetype('./bin/title.ttf', 26)
        
        infographic_image_draw.text(xy = (10, 13), text = entry['Title'], font = image_font, fill = 'gray', stroke_width = 1, stroke_fill = 'black')
        infographic_image_draw.text(xy = (10, 11), text = entry['Title'], font = image_font, fill = 'white', stroke_width = 1, stroke_fill = 'black')

        icon = Img.open(f'./bin/icons/{entry["Icon"]}.png').convert('RGBA')
        icon_position = (int(image_font.getlength(entry['Title'])) + 16, 7)
        infographic_image.alpha_composite(icon, icon_position)

        if entry['Chooseable']:
            chooseable_icon = Img.open(f'./bin/icons/Chooseable.png').convert('RGBA')
            chooseable_icon_x = icon_position[0] + 37
            infographic_image.alpha_composite(chooseable_icon, (chooseable_icon_x, 5))

        infographic_image.alpha_composite(input_image, (15, 54))
        infographic_image.alpha_composite(output_image, (225, 54))

        infographics.append(infographic_image)
    
    if len(infographics) > 1:
        return combine_images_vertically(infographics, 10)
    
    return infographics[0]
import requests
from PIL import Image, ImageDraw, ImageFont
import uuid
import os


def convert_text(text):
    words_to_remove = ['ملاحظات اخرى:','ملاحظات اخرى :','نوع السيارة:', 'نوع السيارة :','وارد او خليجي :', 'كم سلندر:','كم سلندر :'
                         ,'الموديل :','نوع السياره :', 'نوع السياره :', 'نوع السياره:','الموديل:', 'وارد أو خليجى:',
                       'وارد أو خليجي :', 'وارد او خليجى:',
                       'Car Type:', 'Model:', 'Mileage:', 'Gulf or imported:', 'Number of Cylinders:', 'National distance:','نوع سياره:'
                       'Imported or Gulf:', 'Type of car:', 'How many cylinders:', 'Other notes:', 'Car type:', 'Walkway:']

    def remove_words(text, words_to_remove):
        for word in words_to_remove:
            text = text.replace(word, '')
        return text

    def merge_first_three_lines(text):
        lines = text.splitlines()
        merged_line = " ".join(lines[:3])
        remaining_lines = lines[3:]
        result_text = "\n".join([merged_line] + remaining_lines)
        return result_text

    text = remove_words(text, words_to_remove)
    text = merge_first_three_lines(text)

    if len(text)>200:
        max_wrds_in_line = 5
    else:
        max_wrds_in_line = 5


    lines = text.split("\n")
    new_lines = []

    for line in lines:
        words = line.split()
        while len(words) > max_wrds_in_line:
            new_lines.append(' '.join(words[:max_wrds_in_line]))
            words = words[max_wrds_in_line:]
        new_lines.append(' '.join(words))
    text = "\n".join(new_lines)

    return text


def translate(language, content):
    if language == "ar":
        source = 'ar'
        target = 'en'
        co_text = content.replace('وارد', 'مستورد')
    elif language == "en":
        source = 'en'
        target = 'ar'
        co_text = content
    else:
        return 'no translation'

    url = "https://deep-translate1.p.rapidapi.com/language/translate/v2"
    payload = {
        "q": co_text,
        "source": source,
        "target": target
    }
    headers = {
        "x-rapidapi-key": "8caeb9741amshaccc7f5fd9925d3p1bb4b6jsne76d30e29c62",
        "x-rapidapi-host": "deep-translate1.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    text = response.json()['data']['translations']['translatedText']
    text = text.replace('negotiable To negotiate', 'negotiable')
    text = text.replace('negotiable to negotiate', 'negotiable')
    text = text.replace('kilos', 'KM')
    text = text.replace('The location of the car', 'location')
    text = text.replace( 'brought to America','American import')
    text = text.replace( 'He came to', 'imported')
    text = text.replace('Walkway:', '')
    text = text.replace('Mileage:', '')
    # print(text)
    return text


def extract_text_to_keyword(text, keyword):
    lines = text.strip().split('\n')

    try:
        index = next(i for i, line in enumerate(lines) if keyword in line)
        extracted_text = '\n'.join(lines[:index + 1])
        return extracted_text
    except StopIteration:
        return text


def draw_multiline_text(draw, position, text, font, fill, line_height=30, max_width=20, align="left"):
    lines = text.split('\n')
    x, y = position
    for line in lines:
        if align == "center" and max_width:
            line_width = draw.textlength(line, font=font)
            x = position[0] + (max_width - line_width) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height


def process_data(template, language, text, photo_paths):
    downloads_path = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(downloads_path):
        os.makedirs(downloads_path)

    file_name = str(uuid.uuid4()) + '.png'
    output_path = os.path.join(downloads_path, file_name)

    if language == "Arabic":
        first_text = convert_text(text)
        second_text = translate('ar', convert_text(extract_text_to_keyword(text, 'رقم التواصل')))
        second_text = second_text.replace('thousand kilometers', 'KM')
        second_text = second_text.replace('Contact number', 'Contact')
        # first_text = merge_first_three_lines(first_text)
        # second_text = merge_first_three_lines(second_text)

    elif language == "English":
        first_text = convert_text(text)
        # print(first_text.count('\n'))
        second_text = translate('en', convert_text(extract_text_to_keyword(text, 'Contact number')))
        # first_text = merge_first_three_lines(first_text)
        # second_text = merge_first_three_lines(second_text)

    else:
        return 'no translation'

    print(first_text)
    print(second_text)

    if template == 'VIP':
        template_path = os.path.join(os.getcwd(), 'temp/vip3.png')
    elif template == 'مميز':
        template_path = os.path.join(os.getcwd(), 'temp/special3.png')
    elif template == 'مجاني':
        template_path = os.path.join(os.getcwd(), 'temp/free3.png')
    else:
        return 'wrong template'

    base_image = Image.open(template_path)
    width, height = base_image.size
    new_image = Image.new('RGB', (width, height), 'white')
    new_image.paste(base_image, (0, 0))

    num_photos = len(photo_paths)
    padding = 20

    photo_width = width // 2 + 7
    photo_height = height - 2 * padding

    if num_photos == 1:
        photo = Image.open(photo_paths[0])
        photo = photo.resize((photo_width, photo_height), Image.LANCZOS)
        new_image.paste(photo, (padding, padding))
    else:
        photo_height = (height - 2 * padding) // num_photos

        for i, photo_path in enumerate(photo_paths):
            photo = Image.open(photo_path)
            photo = photo.resize((photo_width, int(photo.height * photo_width / photo.width)), Image.LANCZOS)

            if photo.height > photo_height:
                excess_height = photo.height - photo_height
                crop_top = (2 * excess_height) // 3
                crop_bottom = excess_height // 3
                crop_area = (0, crop_top, photo_width, photo.height - crop_bottom)
                photo = photo.crop(crop_area)

            padding_top = padding + i * photo_height
            new_image.paste(photo, (padding, padding_top))

    draw = ImageDraw.Draw(new_image)
    print(len(first_text))
    if len(first_text) > 200:
        font_size = 32
        line_height = 37
    else:
        font_size = 34
        line_height = 45

    bold_font = ImageFont.truetype("Montserrat-Arabic ExtraBold 800.otf", font_size)

    lines = first_text.count('\n')
    # p = 0.05
    if lines<7:
        p = 0.12
    elif lines==7:
        p=0.1
    elif lines==8:
        p = 0.08
    elif lines==9:
        p = 0.045
    elif lines > 10 and len(first_text) > 200:
        p = 0.05
    elif lines > 8 and len(first_text) <= 200:
        p = 0.06
    else:
        p = 0.1
    print(p)
    print(lines)


    arabic_text_position = (int(width * 0.57), int(height * p))
    english_text_position = (int(width * 0.57), int(height * 0.6))
    max_width = width * 0.4

    draw_multiline_text(draw, arabic_text_position, first_text, bold_font, fill="black", line_height=line_height,
                        max_width=max_width, align="center")
    draw_multiline_text(draw, english_text_position, second_text, bold_font, fill="black", line_height=line_height,
                        max_width=max_width, align="center")

    new_image.save(output_path)
    post = first_text + "\n\n" + second_text
    return output_path, post

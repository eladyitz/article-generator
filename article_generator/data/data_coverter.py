import nltk
import pandas as pd
from random import randint
import os
from PIL import Image
import math
from alive_progress import alive_bar


class DataConverter:
    def __init__(self, excelPath):
        self.symbol_to_color_dict = {}
        self.color_to_symbol_dict = {}
        self.color_palate = set()
        self.excel_data = pd.read_excel(excelPath)
        self.excel_path = excelPath
        self.tokenized_text = self._tokenizeText()

    def _tokenizeText(self):
        data = self.excel_data["paper_text"]
        tokenized_text = set()
        for text in data:
            tokenized_text.update([each_string.lower() for each_string in nltk.word_tokenize(text)])

        return tokenized_text

    def _getColorPalate(self, color_spectrum):
        if self.color_palate:
            return self.color_palate

        self.color_palate = set()
        while len(self.color_palate) < color_spectrum:
            # without 0x000000 (black) and is the background
            self.color_palate.add(randint(0x000001, 0xFFFFFF))

        return self.color_palate

    def getTextToColorDictionary(self):
        if self.symbol_to_color_dict:
            return self.symbol_to_color_dict

        self.color_palate = self._getColorPalate(len(self.tokenized_text))
        self.symbol_to_color_dict = dict(zip(self.tokenized_text, self.color_palate))

        return self.symbol_to_color_dict

    def getColorToTextDictionary(self):
        if self.color_to_symbol_dict:
            return self.color_to_symbol_dict

        if not self.symbol_to_color_dict:
            self.symbol_to_color_dict = self.getTextToColorDictionary

        self.color_to_symbol_dict = {v: k for k, v in self.symbol_to_color_dict.items()}
        return self.color_to_symbol_dict

    def _getImageFromColorList(self, color_list):
        image_size = int(math.ceil(math.sqrt(len(color_list))))
        # 0x000000 (black) the background
        img = Image.new('RGB', (image_size, image_size), 0x000000) # Create a new black image
        pixels = img.load() # Create the pixel map
        color_index = 0
        for i in range(image_size):    # For every pixel:
            for j in range(image_size):
                    if color_index < len(color_list):
                        color = color_list[color_index]
                        pixels[i, j] = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
                        color_index += 1
        return img

    def convertTextsToColorImages(self):
        images_file_paths = []

        with alive_bar(len(self.excel_data)) as bar:
            for index, row in self.excel_data[["paper_full_path", "paper_text"]].iterrows():
                tokenized_paper = [each_string.lower() for each_string in nltk.word_tokenize(row["paper_text"])]
                paper_color_list = [self.getTextToColorDictionary()[symbol] for symbol in tokenized_paper]
                img = self._getImageFromColorList(paper_color_list)
                image_file_name = os.path.split(row["paper_full_path"])[-1].replace(".txt", ".png")
                image_file_path = os.path.join("papers", image_file_name)
                try:
                    img.save(image_file_path)
                    images_file_paths.append(image_file_path)
                except Exception as exc:
                    images_file_paths.append("")
                bar()
        self.excel_data["image_file_path"] = images_file_paths
        self.excel_data = self.excel_data.drop(self.excel_data[self.excel_data["image_file_path"] == ""].index)
        self.excel_data.to_excel(self.excel_path)

    def convertColorImageToText(self, image_path, converted_file_path):
        text = []
        with Image.open(image_path) as img:
            pixel_values = list(img.getdata())
            for r, g, b in pixel_values:
                color = (r << 16) + (g << 8) + b
                text.append(self.getColorToTextDictionary()[color])

        text = text.join(" ")
        with open(converted_file_path, "w") as writer:
            writer.write(text)
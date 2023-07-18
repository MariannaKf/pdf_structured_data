import pandas as pd 
import numpy as np 
import string
import unicodedata
import nltk
nltk.download('punkt')
import re
from nltk.tokenize import sent_tokenize 
import fitz
import io
from PIL import Image
from table_extractor import TableExtraction


class Transform_pdf_file:

    def __init__(self,pdf_file,file_path,company_name):
        self.file_path = file_path
        self.file_path_document = pdf_file
        self.pdf_file = fitz.open(pdf_file)
        self.company_name = company_name
        
         #take only the file path to use it to save the images and pdf files
        self.file_path = file_path 
    
    def delete_images(self):

        #read_file
        file = self.pdf_file
        
       
        #delete images in the pdf file
        #take every page

        for page in range(0,len(file)):
            img_list = file.get_page_images(page)
            con_list = file[page].get_contents()

            for i in con_list:
                c = file.xref_stream(i)
                if c != None:
                    for v in img_list:
                        arr = bytes(v[7], 'utf-8')
                        r = c.find(arr)
                        if r != -1:
                            cnew = c.replace(arr, b"")
                            file.update_stream(i, cnew)
                            c = file.xref_stream(i)

        self.pdf_file = file

    def transform_pdf_to_images(self):
        
        for i, page in enumerate(self.pdf_file):
            
            pix = page.get_pixmap()  # render page to an image
                
            
            pix.save('page{}.jpg'.format(i), 'JPEG')
    
    def detect_tables(self):
        
        
        for page_index in range(0,len(self.pdf_file)):
  
            TableExtraction(self.file_path,page_index).cleaned_page()
        
    
    def subtract_files(self,file1_path, file2_path, output_path,encoding='utf-8-sig'):
        # Read the content of both files into separate lists
        with open(file1_path, 'r',encoding=encoding) as file1:
            content_file1 = file1.read().splitlines()

        with open(file2_path, 'r',encoding=encoding) as file2:
            content_file2 = file2.read().splitlines()

        # Subtract the content of file2 from file1
        result_content = [line for line in content_file1 if line not in content_file2]

        # Save the result to the output file
        with open(output_path, 'w',encoding=encoding) as output_file:
            output_file.write("\n".join(result_content))

    
    def subtract_tables_sentences_from_pdf(self):
        #sentences from pdf
        textFile = self.company_name + '.txt'
        text = ''

        f = open(textFile, "w",encoding ='utf-8-sig')
        for i in range(len(self.pdf_file)):
            # creating a page object 
            page = self.pdf_file[i] 
            

            f.write(page.get_text())
        f.close()
        
        #sentences from table
        
        table_file = fitz.open(self.file_path + "/tables_pdf.pdf")
        textFile = self.company_name + '_table.txt'
        text = ''

        f = open(textFile, "w",encoding ='utf-8-sig')
        for i in range(len(table_file)):
            # creating a page object 
            page = self.pdf_file[i] 
            

            f.write(page.get_text())
        f.close()
        
        self.subtract_files(self.company_name + '.txt',self.company_name + '_table.txt',self.company_name + '_cleaned.txt') 
        
        
    def contains_multiple_spaces(self,s):

        return bool(re.search(r' {2,}', s))

    def find_spaces_position(self,s):

        if re.search(r' {2,}', s) != None:
            return re.search(r' {2,}', s).span()
        else:
            return None

    def create_sentences(self,text):
        #### complete the (i)

        for i in range(len(text)-1):

            if text[i+1][0].isupper() and text[i][-1] !='.' and len(text[i])>1:

                text[i] = text[i] + '. ' 
               
        ### complete the (ii):
        for line in text:
            #find the dot in a line
            if '.' in text:
                #find the positions of the dots
                positions = line.find('.')
                if type(positions)!=int:
                    for position in positions:

                        if len(line) < position - 1:
                            if line[position+1].isupper():
                                line = line.replace(line[position],'. ')
                else:

                    if len(line) < positions - 1:
                            if line[positions+1].isupper():
                                    line = line.replace(line[positions],'. ')
            ### complete the third option:

            if self.contains_multiple_spaces(line):

                
                line = re.sub(' +','. ',line)

        return text
    
    def filter_sentences_with_more_digits(self,sentences):

        
        filtered_sentences = []
        for sentence in sentences:
            words = re.findall(r'\b\w+\b', sentence)
            numbers = re.findall(r'\b\d+\b', sentence)
            if len(numbers) <= len(words):
                filtered_sentences.append(sentence)
        return filtered_sentences

    def create_structured_data(self):

        textFile = self.company_name + '_cleaned.txt'

        text = open(textFile, "r",encoding = 'utf-8-sig').readlines()
        text = self.create_sentences(text)

        text = ''.join(text)

        sentences = sent_tokenize(text) 

        sentences = [x.replace('\n',' ') for x in sentences]

        sentences = self.filter_sentences_with_more_digits(sentences)

        final_data = pd.DataFrame(sentences,columns = ['text'])

        #export to the final data
        final_data.to_excel('structured_data.xlsx')


    def return_structured_data_from_pdf(self):
            
        self.delete_images()
        self.transform_pdf_to_images()
        self.detect_tables()
        self.subtract_tables_sentences_from_pdf()
        self.create_structured_data()
            
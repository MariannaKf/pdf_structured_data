from PIL import Image
from transformers import DetrImageProcessor,DetrForObjectDetection
import torch
import matplotlib.pyplot as plt
import cv2
import math
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import os


class TableExtraction:
    def __init__(self, file_path,page):
        
        self.file_path = file_path
        self.page = page
        self.image = Image.open(self.file_path + '/page{}.jpg'.format(self.page)).convert("RGB")
        width, height = self.image.size
        self.image.resize((int(width*0.5), int(height*0.5)))
    
    
        self.feature_extractor = DetrImageProcessor.from_pretrained("TahaDouaji/detr-doc-table-detection")
        self.encoding = self.feature_extractor(self.image, return_tensors="pt")
        self.model = DetrForObjectDetection.from_pretrained("TahaDouaji/detr-doc-table-detection")
        
    def results(self):
        with torch.no_grad():
            outputs = self.model(**self.encoding)

        # rescale bounding boxes
        width, height = self.image.size
        results = self.feature_extractor.post_process_object_detection(outputs, threshold=0.9, target_sizes=[(height, width)])[0]

        return results
    
    def plot_results_text_only(self):
        
        plt.imshow(self.image)
        ax = plt.gca()
        
        
        results = self.results()
        if len(results['boxes'].tolist())>0:
            for score, label, (xmin, ymin, xmax, ymax) in zip(results['scores'].tolist(), results['labels'].tolist(), results['boxes'].tolist()):
                ax.add_patch(plt.Rectangle((xmin -30 , ymin -30), xmax - xmin + 10, ymax - ymin,
                                           fill=True, color='white', linewidth=3))
                
            plt.axis('off')
            plt.savefig(self.file_path+"cleaned/page_{}.png".format(self.page))
        else:
            self.image.save(self.file_path+"cleaned/page_{}.png".format(self.page))
            

            
    def bounding_box_img(self,img,bbox):
        x_min, y_min, x_max, y_max = bbox
        x_min = math.floor(x_min) - 30
        y_min = math.floor(y_min) - 30
        x_max = math.ceil(x_max) + 30
        y_max = math.ceil(y_max) + 30
        bbox_obj = img[y_min:y_max, x_min:x_max]

        return bbox_obj
    
    

    def cleaned_page(self):
        
        results = self.results()
        
        if len(results['boxes'].tolist())>0:

            for i,bbox in enumerate(results['boxes'].tolist()):

                img = cv2.imread(self.file_path + '/page{}.jpg'.format(self.page))
               
                cropped_img = self.bounding_box_img(img,bbox)
                
                cv2.imwrite(self.file_path+"/tables/page_{}_{}_table.png".format(self.page,i),cropped_img)
        
        #create a pdf file with the tables
        image_folder = self.file_path+"/tables/"
        output_pdf_path = "tables_pdf.pdf"

        self.convert_images_to_pdf(image_folder, output_pdf_path)



    def convert_images_to_pdf(self,image_folder, output_pdf_path):
        # Get a list of all files in the image folder
        image_files = [file for file in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, file))]

        # Sort the files to ensure the images are arranged in the correct order
        image_files.sort()

        # Create a new PDF document
        c = canvas.Canvas(output_pdf_path, pagesize=letter)

        # Define the page size (you can adjust this to your preference)
        page_width, page_height = letter

        # Define the margins (adjust as needed)
        left_margin = 36
        bottom_margin = 36

        # Loop through each image and add it to the PDF
        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)

            # Open the image using Pillow
            img = Image.open(image_path)

            # Calculate the image dimensions to fit within the page
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            desired_width = page_width - 2 * left_margin
            desired_height = desired_width / aspect_ratio

            # Determine if the image needs to be scaled to fit the page
            if desired_height > page_height - 2 * bottom_margin:
                desired_height = page_height - 2 * bottom_margin
                desired_width = desired_height * aspect_ratio

            # Center the image on the page
            x_offset = (page_width - desired_width) / 2
            y_offset = (page_height - desired_height) / 2

            # Draw the image on the PDF
            c.drawImage(image_path, x_offset, y_offset, width=desired_width, height=desired_height)

            # Add a new page for the next image
            c.showPage()

        # Save and close the PDF
        c.save()

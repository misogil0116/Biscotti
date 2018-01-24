import numpy as np
import cv2
import os
import pandas as pd

"""
[WIP]

this class operates the dataset.
except for load_dataset() method, other method is used for making dataset.

csv/ => dumped DCT coeffs.
qopt_images/ => images made by guetzli, and this image is only optimized quantization table, but not DCT coeffs.
labels/ => read csv(DCT coeffs), and if each coeff is not 0, set a value 1. if each coeff is 0, set a value 0.


WATCH: After guetzli, images is transformed into YUV420 or YUV444, so you can think label data Y:Cb:Cr = 4:1:1
TODO: this script doesn't accept YUV444 images.
TODO: this script doesn't accept gray scale.
"""


class Image2ImageDataset(object):
    def __init__(self):
        self.qopt_path = "qopt_images/"
        self.train_path = "train/"
        self.csv_path = "csv/"
    
    def load_dataset(self):
        """
        this function is used for training scripts.
        other functions is used for making dataset.
        """
        pass

    def dct_csv2numpy_probability(self):
        checker_0 = np.vectorize(self.check0)
        for csv_file in os.listdir(self.csv_path):
            if csv_file.startswith("."):
                continue
            csv_numpy = pd.read_csv(self.csv_path + "/" + csv_file, header=None).get_values()
            yield checker_0(csv_numpy == 0)
    
    def make_images_and_labels(self):
        """
        this method make dataset.
        now you can only make 3d(YCrCb)Dataset, so you should exclude gray scale images.
        """
        qopt_files = os.listdir(self.qopt_path)
        images = [cv2.imread(self.qopt_path + "/" + q_file) for q_file in qopt_files if not q_file.startswith(".")]
        labels = self.dct_csv2numpy_probability()
        for i in range(len(qopt_files)):
            img = images[i]
            label = next(labels)
            filename = qopt_files[i].replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
            print(filename)

            if self.check_grayscale(img, label):
                print("this image is on gray scale data!")
                continue

            if self.check_chroma_subsampling(img, label):
                print("this image is YUV444")
                continue
            
            img = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb) / 255.0
            height = img.shape[0]
            width = img.shape[1]
            height_blocks = int(height / 8)
            width_blocks = int(width / 8)
            seq = int(label.shape[0] * (2/3))

            coeff_y, coeff_cbcr = label[:seq], label[seq:]
            coeff_y = self.resize_coeff_to_img_matrix(coeff_y, width, height)
            coeff_cb = self.resize420to444(coeff_cbcr[:int(seq/4)], width, height)
            coeff_cr = self.resize420to444(coeff_cbcr[int(seq/4):], width, height)
            coeff3d = np.concatenate((coeff_y, coeff_cr, coeff_cb), axis=2)
            result = np.concatenate((img, coeff3d), axis=2)
            np.save(self.train_path + filename + ".npy", result)
            print(filename, "is done!")

    @staticmethod
    def resize_coeff_to_img_matrix(coeff, width, height):
        canvas = np.zeros((height, width))
        width_blocks = int(width / 8)
        height_blocks = int(height / 8)
        for block_y in range(height_blocks):
            for block_x in range(width_blocks):
                block_ix = height_blocks * block_y + block_x
                block = coeff[block_ix].reshape(8, 8)
                canvas[block_x*8:block_x*8+8, block_y*8:block_y*8+8] = block
        return canvas.reshape(height, width, 1)

    @staticmethod
    def check0(coeff):
        if not coeff:
            return 1
        else:
            return 0
    
    @staticmethod
    def resize420to444(coeff, width, height):
        canvas = np.zeros((height, width))
        width_blocks = int(width / 16)
        height_blocks = int(height / 16)
        for block_y in range(width_blocks):
            for block_x in range(height_blocks):
                canvas16 = np.zeros((16, 16)).astype(np.int32)
                block_ix = height_blocks * block_y + block_x
                block = coeff[block_ix].reshape(8, 8)
                for i in range(8):
                    for j in range(8):
                        dct22 = block[i][j] * np.ones((2, 2)).astype(np.int32)
                        canvas16[j*2:j*2+2, i*2:i*2+2] = dct22
                canvas[block_x*16:block_x*16+16, block_y*16:block_y*16+16] = canvas16
        return canvas.reshape(height, width, 1)

    @staticmethod
    def check_grayscale(image, label):
        return True if image.shape[0]*image.shape[1] == label.shape[0]*label.shape[1] else False
    
    @staticmethod
    def check_chroma_subsampling(image, label):
        return True if image.shape[0] * image.shape[1] * image.shape[2] == label.shape[0] * label.shape[1] else False

if __name__ == "__main__":
    print("=== making dataset... ===")
    dataset = Image2ImageDataset()
    dataset.make_images_and_labels()
    print("=========================")
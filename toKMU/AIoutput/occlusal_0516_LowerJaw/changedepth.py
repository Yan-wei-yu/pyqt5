import cv2
import numpy as np

# Load the image in grayscale
image = cv2.imread('original_patch_0.png', cv2.IMREAD_GRAYSCALE)

# Check if the image was loaded successfully
if image is None:
    print("Error: Could not load the image.")
else:
    # Set all non-zero pixels to 255
    image[image != 0] = 255

    # Save the modified image
    cv2.imwrite('modified_patch_0.png', image)
    print("Image processed and saved as 'modified_patch_0.png'.")
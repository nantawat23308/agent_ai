import cv2
import numpy as np
import matplotlib.pyplot as plt
import easyocr


def extract_text_from_image(image_path):
    """Extract text from the image using OCR"""
    reader = easyocr.Reader(['en', 'nl'])
    result = reader.readtext(image_path, detail=1, paragraph=False)

    # Extract the text and bounding boxes
    extracted_text = []
    for (bbox, text, prob) in result:
        if prob > 0.1 and text.isalpha():  # Filter out low-confidence results
            extracted_text.append((bbox, text, prob))

    return extracted_text

def route_get(image_path):
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    color_ranges = {
        "red1": ([0, 70, 50], [10, 255, 255]),
        "red2": ([170, 70, 50], [180, 255, 255]),  # Red has two ranges
        "blue": ([100, 150, 0], [140, 255, 255]),
        "yellow": ([20, 100, 100], [30, 255, 255]),
        "green": ([40, 70, 70], [80, 255, 255]),
    }
    color_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

    for key, (lower, upper) in color_ranges.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        color_mask |= cv2.inRange(hsv, lower_np, upper_np)

    # --- 2. Detect text areas from grayscale image ---
    # Threshold + Morphological ops (dilate to enhance letters)
    text_mask = cv2.adaptiveThreshold(gray, 255,
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY_INV,
                                      15, 10)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    text_mask = cv2.dilate(text_mask, kernel, iterations=1)
    # --- 3. Combine color and text masks ---
    # combined_mask = cv2.bitwise_or(color_mask, text_mask)

    feature_img = cv2.bitwise_and(image, image, mask=color_mask)

    # --- 6. ENHANCE: Increase contrast and saturation ---
    # Convert to HSV to boost saturation and brightness
    # feature_hsv = cv2.cvtColor(feature_img, cv2.COLOR_BGR2HSV)
    # feature_hsv[:, :, 1] = cv2.add(feature_hsv[:, :, 1], 60)  # Saturation boost
    # feature_hsv[:, :, 2] = cv2.add(feature_hsv[:, :, 2], 50)  # Brightness boost
    # enhanced = cv2.cvtColor(feature_hsv, cv2.COLOR_HSV2BGR)

    # # Optional: sharpen
    # sharpen_kernel = np.array([[0, -1, 0],
    #                            [-1, 5, -1],
    #                            [0, -1, 0]])
    # sharpened = cv2.filter2D(enhanced, -1, sharpen_kernel)

    result_bgra = cv2.cvtColor(feature_img, cv2.COLOR_BGR2BGRA)
    black_pixels = (color_mask == 0)
    result_bgra[black_pixels] = [0, 0, 0, 0]

    result_rgb = cv2.cvtColor(result_bgra, cv2.COLOR_BGRA2RGBA)
    plt.imsave("../report/colored_lines2.png", result_rgb)
    plt.imshow(result_rgb)
    plt.axis('off')
    plt.show()

if __name__ == '__main__':
    # image_path = "/home/nantawat/Desktop/my_project/agent_with_me/doc/MapProfile.png"
    # image_path = "/home/nantawat/Desktop/my_project/agent_with_me/doc/DNK_Procyclingstate.png"
    image_path = "/home/nantawat/Desktop/my_project/agent_with_me/doc/DNK_Bikeraceinfo.png"
    # img = cv2.imread(image_path)
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    # lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)
    # img_lines = img.copy()
    # for x1, y1, x2, y2 in lines[:, 0]:
    #     cv2.line(img_lines, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #
    # img_rgb = cv2.cvtColor(img_lines, cv2.COLOR_BGR2RGB)
    # plt.imshow(img)
    # plt.axis('off')
    # plt.show()
    # extracted_text = extract_text_from_image(image_path)
    # print("Extracted Text:")
    # for bbox, text, prob in extracted_text:
    #     print(f"Text: {text}, Probability: {prob:.2f}")
    route_get(image_path)
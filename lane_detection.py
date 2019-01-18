import numpy as np
import cv2 as cv
from PIL import Image,ImageGrab
from mss import mss
import time
import window_crop as edge_functions
import math
import keyboard_control
# testing, PB
from mask import adaptiveROI
import pyautogui

def lane_detect(img,counter):
    maskedImg = adaptiveROI(img)
    grayScaled = cv.cvtColor(maskedImg, cv.COLOR_BGR2GRAY)
    # grayScaled = edge_functions.filter_out_car(grayScaled)
    edges = cv.Canny(grayScaled,100,200)
    roi_edges = edge_functions.region_of_interest(edges)
    roi_edges = cv.GaussianBlur(roi_edges, (7,7), 0)
    """
    # Original implementation:
    edges = cv.Canny(img,100,200)
    edges = cv.GaussianBlur(edges, (7,7), 0)
    roi_edges = edge_functions.region_of_interest(edges)
    maskedImg = roi_edges
    """

    height = roi_edges.shape[0]
    width = roi_edges.shape[1]

    # Hough Line Detection
    lines = cv.HoughLinesP(
        roi_edges,
        rho=6,
        theta=np.pi / 60,
        threshold=160,
        lines=np.array([]),
        minLineLength=50,
        maxLineGap=7
    )
    # Coordinates
    left_line_x = []
    left_line_y = []
    right_line_x = []
    right_line_y = []
    newLines = []
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                if(x2 == x1):
                    continue
                slope = (y2 - y1) / (x2 - x1) # <-- Calculating the slope.
                if math.fabs(slope) < 0.1: # <-- Only consider extreme slope
                    continue
                if x1 < width/2 and slope < 0: # <-- If the slope is negative, left group.
                    newLines.append(line)
                    left_line_x.extend([x1, x2])
                    left_line_y.extend([y1, y2])
                elif x1 > width/2 and slope > 0: # <-- Otherwise, right group.
                    newLines.append(line)
                    right_line_x.extend([x1, x2])
                    right_line_y.extend([y1, y2])
        return (edge_functions.region_of_interest(img), grayScaled, edge_functions.draw_lines(roi_edges,newLines))
    pyautogui.keyUp("left")
    pyautogui.keyUp("right")
    pyautogui.keyUp("z")
    if left_line_x and right_line_x:
        # NOTE; Lines drawn from BOOTUM -> TOP
        min_y = 0                               # <-- Just below the horizon
        max_y = int(height)                     # <-- The bottom of the image

        poly_left = np.poly1d(np.polyfit(
            left_line_y,
            left_line_x,
            deg=1
        ))

        left_x_max = np.zeros_like(left_line_x[1])
        # left_x_max = int(poly_left(max_y))
        left_x_min = int(poly_left(min_y))

        poly_right = np.poly1d(np.polyfit(
            right_line_y,
            right_line_x,
            deg=1
        ))

        right_x_max = width * np.ones_like(left_line_x[1])
        # right_x_max = int(poly_right(max_y))
        right_x_min = int(poly_right(min_y))
        keyboard_control.determine_direction((left_x_max, max_y, left_x_min, min_y),(right_x_max, max_y, right_x_min, min_y),height,width,counter)
        line_image = edge_functions.draw_lines(
            roi_edges,
            [[
                [left_x_max, max_y, left_x_min, min_y],
                [right_x_max, max_y, right_x_min, min_y],
            ]],thickness=5)
        return (line_image)
    else:
        # return (roi_edges)
        return (edge_functions.region_of_interest(img), grayScaled, edge_functions.draw_lines(roi_edges,newLines))

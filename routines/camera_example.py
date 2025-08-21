# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 15:07:26 2025

@author: fkt25ya
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE
import cv2

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None

# if high, then will place circle at highest point of image
def find_circle(array, high=False, size=10):
     best = 0
     best_pos = (0,0)
     shape = (108,144)
     print(shape)
     array_resized = cv2.resize(array, dsize=(144,108))
     array_best = array_resized
     for (y,x), value in np.ndenumerate(array_resized):
         
         array_tp = np.copy(array_resized)
         Y,X = np.ogrid[:shape[0],:shape[1]]
         mask = ((X-x)**2 + (Y-y)**2) <= size**2
         array_tp[mask] = 1024 * (1 - high)
         val = np.sum(array_tp)
         if (val > best) ^ high:
             best = val
             best_pos = (x,y)
             array_best = np.copy(array_tp)
     return np.array(best_pos),array_best

with TLCameraSDK() as sdk:
    available_cameras = sdk.discover_available_cameras()
    print(available_cameras)
    if len(available_cameras) < 1:
        print("no cameras detected")

    with sdk.open_camera(available_cameras[0]) as camera:
        camera.exposure_time_us = 500000  # set exposure to 11 ms
        camera.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
        camera.image_poll_timeout_ms = 1000  # 1 second polling timeout

        camera.arm(2)

        camera.issue_software_trigger()

        frame = camera.get_pending_frame_or_null()
        if frame is not None:
            print("frame #{} received!".format(frame.frame_count))
            frame.image_buffer
            image_buffer_copy = np.copy(frame.image_buffer)
            numpy_shaped_image = image_buffer_copy.reshape(camera.image_height_pixels, camera.image_width_pixels)
            circle_pt, circle = find_circle(1024-numpy_shaped_image, high=False)
            imgfig = plt.imshow(circle)
            print(circle_pt, " is the optimal point")
            plt.show()
        else:
            print("Unable to acquire image, program exiting...")
            exit()
            

        camera.disarm()

#  Because we are using the 'with' statement context-manager, disposal has been taken care of.
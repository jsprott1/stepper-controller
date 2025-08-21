import numpy as np
import matplotlib.pyplot as plt
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
import client
import cv2
import time

from windows_setup import configure_path


def find_circle(array, high=False, size=10, invert=True):
    if invert:
        array = 1024 - array
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

def lattice_move_correct(lattice_vector, camera):
    initial_pos =  np.array(client.get_position())*1000
    print(f"Starting at {initial_pos}um")
    initial_pos_p, initial_image = find_circle(get_frame(camera))
    plt.imshow(initial_image)
    plt.pause(0.05)
    client.cryo_move_to_um_rel(lattice_vector[0], lattice_vector[1],velocity=200)
    time.sleep(1)
    new_frame = get_frame(camera)
    final_pos_p, final_image = find_circle(new_frame)
    delta_px = final_pos_p - initial_pos_p
    delta_px[0] *= -1
    delta_um = delta_px * um_per_px
    print(f"After 1st iteration: off by {delta_um}um, or {delta_px}px")
    plt.imshow(final_image)
    plt.pause(0.05)
    count = 1
    while (abs(delta_um) > 5).any():
        count+=1
        client.cryo_move_to_um_rel(delta_um[0], delta_um[1], velocity=200)
        time.sleep(1)
        new_frame = get_frame(camera)
        final_pos_p, final_image = find_circle(new_frame)
        delta_px = final_pos_p - initial_pos_p
        delta_um = delta_px * um_per_px
        print(f"After {count} iteration: off by {delta_um}um, or {delta_px}px")
        plt.imshow(final_image)
        plt.pause(0.05)
    final_pos = np.array(client.get_position())*1000
    total_moved = final_pos - initial_pos
    print(f"Moved a total distance of {total_moved}")
    error = (total_moved)/lattice_vector
    print(f"Estimated error is {error}")
    client.update_config(("stepper_controller", "steps_per_mm", "x", int(1*(lattice_vector[1] > 0))), float(error[1]), by_factor=True)
    client.update_config(("stepper_controller", "steps_per_mm", "y", int(1*(lattice_vector[0] > 0))), float(error[0]), by_factor=True)
    client.cryo_reset()
    return error



        
        
def get_frame(camera):
    camera.issue_software_trigger()
    frame = camera.get_pending_frame_or_null()
    if frame is not None:
        print("frame #{} received!".format(frame.frame_count))
        frame.image_buffer
        image_buffer_copy = np.copy(frame.image_buffer)
        numpy_shaped_image = image_buffer_copy.reshape(camera.image_height_pixels, camera.image_width_pixels)
        return numpy_shaped_image
    else:
        print("Unable to acquire image")
        return None
            
            
configure_path()
um_per_px = 1.5
lattice_vector_real = np.array([-1359.7,-59.6])
correction_log = []


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


        
        for i in range(10):
            correction_log.append(lattice_move_correct(lattice_vector_real, camera))
            plt.imshow(get_frame(camera))
            plt.pause(0.1)
            correction_log.append(lattice_move_correct(-lattice_vector_real, camera))
            plt.imshow(get_frame(camera))
            plt.pause(0.1)
        plt.plot(correction_log)
        plt.show()
        camera.disarm()

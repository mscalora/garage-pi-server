import os
import re
import sys
import threading
import util

cameras = {}

if sys.platform == 'darwin':
    import time
    import subprocess
    import shutil

    def get_webcam_image(tmp_file='/tmp/temp_image.jpeg', rotation=None):
        cap_file = os.path.join(os.path.dirname(tmp_file), 'cap%s' % (int(time.time()) % 5))
        cmd = 'bin/wacaw --jpeg %s >>/tmp/camera_stdout.txt &2>>/tmp/camera_stderr.txt' % cap_file
        # status = subprocess.check_call(cmd, shell=True)
        status = subprocess.call(cmd, shell=True)
        cap_file += '.jpeg'
        # os.system(cmd)
        for i in range(25):
            if os.path.exists(cap_file):
                break
            time.sleep(0.1)
        time.sleep(0.15)
        if os.path.exists(cap_file):
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)
            shutil.copyfile(cap_file, tmp_file)

else:
    import pygame
    import pygame.camera
    import pygame.transform
    import random

    pygame.camera.init()


    @util.repeat_delay_call(60*60)
    def reset_camera_list():
        global cameras
        cameras = {}


    def pick_camera():
        if len(cameras) > 0:
            return sorted(cameras.keys(), key=lambda n: cameras[n]["errors"]*100+ord(n[-1:]))[0]
        return '/dev/video0'


    def report_camera_error(camera):
        global cameras
        if len(cameras) == 0:
            cameras = {path: {"errors": 0} for path in pygame.camera.list_cameras()}
        if camera in cameras:
            cameras[camera]["errors"] += 1


    def get_camera_path_list():
        camera_list = pygame.camera.list_cameras()
        return camera_list


    def resolve_camera(camera):
        if isinstance(camera, int) or (hasattr(camera, 'zfill') and len(camera) == 1):
            return '/dev/video%s' % camera
        return camera


    def get_webcam_image(tmp_file='/var/tmp/temp_image.jpeg', rotation=None, retry=0, camera=None, brightness=None):
        # test pygame.camera.list_cameras() #Camera detected or not
        camera_path = pick_camera() if camera is None else resolve_camera(camera)
        try:
            cam = pygame.camera.Camera(camera_path, (640, 480))
            options = {}
            if rotation is not None and rotation == 180:
                options['vflip'] = True
            if brightness is not None:
                options['brightness'] = int(brightness)
            cam.start()
            # time.sleep(0.05)
            if len(options):
                cam.set_controls(**options)
            tls = threading.local()
            if hasattr(tls, 'surface'):
                img = cam.get_image(tls.surface)
            else:
                img = cam.get_image()
            tls.surface = img
            cam.stop()
            if rotation is not None and rotation != 180:
                img = pygame.transform.rotate(img, int(rotation))
            pygame.image.save(img, tmp_file)
        except SystemError, e:
            print("Retry: %d" % retry)
            report_camera_error(camera_path)
            if retry < 3:
                get_webcam_image(tmp_file=tmp_file, rotation=rotation, camera=camera, brightness=brightness, retry=retry+1)


    def get_webcams():
        cam_list = pygame.camera.list_cameras()
        return {path: {
            "size": pygame.camera.Camera(path).get_size(),
            "name": 'Camera %d' % (int('0'+re.sub(ur'\D', '', path))+1)
        } for path in cam_list}


#
# # for debugging
#
#     def get_surface(rotation=None, retry=0, camera=None, brightness=None):
#         # test pygame.camera.list_cameras() #Camera detected or not
#         camera_path = pick_camera() if camera is None else resolve_camera(camera)
#         try:
#             cam = pygame.camera.Camera(camera_path, (640, 480))
#             options = {}
#             if rotation is not None and rotation == 180:
#                 options['vflip'] = True
#             if brightness is not None:
#                 options['brightness'] = int(brightness)
#             cam.start()
#             if len(options):
#                 cam.set_controls(**options)
#             tls = threading.local()
#             if hasattr(tls, 'surface'):
#                 img = cam.get_image(tls.surface)
#             else:
#                 img = cam.get_image()
#             tls.surface = img
#             cam.stop()
#             if rotation is not None and rotation != 180:
#                 img = pygame.transform.rotate(img, int(rotation))
#             return img
#         except SystemError, e:
#             report_camera_error(camera_path)
#             if retry < 3:
#                 get_surface(rotation=rotation, camera=camera, brightness=brightness, retry=retry+1)
#         return None

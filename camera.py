import os
import sys

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

    pygame.camera.init()

    def get_camera_list():
        camera_list = pygame.camera.list_cameras()
        return camera_list

    def get_webcam_image(tmp_file='/tmp/temp_image.jpeg', rotation=None):
        # test pygame.camera.list_cameras() #Camera detected or not
        cam = pygame.camera.Camera("/dev/video0", (640, 480))
        cam.start()
        img = cam.get_image()
        cam.stop()
        if rotation is not None:
            img = pygame.transform.rotate(img, int(rotation))
        pygame.image.save(img, tmp_file)

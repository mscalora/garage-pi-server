import os
import subprocess
import sys
import time
import datetime

if sys.platform == 'darwin':

    def get_webcam_image(tmp_file='/tmp/temp_image.jpeg', rotation=None):
        cap_file = os.path.join(os.path.dirname(tmp_file), 'cap%s' % (int(time.time()) % 20))
        cmd = 'bin/wacaw --jpeg %s >>/tmp/camera_stdout.txt &2>>/tmp/camera_stderr.txt' % cap_file
        status = subprocess.call(cmd, shell=True)
        cap_file += '.jpeg'
        # os.system(cmd)
        for i in range(25):
            if os.path.exists(cap_file):
                break
            time.sleep(0.1)
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
        if os.path.exists(cap_file):
            os.rename(cap_file, tmp_file)

else:
    import pygame
    import pygame.camera
    import pygame.transform

    def get_webcam_image(tmp_file='/tmp/temp_image.jpeg', rotation=None):
        pygame.camera.init()
        # test pygame.camera.list_cameras() #Camera detected or not
        cam = pygame.camera.Camera("/dev/video0", (640, 480))
        cam.start()
        img = cam.get_image()
        cam.stop()
        if rotation is not None:
            img = pygame.transform.rotate(img, int(rotation))
        pygame.image.save(img, tmp_file)

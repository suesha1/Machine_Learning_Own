# Age and Gender Estimation
This repository contains a WideResNet model for face age and gender estimation. The pretrained weights can be found [here](https://github.com/yu4u/age-gender-estimation/releases/download/v0.5/weights.29-3.76_utk.hdf5).

## The Project Architecture

 - Import all the required libraries.
 - Load the pre-built model for facial detection.
 - Specify the path of a video file chosen for the age-gender estimation.
 - Read the video frame by frame in cycle until the end of the video using OpenCV.
 - Get a smaller resized frame. As it is faster to process small images and this merely does not affect quality.
 - Detect the faces in each frame using the face detector.
 - Use faces coordinates of a small frame to extract faces patches from original (big) frame.
 - Convert and adjust faces patches to a format that model expects.
 - Pass facial images through model to get predicted genders and ages for all faces.
 - Draw a rectangle around each face and a label with estimated gender and age.
 - Finally, create video using all the frames using OpenCV.

## Demo Videos
  The demo videos can be found here. https://drive.google.com/file/d/1mDzFXsvortftzvFUKrh_jxlNrPx-ckEi/view?usp=sharing

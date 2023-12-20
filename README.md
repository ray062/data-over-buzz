Data-over-buzz can convert file into sound and demodulate the sound back to the file.

It would be useful if you want to transfer a (small) file from PC A to PC B for which there is no conventional data connection possible (USB, Network, SD card etc.)

sonit.py is to convert a file to a wav file.

demodit.py convert a wav file back to the file.

# How to use it:
- Typically, you use sonit.py to convert the file to a wav file on PC A.
- Then, connect PC A and PC B with audio cable (Jack cable from speaker of A to line in of B).
- Turn the volume of A to 80%, turn off all sound enhancement feature (equalizer).
- Start record sound from line in on B (choose 192k or higher sample rate, 100% volume).
- Immediately start to play the wav file on A.
- When it's finished on A, STOP recording on B.
- Now you have a wav file on B and you can try to use demodit.py to convert it back to the file.

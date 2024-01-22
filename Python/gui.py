#!/usr/bin/env python
import PySimpleGUI as sg
import cv2
import numpy as np

CAM_NUM = 0

def main():

    sg.theme('Black')

    # define the window layout
    layout = [[sg.Text('Theia Dashboard', size=(40, 1), justification='center', font='Any 20')],
              [sg.Image(filename='', key='image')],
              [sg.Button('Enable Theia\'s Eye', size=(10, 2), font='Any 14'),
               sg.Button('Disable Theia\'s Eye', size=(10, 2), font='Any 14', disabled=True),
               sg.Button('Exit', size=(10, 2), font='Any 14'), ]]

    # create the window and show it without the plot
    window = sg.Window('Theia Dashboard', layout, location=(800, 400), element_justification='center', icon='Media/Theia.png')

    # ---===--- Event LOOP Read and display frames, operate the GUI --- #
    recording = False
    startup = False
    
    while True:
        event, values = window.read(timeout=20)

        if startup == False:
            # Create Dark Image
            img = np.full((480, 640), 0)
            imgbytes = cv2.imencode('.png', img)[1].tobytes()
            window['image'].update(data=imgbytes)
            startup = True

        elif event == 'Exit' or event == sg.WIN_CLOSED:
            break

        elif event == 'Enable Theia\'s Eye':
            recording = True
            cap = cv2.VideoCapture(CAM_NUM)
            window['Enable Theia\'s Eye'].update(disabled=True)
            window['Disable Theia\'s Eye'].update(disabled=False)

        elif event == 'Disable Theia\'s Eye':
            recording = False
            cap.release()
            img = np.full((480, 640), 0)
            # this is faster, shorter and needs less includes
            imgbytes = cv2.imencode('.png', img)[1].tobytes()
            window['Enable Theia\'s Eye'].update(disabled=False)
            window['Disable Theia\'s Eye'].update(disabled=True)
            window['image'].update(data=imgbytes)

        if recording:
            ret, frame = cap.read()
            imgbytes = cv2.imencode('.png', frame)[1].tobytes()  # ditto
            window['image'].update(data=imgbytes)

    if cap.isOpened():
        cap.release()


main()
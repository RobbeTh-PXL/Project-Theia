#!/usr/bin/env python
import PySimpleGUI as sg
import cv2 as cv
import numpy as np
import argparse
import time
from yunet import YuNet
import serial
import serial.tools.list_ports

im_width = 640
im_height = 480
im_width_center = im_width / 2
im_height_center = im_height / 2
deadzone = 10

sg.theme('Black')
programIcon = 'Media/Theia.png'

# Valid combinations of backends and targets
backend_target_pairs = [
    [cv.dnn.DNN_BACKEND_OPENCV, cv.dnn.DNN_TARGET_CPU],
    [cv.dnn.DNN_BACKEND_CUDA,   cv.dnn.DNN_TARGET_CUDA],
    [cv.dnn.DNN_BACKEND_CUDA,   cv.dnn.DNN_TARGET_CUDA_FP16],
    [cv.dnn.DNN_BACKEND_TIMVX,  cv.dnn.DNN_TARGET_NPU],
    [cv.dnn.DNN_BACKEND_CANN,   cv.dnn.DNN_TARGET_NPU]
]

parser = argparse.ArgumentParser(description='YuNet: A Fast and Accurate CNN-based Face Detector (https://github.com/ShiqiYu/libfacedetection).')
parser.add_argument('--input', '-i', type=str,
                    help='Usage: Set input to a certain image, omit if using camera.')
parser.add_argument('--model', '-m', type=str, default='Python/face_detection_yunet_2023mar.onnx',
                    help="Usage: Set model type, defaults to 'face_detection_yunet_2023mar.onnx'.")
parser.add_argument('--backend_target', '-bt', type=int, default=0,
                    help='''Choose one of the backend-target pair to run this demo:
                        {:d}: (default) OpenCV implementation + CPU,
                        {:d}: CUDA + GPU (CUDA),
                        {:d}: CUDA + GPU (CUDA FP16),
                        {:d}: TIM-VX + NPU,
                        {:d}: CANN + NPU
                    '''.format(*[x for x in range(len(backend_target_pairs))]))
parser.add_argument('--conf_threshold', type=float, default=0.9,
                    help='Usage: Set the minimum needed confidence for the model to identify a face, defauts to 0.9. Smaller values may result in faster detection, but will limit accuracy. Filter out faces of confidence < conf_threshold.')
parser.add_argument('--nms_threshold', type=float, default=0.3,
                    help='Usage: Suppress bounding boxes of iou >= nms_threshold. Default = 0.3.')
parser.add_argument('--top_k', type=int, default=5000,
                    help='Usage: Keep top_k bounding boxes before NMS.')
parser.add_argument('--save', '-s', action='store_true',
                    help='Usage: Specify to save file with results (i.e. bounding box, confidence level). Invalid in case of camera input.')
parser.add_argument('--vis', '-v', action='store_true',
                    help='Usage: Specify to open a new window to show results. Invalid in case of camera input.')
args = parser.parse_args()

# Check OpenCV version
assert cv.__version__ >= "4.8.0", \
       "Please install latest opencv-python to try this demo: python3 -m pip install --upgrade opencv-python"

def get_camera_list():
    camera_list = []
    index = 0

    while True:
        cap = cv.VideoCapture(index)
        if cap is None or not cap.isOpened():
            break
        else:
            camera_list.append(index)
        cap.release()
        index += 1

    return camera_list

def find_active_ports():
    active_ports = [
        p.device
        for p in serial.tools.list_ports.comports()
    ]

    return active_ports

def visualize(image, results, box_color=(0, 255, 0), text_color=(0, 0, 255), fps=None):
    output = image.copy()
    landmark_color = [
        (255,   0,   0), # right eye
        (  0,   0, 255), # left eye
        (  0, 255,   0), # nose tip
        (255,   0, 255), # right mouth corner
        (  0, 255, 255)  # left mouth corner
    ]

    if fps is not None:
        cv.putText(output, 'FPS: {:.2f}'.format(fps), (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, text_color)

    if len(results) != 0:
        first = results[0]
        target_xy = [first[8], first[9]]
        # target_xy = [first[4], first[5]]

        if target_xy[0] > im_width_center + deadzone:
            do_yaw = 1
        elif target_xy[0] < im_width_center - deadzone:
            do_yaw = -1
        else:
            do_yaw = 0

        if target_xy[1] < im_height_center - deadzone:
            do_pitch = 1
        elif target_xy[1] > im_height_center + deadzone:
            do_pitch = -1
        else:
            do_pitch = 0

        formatted_str = "{} {}\n".format(do_yaw, do_pitch)

    for det in results:
        bbox = det[0:4].astype(np.int32)
        cv.rectangle(output, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), box_color, 2)

        conf = det[-1]
        cv.putText(output, '{:.4f}'.format(conf), (bbox[0], bbox[1]+12), cv.FONT_HERSHEY_DUPLEX, 0.5, text_color)

        landmarks = det[4:14].astype(np.int32).reshape((5,2))
        for idx, landmark in enumerate(landmarks):
            cv.circle(output, landmark, 2, landmark_color[idx], 2)

    cv.circle(output, [int(im_width/2), int(im_height/2)], 2, (255,255,255), 2)

    return output, formatted_str

# define the window layout
layout = [
    [
        sg.Text('Theia System Controller', size=(40, 1), justification='center', font='Any 20')
    ],
    [
        sg.Text('Camera:'),
        sg.DropDown(values=get_camera_list(), key='-CAMERA_DROPDOWN-', size=(10,5), enable_events=True, readonly=True),
        sg.Text('Weapon Controller:'),
        sg.DropDown(values=find_active_ports(), key='-PORT_DROPDOWN-', size=(10,5), enable_events=True, readonly=True),
        sg.Button('Refresh', auto_size_button=True, font='Any 10'),
    ],
    [
        sg.Image(filename='', key='image')
    ],
    [
        sg.Listbox(values=[], key='-LIST-', enable_events=True, size=(75, 10))
    ],
    [
        sg.Button('Enable Theia\'s Eye', size=(10, 2), font='Any 14', disabled=True),
        sg.Button('Disable Theia\'s Eye', size=(10, 2), font='Any 14', disabled=True),
        sg.Button('Exit', size=(10, 2), font='Any 14')
    ]
]

def main():

    backend_id = backend_target_pairs[args.backend_target][0]
    target_id = backend_target_pairs[args.backend_target][1]

    model = YuNet(modelPath=args.model,
                  inputSize=[320, 320],
                  confThreshold=args.conf_threshold,
                  nmsThreshold=args.nms_threshold,
                  topK=args.top_k,
                  backendId=backend_id,
                  targetId=target_id)
    
    #print("Port status:", arduino.is_open)

    # create the window and show it without the plot
    window = sg.Window('Theia Dashboard', layout, location=(800, 400), element_justification='center', icon=programIcon)

    # ---===--- Event LOOP Read and display frames, operate the GUI --- #
    record = False
    recording_failed = False
    blank_screen = True
    cap = None
    arduino = None
    enable_motion = False
    
    while True:
        event, values = window.read(timeout=20)

        if event == 'Exit' or event == sg.WIN_CLOSED:
            if arduino is not None:
                arduino.close()
            if cap is not None:
                cap.release()
            break

        elif event == "Refresh":
            window['-CAMERA_DROPDOWN-'].update(values=get_camera_list())
            window['-PORT_DROPDOWN-'].update(values=find_active_ports())

        elif event == '-CAMERA_DROPDOWN-':
             camera_index = values['-CAMERA_DROPDOWN-']
             if camera_index is not None or not "":
                  window['Enable Theia\'s Eye'].update(disabled=False)
        
        elif event == '-PORT_DROPDOWN-':
             port_index = values['-PORT_DROPDOWN-']
             arduino = serial.Serial(port=port_index, baudrate=115200, timeout=.1)

        elif event == '-LIST-':
            selected_item = values['-LIST-'][0]

        elif event == 'Enable Theia\'s Eye':
            record = True
            cap = cv.VideoCapture(camera_index)

            w = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
            print("width: {} height: {}".format(w, h))
            model.setInputSize([w, h])

            window['Enable Theia\'s Eye'].update(disabled=True)
            window['Disable Theia\'s Eye'].update(disabled=False)

        elif event == 'Disable Theia\'s Eye' or recording_failed and record:
            record = False
            cap.release()
            window['Enable Theia\'s Eye'].update(disabled=False)
            window['Disable Theia\'s Eye'].update(disabled=True)
            blank_screen = True

        if blank_screen == True:
            img = cv.imread("Media/NO_SIGNAL.jpg")
            imgbytes = cv.imencode('.png', img)[1].tobytes()
            window['image'].update(data=imgbytes)
            blank_screen = False

        elif record:
            hasFrame, frame = cap.read()
            
            tm = cv.TickMeter()
            if not hasFrame:
                sg.popup('ERROR: Invalid Source, No Frames Grabbed', title='SYSTEM ERROR', keep_on_top= True, icon=programIcon)
                recording_failed = True

            else:
                recording_failed = False

                # Inference
                tm.start()
                results = model.infer(frame) # results is a tuple
                # print(results)
                tm.stop()

                # Draw results on the input image
                frame, movePos = visualize(frame, results, fps=tm.getFPS())

                #print(movePos, end='')
                if enable_motion and arduino is not None:
                    arduino.write(bytes(movePos, 'utf-8'))

                imgbytes = cv.imencode('.png', frame)[1].tobytes()
                window['image'].update(data=imgbytes)
                tm.reset()


main()
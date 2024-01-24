import PySimpleGUI as sg

layout = [
    [
        sg.Image(key='-IMAGE-', filename='Media/Theia.png'),
        sg.Listbox(values=['Item 1', 'Item 2', 'Item 3'], key='-LIST-', enable_events=True, size=(20, 10))
    ],
    [
        sg.Text('Target:', font=('Helvetica', 12), justification='center', pad=((10, 10), (5, 5))),
        sg.Button('Button 1', size=(10, 1), pad=((50, 10), (5, 5))),
        sg.Button('Button 2', size=(10, 1), pad=((10, 50), (5, 5)))
    ]
]

window = sg.Window('Image and Clickable List', layout, resizable=True)

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break
    elif event == '-LIST-':
        selected_item = values['-LIST-'][0]
        sg.popup(f'You clicked on {selected_item}')

window.close()

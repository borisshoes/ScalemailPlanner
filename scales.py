from dataclasses import dataclass
import dearpygui.dearpygui as dpg
import numpy as np
import pyperclip
dpg.create_context()

@dataclass
class Scale:
    x: int
    y: int
    color_id: int
    texture: str
    layer_id: str = None

txt_width, txt_height, txt_channels, txt_data = dpg.load_image("scale.png")
scales = []
scale_size_mod = 1
scale_width, scale_height, scale_y_spacing, scale_x_spacing, scale_x_offset = 0,0,0,0,0
max_scale_x_spacing = int(txt_width*1.1)
max_scale_y_spacing = int(txt_height/3)

previous_states = ['[0,0][ffffff][0]']

def scale_scales(mod:int):
    global scale_size_mod,scale_width,scale_height,scale_y_spacing,scale_x_spacing,scale_x_offset
    scale_size_mod = mod
    scale_width = scale_size_mod*txt_width
    scale_height = scale_size_mod*txt_height
    scale_y_spacing = int(scale_height/3)
    scale_x_spacing = int(scale_width*1.1)
    scale_x_offset = int(scale_width*1.1/2)
scale_scales(scale_size_mod)

def make_new_texture(tag, color):
    with dpg.texture_registry():
        dpg.add_dynamic_texture(txt_width, txt_height, txt_data, tag=tag)
    update_dynamic_texture(color,tag)


def update_dynamic_texture(color,texture_id):
    new_color = [0,0,0,0]
    new_color[0] = color[0] / 255
    new_color[1] = color[1] / 255
    new_color[2] = color[2] / 255
    new_color[3] = color[3] / 255

    new_texture_data = []
    for i in range(0, txt_width * txt_height):
        base_color = (txt_data[4*i+0],txt_data[4*i+1],txt_data[4*i+2],txt_data[4*i+3])
        new_color_rgb = (base_color[0]*new_color[0],base_color[1]*new_color[1],base_color[2]*new_color[2])

        new_texture_data.append(new_color_rgb[0])
        new_texture_data.append(new_color_rgb[1])
        new_texture_data.append(new_color_rgb[2])
        new_texture_data.append(base_color[3] if not texture_id == "texture_0" else 0)

    dpg.set_value(texture_id, new_texture_data)
            
def draw_scale(scale):
    dpg.draw_image(scale.texture, (scale.x-scale_width/2, scale.y-scale_height/2), (scale.x+scale_width/2, scale.y+scale_height/2), uv_min=(0, 0), uv_max=(1, 1), tag=f"scale_{scale.x}_{scale.y}", parent=drawlist)

def create_scale(x,y,color_id,texture,layer_id=None):
    new_scale = Scale(x,y,color_id,texture,layer_id)
    draw_scale(new_scale)
    scales.append(new_scale)
    

def click_handler():
    x,y = dpg.get_mouse_pos()
    closest = get_closest_scale(x,y)
    try:
        if closest != None:
            closest.color_id = selected_color
            closest.texture = f"texture_{selected_color}"
            dpg.configure_item(f"scale_{closest.x}_{closest.y}",texture_tag=f"texture_{selected_color}")
    except:
        print(f"Couldn't find scale_{closest.x}_{closest.y}")
    update_color_counts()

    while dpg.is_mouse_button_down(button=dpg.mvMouseButton_Left):
        new_x,new_y = dpg.get_mouse_pos()
        if new_x != x or new_y != y:
            try:
                closest = get_closest_scale(new_x,new_y)
                if closest != None:
                    closest.color_id = selected_color
                    closest.texture = f"texture_{selected_color}"
                    dpg.configure_item(f"scale_{closest.x}_{closest.y}",texture_tag=f"texture_{selected_color}")
                    update_color_counts()
            except:
                print(f"Couldn't find scale_{closest.x}_{closest.y}")
    save_state()
    

def color_picked(sender, app_data, user_data):
    color_index = saved_color_icons.index(sender)
    new_color = dpg.get_value(sender)
    saved_colors[color_index] = new_color
    update_dynamic_texture(new_color,texture_id=f"texture_{color_index}")
    
y_top_off = 0
x_right_off = 0
y_off = 0
x_off = 0
rows = 0
columns = 0
def create_scale_matrix(save_after):
    global x_off,y_off,x_right_off,y_top_off,rows,columns,canvas_x,canvas_y,scales
    scales = []
    input_size = dpg.get_value("input_size")
    columns = input_size[0]
    rows = input_size[1]
    x_right_off = 0

    max_x = max_scale_x_spacing*columns
    max_y = max_scale_y_spacing*rows
    x_mod = 1
    y_mod = 1
    x_pad = txt_width*0.75
    y_pad = txt_height

    if max_x > canvas_x-x_pad:
        x_mod = (canvas_x-x_pad) / max_x
    if max_y > canvas_y-y_pad:
        y_mod = (canvas_y-y_pad) / max_y

    scale_scales(min(1,x_mod,y_mod))

    y_off = dpg.get_item_height(drawlist)-int((canvas_y-scale_y_spacing*rows)/1.8)
    x_off = int((canvas_x-scale_x_spacing*columns)/2)

    dpg.delete_item(drawlist, children_only=True)
    
    row_iter = 0
    y = y_off
    while row_iter < rows:
        with dpg.draw_layer(parent=drawlist, tag=f"layer_{y}"):
            x = x_off if row_iter % 2 == 0 else scale_x_offset+x_off
            col_iter = 0
            while col_iter < columns:
                create_scale(x,y,selected_color,f"texture_{selected_color}",layer_id=f"layer_{y}")
                if x > x_right_off:
                    x_right_off = x
                x += scale_x_spacing
                col_iter += 1
            y -= scale_y_spacing
            row_iter += 1
        y_top_off = y
    if save_after:
        save_state()
    update_color_counts()

def get_closest_scale(x,y):
    x1_n = round((x-x_off)/scale_x_spacing)
    x1 = x1_n*scale_x_spacing+x_off
    x2 = round((x-scale_x_offset-x_off) / scale_x_spacing) * scale_x_spacing + scale_x_offset + x_off
    y1_n = round((y-y_top_off)/scale_y_spacing)
    y1_type = 0 if (rows-y1_n) % 2 == 1 else 1
    y1 = y1_n*scale_y_spacing+y_top_off
    y2 = y1 - scale_y_spacing
    y3 = y1 + scale_y_spacing

    closest_scales = []

    if y1_type == 1:
        scale1 = (x1,y1)
        scale2 = (x2,y2)
        scale3 = (x2,y3)
    else:
        scale1 = (x2,y1)
        scale2 = (x1,y2)
        scale3 = (x1,y3)
    closest_scales.append(scale1)
    closest_scales.append(scale2)
    closest_scales.append(scale3)

    closest_scales = [scale for scale in closest_scales if not (scale[0] > x_right_off or scale[0] < x_off or scale[1] <= y_top_off or scale[1] > y_off)]

    if not closest_scales:
        return None

    point = np.array((x,y))
    centers = [np.array((scale[0],scale[1]+int(scale_height/6))) for scale in closest_scales]
    dists = [np.linalg.norm(point-center) for center in centers]
    pairs = [(closest_scales[i], dists[i]) for i in range(0, len(closest_scales))]
    pairs.sort(key = lambda pair: pair[1])
    closest = pairs[0]

    for scale in scales:
        if scale.x == int(closest[0][0]) and scale.y == int(closest[0][1]):
            return scale
    return None


def add_color_group(invisible=False,default_color=[255.0,255.0,255.0,255.0]):
    group_id = f"color_group_{len(saved_colors)}"
    dpg.add_group(horizontal=True, parent="color_selector",tag=group_id)
    saved_color_groups.append(group_id)
    if invisible:
        color_icon = dpg.add_color_button(parent=group_id,default_value=[0,0,0,0],enabled=False)
        color_text = dpg.add_selectable(label=f"Invisible (0)",parent=group_id)       
        make_new_texture(f"texture_{len(saved_colors)}",[0,0,0,0])
        saved_colors.append([0,0,0,0])
    else:
        color_icon = dpg.add_color_edit(parent=group_id, no_inputs=True, no_alpha=True,callback=color_picked,default_value=default_color)
        color_text = dpg.add_selectable(tag=f"color_text_{len(saved_colors)}",label=f"Color {len(saved_colors)} (0)",parent=group_id)
        make_new_texture(f"texture_{len(saved_colors)}",default_color)
        saved_colors.append(default_color)
    saved_color_icons.append(color_icon)
    saved_color_texts.append(color_text)
    dpg.configure_item(color_text,callback=_selection, user_data=saved_color_texts)
    if not invisible:
        _selection(color_text)

def update_color_counts():
    counts = [0 for color in saved_colors]
    for scale in scales:
        counts[scale.color_id] = counts[scale.color_id]+1

    index = 0
    for count in counts:
        lbl = f"Invisible ({count})" if index == 0 else f"Color {index} ({count})"
        dpg.configure_item(saved_color_texts[index],label=lbl)
        index += 1

def condense_layout(layout):
    if len(layout) < 3:
        return layout
    
    new_layout = []
    cur_value = layout[0]
    cur_index = 1
    counter = 1
    
    while cur_index < len(layout):
        if layout[cur_index] == cur_value:
            counter += 1
        else:
            if counter == 1:
                new_layout.append(f"{cur_value}")
            else:
                new_layout.append(f"{counter}-{cur_value}")
            counter = 1
            cur_value = layout[cur_index]
        if cur_index == len(layout)-1:
            if counter == 1:
                new_layout.append(f"{cur_value}")
            else:
                new_layout.append(f"{counter}-{cur_value}")

        cur_index += 1

    return new_layout

def generate_code(for_box = True):
    colors = ['{:02x}{:02x}{:02x}'.format(round(color[0]), round(color[1]), round(color[2])) for color in saved_colors[1:]]
    uncondensed_layout = [scale.color_id for scale in scales]
    layout = condense_layout(uncondensed_layout)
    code = f"[{columns},{rows}]{colors}{layout}".replace("'","").replace(" ","")
    if for_box:
        dpg.set_value("code_box", code)
        pyperclip.copy(code)
    return code

def import_code_button():
    import_code(False, dpg.get_value("code_box"))

def import_code(from_undo, raw_code):
    global saved_colors,saved_color_texts,saved_color_groups,saved_color_icons,selected_color,previous_states,selected_color
    code = raw_code[1:-1].replace("'","").replace(" ","")
    split_code = code.split('][')
    if len(split_code) != 3:
        return
    
    dims = split_code[0].split(',')
    colors = split_code[1].split(',')
    layout = split_code[2].split(',')
    
    if len(dims) != 2 or not dims[0].isdigit() or not dims[1].isdigit():
        return
    dpg.set_value("input_size",(int(dims[0]),int(dims[1]),0,0))
    
    for i in range(len(saved_colors)):
        item = dpg.get_alias_id(f"color_group_{i}")
        dpg.remove_alias(f"color_group_{i}")
        dpg.delete_item(item)

        item = dpg.get_alias_id(f"texture_{i}")
        dpg.remove_alias(f"texture_{i}")
        dpg.delete_item(item)

    previous_color = selected_color
    saved_colors = []
    saved_color_groups = []
    saved_color_texts = []
    saved_color_icons = []
    selected_color = 0
    add_color_group(True)
    create_scale_matrix(False)

    for color in colors:
        if len(color) != 6:
            add_color_group(True)
        else:
            color += "FF"
            add_color_group(False, [int(color[i:i+2], 16) for i in (0, 2, 4, 6)])
    
    index = 0
    count = 0
    for sequence in layout:
        if sequence.isdigit():
            length = 1
            color = int(sequence)
        else:
            seq_arr = sequence.split('-')
            if len(seq_arr) != 2 or not seq_arr[0].isdigit() or not seq_arr[1].isdigit():
                print("Error in sequence")
                continue
            length = int(seq_arr[0])
            color = int(seq_arr[1])
        count += length

        for i in range(length):
            if index >= len(scales):
                break
            scale = scales[index]
            scale.color_id = color
            scale.texture = f"texture_{color}"
            dpg.configure_item(f"scale_{scale.x}_{scale.y}",texture_tag=f"texture_{color}")
            index += 1
    if from_undo:
        if previous_color < len(saved_color_texts):
            _selection(saved_color_texts[previous_color])
    else:
        save_state()
    update_color_counts()

def number_keybind(num):
    if num < len(saved_color_texts):
        _selection(saved_color_texts[num])

def switch_color():
    global selected_color, prev_selected_color
    if prev_selected_color < len(saved_colors):
        _selection(saved_color_texts[prev_selected_color])
    else:
        _selection(saved_color_texts[0])

def undo():
    global previous_states
    if dpg.is_key_down(dpg.mvKey_Control):
        if previous_states:
            previous_states.pop()
            if not previous_states:
                previous_states = ['[0,0][ffffff][0]']
            restore_code = previous_states[-1]
            # print(f"Undoing {restore_code}")
            # print(previous_states)
            import_code(True, restore_code)

def save_state():
    global previous_states
    new_code = generate_code(False)
    if not previous_states or previous_states[-1] != new_code:
        previous_states.append(new_code)
        # print(f"Saving {new_code}")
        # print(previous_states)

with dpg.theme() as canvas_theme, dpg.theme_component():
    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0,0)

saved_colors = []
saved_color_groups = []
saved_color_texts = []
saved_color_icons = []
selected_color = 0
prev_selected_color = 0


window_width = 1450
window_height = 800
color_bar_width = 150
canvas_x = window_width-color_bar_width-60
canvas_y = window_height-60
with dpg.window() as window:
    with dpg.handler_registry():
        dpg.add_key_press_handler(dpg.mvKey_0,callback = lambda: number_keybind(0))
        dpg.add_key_press_handler(dpg.mvKey_1,callback = lambda: number_keybind(1))
        dpg.add_key_press_handler(dpg.mvKey_2,callback = lambda: number_keybind(2))
        dpg.add_key_press_handler(dpg.mvKey_3,callback = lambda: number_keybind(3))
        dpg.add_key_press_handler(dpg.mvKey_4,callback = lambda: number_keybind(4))
        dpg.add_key_press_handler(dpg.mvKey_5,callback = lambda: number_keybind(5))
        dpg.add_key_press_handler(dpg.mvKey_6,callback = lambda: number_keybind(6))
        dpg.add_key_press_handler(dpg.mvKey_7,callback = lambda: number_keybind(7))
        dpg.add_key_press_handler(dpg.mvKey_8,callback = lambda: number_keybind(8))
        dpg.add_key_press_handler(dpg.mvKey_9,callback = lambda: number_keybind(9))
        dpg.add_key_press_handler(dpg.mvKey_NumPad0,callback = lambda: number_keybind(0))
        dpg.add_key_press_handler(dpg.mvKey_NumPad1,callback = lambda: number_keybind(1))
        dpg.add_key_press_handler(dpg.mvKey_NumPad2,callback = lambda: number_keybind(2))
        dpg.add_key_press_handler(dpg.mvKey_NumPad3,callback = lambda: number_keybind(3))
        dpg.add_key_press_handler(dpg.mvKey_NumPad4,callback = lambda: number_keybind(4))
        dpg.add_key_press_handler(dpg.mvKey_NumPad5,callback = lambda: number_keybind(5))
        dpg.add_key_press_handler(dpg.mvKey_NumPad6,callback = lambda: number_keybind(6))
        dpg.add_key_press_handler(dpg.mvKey_NumPad7,callback = lambda: number_keybind(7))
        dpg.add_key_press_handler(dpg.mvKey_NumPad8,callback = lambda: number_keybind(8))
        dpg.add_key_press_handler(dpg.mvKey_NumPad9,callback = lambda: number_keybind(9))
        dpg.add_key_press_handler(dpg.mvKey_Tilde,callback = lambda: number_keybind(0))
        dpg.add_key_press_handler(dpg.mvKey_Spacebar,callback = switch_color)
        dpg.add_key_press_handler(dpg.mvKey_Z,callback = undo)

    with dpg.group(horizontal=True):

        with dpg.child_window(width=canvas_x, height=canvas_y) as canvas:
            dpg.bind_item_theme(canvas, canvas_theme)
            drawlist = dpg.add_drawlist(width=canvas_x, height=canvas_y)
            with dpg.item_handler_registry() as registry:
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Left, callback=click_handler)
            dpg.bind_item_handler_registry(drawlist, registry)

        with dpg.child_window(border=False):
            dpg.add_button(label="New Color",width=color_bar_width, callback=lambda: add_color_group(False))
            
            color_selector = dpg.child_window(width=color_bar_width, height=250, label="Color Selector",tag="color_selector")
            with color_selector:
                def _selection(sender):
                    global selected_color, prev_selected_color
                    prev_selected_color = selected_color
                    selected_color = saved_color_texts.index(sender)
                    for item in saved_color_texts:
                        if item != sender:
                            dpg.set_value(item, False)
                        else:
                            dpg.set_value(item, True)
                
                add_color_group(True)
                add_color_group()
            
            dpg.add_text("    Width | Height")
            dpg.add_input_intx(tag="input_size",width=color_bar_width,default_value=[15,20],size=2,min_value=1,min_clamped=True)
            dpg.add_button(label="Make Scale Grid",width=color_bar_width, callback=lambda: create_scale_matrix(True) )
            dpg.add_text("")
            dpg.add_button(label="Export",width=color_bar_width, callback=lambda: generate_code(True))
            dpg.add_input_text(tag="code_box",width=color_bar_width,hint="Code")
            dpg.add_button(label="Import",width=color_bar_width, callback=import_code_button)
            

dpg.set_primary_window(window, True)
dpg.create_viewport(width=window_width, height=window_height, title="Boris's Scalemail Planner")
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
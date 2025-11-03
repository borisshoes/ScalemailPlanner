import dearpygui.dearpygui as dpg
import pyperclip, base64, sys, os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    """https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ---- DPG context & source texture ----
dpg.create_context()
txt_width, txt_height, txt_channels, txt_data = dpg.load_image(resource_path("scale.png"))

# ---- App state ----
grid = []
x_vals = set()
y_vals = set()
rows = 0
columns = 0
scale_size_mod = 1.0
scale_width = scale_height = 0
scale_y_spacing = scale_x_spacing = scale_x_offset = 0
previous_states = ['[0,0][ffffff][0]']
base_row_parity = 0
coords_enabled = False

# canvas sizing
window_width = 1450
window_height = 800
color_bar_width = 150
canvas_x = window_width - color_bar_width - 40
canvas_y = window_height - 60

# layout offsets (top-left anchor of row 0, col 0)
x_off = 0
y_off = 0
total_w = 0
total_h = 0

# color/palette state
saved_colors = []
saved_color_groups = []
saved_color_texts = []
saved_color_icons = []
selected_color = 0
prev_selected_color = 0

# symmetry state
x_mirror_enabled = False
y_mirror_enabled = False
x_mirror_pos = 1.0  # column index space
y_mirror_pos = 2.0  # row index space

# ---- small utils ----
def _flatten_grid(): return [grid[r][c] for r in range(len(grid)) for c in range(len(grid[r]))]
def _clamp(v, lo, hi): return lo if v < lo else hi if v > hi else v
def _rgba01(r, g, b, a=255): return [r/255.0, g/255.0, b/255.0, a/255.0]

def ensure_palette_textures():
    if not dpg.does_item_exist("texture_registry"):
        with dpg.texture_registry(tag="texture_registry"): pass
    for i, col in enumerate(saved_colors):
        tag = f"texture_{i}"
        if not dpg.does_item_exist(tag):
            if i == 0:
                pixels = _rgba01(0, 0, 0, 0)
            else:
                r, g, b = map(int, col[:3])
                pixels = _rgba01(r, g, b, 255)
            dpg.add_static_texture(1, 1, pixels, tag=tag, parent="texture_registry")

def get_texture_tag_for(color_id: int) -> str:
    if color_id is None or color_id < 0 or color_id >= len(saved_colors): color_id = 0
    tag = f"texture_{color_id}"
    if not dpg.does_item_exist(tag): ensure_palette_textures()
    return tag

def normalize_grid_colors():
    if not grid: return
    max_id = len(saved_colors) - 1
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            cid = grid[r][c]
            grid[r][c] = cid if isinstance(cid, int) and 0 <= cid <= max_id else 0

# ---- geometry: scale sizes + centering ----
def _recompute_layout():
    global scale_width, scale_height, scale_y_spacing, scale_x_spacing, scale_x_offset, x_off, y_off, total_h, total_w
    # “ideal” spacing from source texture
    ideal_x = int(txt_width * 1.1)
    ideal_y = int(txt_height / 3)
    max_x = ideal_x * max(1, columns)
    max_y = ideal_y * max(1, rows)
    x_pad = int(txt_width * 0.75)
    y_pad = int(txt_height)

    x_mod = 1.0 if max_x <= canvas_x - x_pad else (canvas_x - x_pad) / max_x
    y_mod = 1.0 if max_y <= canvas_y - y_pad else (canvas_y - y_pad) / max_y
    mod = min(x_mod, y_mod, float(scale_size_mod))

    scale_width = max(1, int(txt_width * mod))
    scale_height = max(1, int(txt_height * mod))
    scale_y_spacing = max(1, int(scale_height / 3))
    scale_x_spacing = max(1, int(scale_width * 1.1))
    scale_x_offset = int(scale_width * 0.55)

    total_w = scale_width + (max(0, columns - 1)) * scale_x_spacing
    total_h = scale_height + (max(0, rows - 1)) * scale_y_spacing
    x_off = int((canvas_x - total_w) / 2)
    y_off = int((canvas_y - total_h) / 2)

    # print(f"columns: {columns}")
    # print(f"rows: {rows}")
    # print(f"max_x: {max_x}")
    # print(f"max_y: {max_y}")
    # print(f"x_pad: {x_pad}")
    # print(f"y_pad: {y_pad}")
    # print(f"mod: {mod}")
    # print(f"scale_width: {scale_width}")
    # print(f"scale_height: {scale_height}")
    # print(f"scale_y_spacing: {scale_y_spacing}")
    # print(f"scale_x_spacing: {scale_x_spacing}")
    # print(f"scale_x_offset: {scale_x_offset}")
    # print(f"total_w: {total_w}")
    # print(f"total_h: {total_h}")
    # print(f"x_off: {x_off}")
    # print(f"y_off: {y_off}")

def grid_to_pixel(row_index, col_index):
    y_from_top = (rows - 1 - row_index) * scale_y_spacing
    px = x_off + col_index * scale_x_spacing + (scale_x_offset if ((row_index + base_row_parity) % 2) == 1 else 0)
    py = y_off + y_from_top
    return int(px), int(py)

def pixel_to_grid(mouse_x, mouse_y):
    if rows <= 0 or columns <= 0 or scale_x_spacing == 0 or scale_y_spacing == 0:
        return None
    row_from_top = round((mouse_y - y_off) / max(1e-6, scale_y_spacing))
    row_from_top = _clamp(row_from_top, 0, rows - 1)
    row_index = rows - 1 - row_from_top
    row_has_offset = ((row_index + base_row_parity) % 2) == 1
    x_relative = mouse_x - x_off - (scale_x_offset if row_has_offset else 0)
    col_index = round(x_relative / max(1e-6, scale_x_spacing))
    col_index = _clamp(col_index, 0, columns - 1)
    return int(row_index), int(col_index)

def nearest_multiples(m, n):
    if n == 0: raise ValueError("n must be nonzero")
    k = round(m / n)
    nearest = k
    before = (k - 1)
    after = (k + 1)
    if isinstance(m, int) and isinstance(n, int): return int(nearest), int(before), int(after)
    return nearest, before, after

def _apply_paint(r: int, c: int, color_id: int):
    if 0 <= r < rows and 0 <= c < columns:
        grid[r][c] = color_id
        try:
            dpg.configure_item(f"scale_{r}_{c}", texture_tag=f"texture_{color_id}")
        except: pass

def _mirror_coords(r: int, c: int):
    coords = {(r, c)}
    if x_mirror_enabled:
        use_unoffset = (r % 2) == 0 if base_row_parity == 0 else (r % 2) == 1
        col = c if use_unoffset else c + 0.5
        dist = col - x_mirror_pos/2.0
        mc = int(round(c - 2*dist))
        coords.add((r, mc))
    if y_mirror_enabled:
        mr = int(round(2 * (rows-y_mirror_pos) - r))
        coords.add((mr, c))
    if x_mirror_enabled and y_mirror_enabled:
        mr = int(round(2 * (rows-y_mirror_pos) - r))
        use_unoffset = (r % 2) == 0 if base_row_parity == 0 else (r % 2) == 1
        col = c if use_unoffset else c + 0.5
        dist = col - x_mirror_pos/2.0
        mc = int(round(c - 2*dist))
        coords.add((mr, mc))
    return [(rr, cc) for rr, cc in coords if 0 <= rr < rows and 0 <= cc < columns]

# precise pick using 3-candidate test (same idea, centered math)
def get_closest_scale(x, y):
    #dpg.draw_circle((x, y), 3, color=(0, 255, 0, 255), fill=(0, 255, 0, 255), parent=drawlist)
    if rows <= 0 or columns <= 0 or scale_x_spacing == 0 or scale_y_spacing == 0:
        return None
    
    x_noff = x - x_off - (scale_width//2)
    y_noff = y - y_off - (scale_height//2)

    row_has_offset = (rows % 2) == 1 if base_row_parity == 0 else (rows % 2) == 0

    y_n1, y_n2, y_n3 = nearest_multiples(y_noff,scale_y_spacing)
    x_n1, x_n2, x_n3 = nearest_multiples(x_noff,scale_x_spacing)
    x_n4, x_n5, x_n6 = nearest_multiples(x_noff-scale_x_offset,scale_x_spacing)

    coord_pairs = {}
    first_x = (x_n1,x_n2,x_n3)
    last_x = (x_n4,x_n5,x_n6)
    for yv in (y_n1,y_n2,y_n3):
        is_even = yv % 2 == 0
        use_first = is_even if row_has_offset else not is_even
        xs = first_x if use_first else last_x
        for xv in xs: 
            if yv >= 0 and yv < rows and xv >= 0 and xv < columns:
                py = yv*scale_y_spacing + y_off + int(scale_height*0.66)
                px = xv*scale_x_spacing + x_off + (scale_width//2) if use_first else xv*scale_x_spacing + x_off + scale_x_offset + (scale_width//2)
                coord_pairs[(px,py)] = (xv,yv)

    #for px, py in coord_pairs.keys():
        #dpg.draw_circle((px, py), 3, color=(255, 255, 0, 255), fill=(255, 255, 0, 255), parent=drawlist)
    
    if len(coord_pairs) == 0:
        return None

    chosen = min(coord_pairs.keys(), key=lambda k: (k[0]-x)*(k[0]-x)+(k[1]-y)*(k[1]-y))
    #dpg.draw_circle((chosen[0], chosen[1]), 3, color=(255, 0, 0, 255), fill=(255, 0, 0, 255), parent=drawlist)
    return pixel_to_grid(chosen[0],chosen[1]-int(scale_height*0.66))

# ---- textures & drawing ----
def make_new_texture(tag, color):
    with dpg.texture_registry(): dpg.add_dynamic_texture(txt_width, txt_height, txt_data, tag=tag)
    update_dynamic_texture(color, tag)

def update_dynamic_texture(color, texture_id):
    rgba = [color[0]/255.0, color[1]/255.0, color[2]/255.0, color[3]/255.0]
    out = []
    use_alpha = (texture_id != "texture_0")
    for i in range(0, txt_width * txt_height):
        r0, g0, b0, a0 = txt_data[4*i+0], txt_data[4*i+1], txt_data[4*i+2], txt_data[4*i+3]
        out.append(r0 * rgba[0])
        out.append(g0 * rgba[1])
        out.append(b0 * rgba[2])
        out.append(a0 if use_alpha else 0)
    dpg.set_value(texture_id, out)
    redraw_symmetry_lines()

def draw_cell(row, col, color_id, layer_id):
    global x_vals, y_vals
    px, py = grid_to_pixel(row, col)
    x_vals.add(px)
    y_vals.add(py)
    dpg.draw_image(get_texture_tag_for(color_id), (px, py), (px + scale_width, py + scale_height), tag=f"scale_{row}_{col}", parent=layer_id)
    if coords_enabled:
        dpg.draw_text((px+scale_width/2-20, py+scale_height/2), f"{col},{row}",color=find_most_distant_oklab_color_rgba(),size=15*scale_size_mod)

# ---- grid lifecycle ----
def create_scale_matrix(save_after):
    global rows, columns, grid, x_vals, y_vals
    ensure_palette_textures()
    normalize_grid_colors()
    columns, rows = map(int, dpg.get_value("input_size")[:2])
    _recompute_layout()
    dpg.delete_item(drawlist, children_only=True)

    old = grid
    new_grid = [[0 for _ in range(columns)] for _ in range(rows)]
    for r in range(min(rows, len(old))):
        for c in range(min(columns, len(old[r]))):
            new_grid[r][c] = old[r][c]
    grid = new_grid
    if len(old) != rows or len(old) == 0 or len(old[0]) != columns:
        x_vals.clear()
        y_vals.clear()

    for r in range(rows):
        layer_id = f"layer_{r}"
        with dpg.draw_layer(parent=drawlist, tag=layer_id):
            for c in range(columns): draw_cell(r, c, grid[r][c], layer_id)

    if save_after: save_state()
    update_color_counts()

    try:
        dpg.configure_item("x_mirror_slider", max_value=max(1, 2*(columns - 1)))
        dpg.configure_item("y_mirror_slider", max_value=max(2, rows - 1))
    except: pass
    redraw_symmetry_lines()

def make_new_grid():
    global grid, rows, columns, base_row_parity
    columns, rows = map(int, dpg.get_value("input_size")[:2])
    grid = [[selected_color for _ in range(columns)] for _ in range(rows)]
    base_row_parity = 0
    create_scale_matrix(True)
    save_state()

def _ensure_symmetry_layer():
    if not dpg.does_item_exist("symmetry_lines"):
        dpg.add_draw_layer(parent=drawlist, tag="symmetry_lines")

def redraw_symmetry_lines():
    _ensure_symmetry_layer()
    dpg.delete_item("symmetry_lines", children_only=True)
    if not (x_mirror_enabled or y_mirror_enabled): return
    rgba = find_most_distant_oklab_color_rgba()
    color = (int(rgba[0]), int(rgba[1]), int(rgba[2]), int(rgba[3]))
    if x_mirror_enabled:
        x = x_off + (int(x_mirror_pos) + 0.5) * scale_x_spacing//2 + scale_width*0.25 - 1
        dpg.draw_line(p1=(x, 0), p2=(x, canvas_y), color=color, thickness=2, parent="symmetry_lines")
        #print(f"Drawing Line {(x, 0)}, {(x, canvas_y)}")
    if y_mirror_enabled:
        y = y_off + (int(y_mirror_pos) + 0.5) * scale_y_spacing + scale_height*0.167
        dpg.draw_line(p1=(0, y), p2=(canvas_x, y), color=color, thickness=2, parent="symmetry_lines")
        #print(f"Drawing Line {(0, y)}, {(canvas_x, y)}")


# ---- painting ----
def click_handler():
    x, y = dpg.get_mouse_pos()
    rc = get_closest_scale(x, y)
    if rc:
        r, c = rc
        for rr, cc in _mirror_coords(r, c): _apply_paint(rr, cc, selected_color)
        update_color_counts()
    while dpg.is_mouse_button_down(button=dpg.mvMouseButton_Left):
        nx, ny = dpg.get_mouse_pos()
        if nx != x or ny != y:
            rc = get_closest_scale(nx, ny)
            if rc:
                r, c = rc
                for rr, cc in _mirror_coords(r, c): _apply_paint(rr, cc, selected_color)
                update_color_counts()
                x, y = nx, ny
    save_state()

# ---- palette UI ----
def color_picked(sender, app_data, user_data):
    idx = saved_color_icons.index(sender)
    new_color = dpg.get_value(sender)
    saved_colors[idx] = new_color
    update_dynamic_texture(new_color, texture_id=f"texture_{idx}")

def add_color_group(invisible=False, default_color=[255, 255, 255, 255]):
    gid = f"color_group_{len(saved_colors)}"
    dpg.add_group(horizontal=True, parent="color_selector", tag=gid)
    saved_color_groups.append(gid)
    if invisible:
        icon = dpg.add_color_button(parent=gid, default_value=[0,0,0,0], enabled=False)
        text = dpg.add_selectable(label="Invisible (0)", parent=gid)
        make_new_texture(f"texture_{len(saved_colors)}", [0,0,0,0])
        saved_colors.append([0,0,0,0])
    else:
        icon = dpg.add_color_edit(parent=gid, no_inputs=True, no_alpha=True, callback=color_picked, default_value=default_color)
        text = dpg.add_selectable(tag=f"color_text_{len(saved_colors)}", label=f"Color {len(saved_colors)} (0)", parent=gid)
        make_new_texture(f"texture_{len(saved_colors)}", default_color)
        saved_colors.append(default_color)
    saved_color_icons.append(icon)
    saved_color_texts.append(text)
    dpg.configure_item(text, callback=_selection, user_data=saved_color_texts)
    if not invisible: _selection(text)

def update_color_counts():
    counts = [0 for _ in saved_colors]
    for color_id in _flatten_grid():
        if 0 <= color_id < len(saved_colors): counts[color_id] += 1
    for i, count in enumerate(counts):
        dpg.configure_item(saved_color_texts[i], label=("Invisible" if i == 0 else f"Color {i}") + f" ({count})")

# --- OKLab helpers (Björn Ottosson reference impl; no external deps)
def _srgb_to_linear(c): return ((c/12.92) if c<=0.04045 else (((c+0.055)/1.055)**2.4))
def _linear_to_srgb(c): 
    v = (12.92*c if c<=0.0031308 else (1.055*(c**(1/2.4))-0.055))
    return 0.0 if v<0.0 else 1.0 if v>1.0 else v

def _srgb_u8_to_oklab(r, g, b):
    r = _srgb_to_linear(r/255.0)
    g = _srgb_to_linear(g/255.0)
    b = _srgb_to_linear(b/255.0)
    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b
    l_ = l**(1/3)
    m_ = m**(1/3)
    s_ = s**(1/3)
    L = 0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_
    a = 1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_
    b = 0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_
    return (L, a, b)

# --- distance utility
def _oklab_dist2(c1, c2):
    dL = c1[0]-c2[0]
    da = c1[1]-c2[1]
    db = c1[2]-c2[2]
    return dL*dL + da*da + db*db

# --- main: find most distant color vs. current palette (returns RGBA)
def find_most_distant_oklab_color_rgba(palette_rgb_u8=None, alpha=255):
    # palette_rgb_u8: iterable of [r,g,b] or (r,g,b); if None, uses saved_colors[1:]
    # returns (R,G,B,A)
    source = palette_rgb_u8
    if source is None:
        try:
            source = [c for i,c in enumerate(saved_colors) if i>0 and c is not None]
            source.append((37,37,38))
        except NameError:
            source = []
    pal_ok = []
    for c in source:
        r, g, b = int(c[0]), int(c[1]), int(c[2])
        pal_ok.append(_srgb_u8_to_oklab(r, g, b))
    if not pal_ok:
        return (255, 0, 255, int(alpha))
    # multi-resolution search over RGB cube; progressively refine around best
    # steps define the half-window radius at each refinement level
    levels = [48, 24, 12, 6, 3, 1]
    # start from a decent seed: mid-gray and primaries as candidates
    seeds = [(128,128,128),(255,0,0),(0,255,0),(0,0,255),(0,255,255),(255,0,255),(255,255,0),(0,0,0),(255,255,255)]
    best_rgb = None
    best_min_d2 = -1.0
    # evaluate seeds
    for rs,gs,bs in seeds:
        ok = _srgb_u8_to_oklab(rs,gs,bs)
        mind2 = min(_oklab_dist2(ok, p) for p in pal_ok)
        if mind2>best_min_d2:
            best_min_d2 = mind2
            best_rgb = (rs,gs,bs)
    # refine
    cr, cg, cb = best_rgb
    for rad in levels:
        # build a small grid around current best; clamp to 0..255; stride = max(1, rad//2)
        stride = max(1, rad//2)
        r0 = max(0, cr - rad)
        r1 = min(255, cr + rad)
        g0 = max(0, cg - rad)
        g1 = min(255, cg + rad)
        b0 = max(0, cb - rad)
        b1 = min(255, cb + rad)
        local_best = best_rgb
        local_best_d2 = best_min_d2
        r = r0
        while r<=r1:
            g = g0
            while g<=g1:
                b = b0
                while b<=b1:
                    ok = _srgb_u8_to_oklab(r,g,b)
                    mind2 = min(_oklab_dist2(ok, p) for p in pal_ok)
                    if mind2>local_best_d2:
                        local_best_d2 = mind2
                        local_best = (r,g,b)
                    b += stride
                g += stride
            r += stride
        best_rgb = local_best
        best_min_d2 = local_best_d2
        cr, cg, cb = best_rgb
    return (best_rgb[0], best_rgb[1], best_rgb[2], int(alpha))

# ---- canvas size ops ----
def _sync_size(): dpg.set_value("input_size", (columns, rows, 0, 0))

def _add_row_top():
    global rows, y_mirror_pos
    if columns <= 0: return
    grid.append([0 for _ in range(columns)])  # add at top (visually)
    rows += 1
    _sync_size()
    create_scale_matrix(True)
    y_mirror_pos += 1
    redraw_symmetry_lines()

def _add_row_bottom():
    global rows, base_row_parity
    if columns <= 0: return
    grid.insert(0, [0 for _ in range(columns)])  # add at bottom
    base_row_parity ^= 1  # flip stagger so existing rows keep their visual parity
    rows += 1
    _sync_size()
    create_scale_matrix(True)

def _add_col_left():
    global columns, x_mirror_pos
    if rows <= 0: return
    for r in range(rows): grid[r].insert(0, 0)
    columns += 1
    _sync_size()
    create_scale_matrix(True)
    x_mirror_pos += 2
    redraw_symmetry_lines()

def _add_col_right():
    global columns
    if rows <= 0: return
    for r in range(rows): grid[r].append(0)
    columns += 1
    _sync_size()
    create_scale_matrix(True)

def _crop_canvas():
    global rows, columns, base_row_parity, grid, y_mirror_pos, x_mirror_pos
    if not grid or not grid[0]: return
    def row_empty(r): return all(v == 0 for v in r)
    def col_empty(ci): return all(grid[r][ci] == 0 for r in range(len(grid)))
    # trim empty bottom rows
    while grid and row_empty(grid[0]):
        grid.pop(0)
        base_row_parity ^= 1
    # trim empty top rows
    while grid and row_empty(grid[-1]):
        grid.pop(-1)
        y_mirror_pos -= 1
    if not grid:
        grid = [[0]]
        rows, columns, base_row_parity = 1, 1, 0
        _sync_size()
        create_scale_matrix(True)
        return
    # trim empty left columns
    while grid and len(grid[0]) > 0 and col_empty(0):
        for r in range(len(grid)): 
            grid[r].pop(0)
        x_mirror_pos -= 2
    # trim empty right columns
    while grid and len(grid[0]) > 0 and col_empty(len(grid[0]) - 1):
        for r in range(len(grid)): grid[r].pop(-1)
    # recompute dimensions from grid
    rows = len(grid)
    columns = len(grid[0]) if rows > 0 else 0
    if rows <= 0 or columns <= 0:
        grid = [[0]]
        rows, columns, base_row_parity = 1, 1, 0
    _sync_size()
    create_scale_matrix(True)

def _set_x_sym(sender, app_data):
    global x_mirror_pos
    x_mirror_pos = int(app_data)
    redraw_symmetry_lines()

def _set_y_sym(sender, app_data):
    global y_mirror_pos
    y_mirror_pos = int(app_data)
    redraw_symmetry_lines()

SYM_BTN_SIZE = 18

def _create_sym_themes():
    if not dpg.does_item_exist("sym_on_theme"):
        with dpg.theme(tag="sym_on_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (41,124,226,230))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (75,147,236,240))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (35,163,236,255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255,255,255,255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4.0)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3.0, 3.0)
    if not dpg.does_item_exist("sym_off_theme"):
        with dpg.theme(tag="sym_off_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (70,70,70,230))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (85,85,85,240))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60,60,60,255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220,220,220,255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4.0)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3.0, 3.0)

def _sync_sym_btn_visual(tag: str, enabled: bool):
    # keep label as "X" / "Y"; size enforced; theme bound for ON/OFF
    dpg.configure_item(tag, width=SYM_BTN_SIZE, height=SYM_BTN_SIZE)
    dpg.bind_item_theme(tag, "sym_on_theme" if enabled else "sym_off_theme")

def _toggle_sym(axis: str):
    global x_mirror_enabled, y_mirror_enabled
    if axis == "x":
        x_mirror_enabled = not x_mirror_enabled
        _sync_sym_btn_visual("x_toggle_btn", x_mirror_enabled)
    else:
        y_mirror_enabled = not y_mirror_enabled
        _sync_sym_btn_visual("y_toggle_btn", y_mirror_enabled)
    redraw_symmetry_lines()

def _toggle_coords():
    global coords_enabled
    coords_enabled = not coords_enabled
    create_scale_matrix(True)

# ---- encode/decode ----
# Schema (bitstream):
#   Magic (32) = 0xF1D3BA02
#   Width (8) | Height (8) | ColorCount (8)     # width=columns, height=rows, color_count excludes invisible 0
#   Colors: color_count × 3 bytes (R,G,B)
#   Scales: run-coded tokens until rows*columns items produced
#       Individual: 2b 00 | color: len(colors).bit_length()
#       Small:      2b 01 | color: len(colors).bit_length() | len:3      (stores length-1; represents 1..8)
#       Medium:     2b 10 | color: len(colors).bit_length() | len:6      (stores length-1; represents 1..64)
#       Large:      2b 11 | color: len(colors).bit_length() | len:15     (stores length-1; represents 1..32768)

_MAGIC = 0xF1D3BA02

class _BitWriter:
    def __init__(self): 
        self.buf=bytearray()
        self.acc=0
        self.bits=0
        
    def write(self, value, width):
        v=int(value)&((1<<width)-1)
        self.acc=(self.acc<<width)|v
        self.bits+=width
        while self.bits>=8:
            self.bits-=8
            self.buf.append((self.acc>>self.bits)&0xFF)
            self.acc&=(1<<self.bits)-1
            
    def bytes(self):
        if self.bits>0: self.buf.append((self.acc<<(8-self.bits))&0xFF)
        self.acc=0
        self.bits=0
        return bytes(self.buf)

class _BitReader:
    def __init__(self, data): 
        self.data=data
        self.i=0
        self.acc=0
        self.bits=0
        
    def read(self, width):
        while self.bits<width:
            if self.i>=len(self.data): raise ValueError("Unexpected end of stream")
            self.acc=(self.acc<<8)|self.data[self.i]
            self.i+=1
            self.bits+=8
        self.bits-=width
        v=(self.acc>>self.bits)&((1<<width)-1)
        self.acc&=(1<<self.bits)-1
        return v
    
def _encode_runs(flat, palette_rgb):
    w=_BitWriter()
    #print("Starting bitwriter")
    color_len = len(palette_rgb)
    color_bits = color_len.bit_length() or 1
    #print(f"{color_len} colors, {color_bits} color bits")
    w.write(_MAGIC,32)
    w.write(columns,8)
    w.write(rows,8)
    w.write(len(palette_rgb),7)
    w.write(base_row_parity,1)
    for r,g,b in palette_rgb:
        w.write(r,8); w.write(g,8)
        w.write(b,8) 
    n=len(flat)
    i=0
    while i<n:
        cid=_clamp(int(flat[i]),0,255)
        run_len=1
        while i+run_len<n and flat[i+run_len]==cid and run_len<10**9: run_len+=1
        remaining=run_len
        #print(f"Starting Block of Color: {cid} and length {remaining}")
        while remaining>0:
            if remaining==1:
                #print(f"Writing single block (00 {cid:0{color_bits}b})")
                w.write(0b00,2); w.write(cid,color_bits); remaining=0
            elif remaining<=8:
                #print(f"Writing small block (01 {cid:0{color_bits}b} {remaining-1:03b})")
                w.write(0b01,2); w.write(cid,color_bits); w.write(remaining-1,3); remaining=0
            elif remaining<=64:
                #print(f"Writing medium block (10 {cid:0{color_bits}b} {remaining-1:06b})")
                w.write(0b10,2); w.write(cid,color_bits); w.write(remaining-1,6); remaining=0
            else:
                chunk=min(32768, remaining)
                if chunk==1:
                    #print(f"Writing single block (00 {cid:0{color_bits}b})")
                    w.write(0b00,2); w.write(cid,color_bits); remaining-=1
                elif chunk<=8:
                    #print(f"Writing small block (01 {cid:0{color_bits}b} {remaining-1:03b})")
                    w.write(0b01,2); w.write(cid,color_bits); w.write(chunk-1,3); remaining-=chunk
                elif chunk<=64:
                    #print(f"Writing medium block (10 {cid:0{color_bits}b} {remaining-1:06b})")
                    w.write(0b10,2); w.write(cid,color_bits); w.write(chunk-1,6); remaining-=chunk
                else:
                    #print(f"Writing large block (11 {cid:0{color_bits}b} {remaining-1:015b})")
                    w.write(0b11,2); w.write(cid,color_bits); w.write(chunk-1,15); remaining-=chunk
        i+=run_len
    return "("+base64.b64encode(w.bytes()).decode("ascii")+")"

def _decode_runs(raw:str):
    s=raw.strip().replace(")","").replace("(","")
    data=base64.b64decode(s)
    br=_BitReader(data)
    magic=br.read(32)
    if magic!=_MAGIC: raise ValueError("Bad magic")
    columns=br.read(8)
    rows=br.read(8)
    color_count=br.read(7)
    bit=br.read(1)
    color_bits = color_count.bit_length()
    palette=[]
    for _ in range(color_count):
        r=br.read(8)
        g=br.read(8)
        b=br.read(8)
        palette.append([r,g,b,255])
    total=rows*columns
    out=[]
    while len(out)<total:
        tag=br.read(2)
        cid=br.read(color_bits)
        if tag==0b00: length=1
        elif tag==0b01: length=br.read(3)+1
        elif tag==0b10: length=br.read(6)+1
        elif tag==0b11: length=br.read(15)+1
        else: raise ValueError("Bad tag")
        out.extend([cid]*min(length, total-len(out)))
    return columns, rows, palette, out, bit

def _is_old_text_code(s:str)->bool: return s.strip().startswith('[') and '][' in s

def import_code_button(): import_code(False, dpg.get_value("code_box"))

def condense_layout(flat):
    if not flat: return flat
    out = []
    run_val = flat[0]
    run_len = 1
    for v in flat[1:]:
        if v == run_val: run_len += 1
        else:
            out.append(f"{run_len}-{run_val}" if run_len > 1 else f"{run_val}")
            run_val, run_len = v, 1
    out.append(f"{run_len}-{run_val}" if run_len > 1 else f"{run_val}")
    return out

def generate_code(for_box=True):
    flat = _flatten_grid()
    colors_rgb=[[int(c[0]),int(c[1]),int(c[2])] for c in saved_colors[1:]]
    if for_box:
        used_ids = sorted({cid for cid in flat if cid > 0})
        id_map = {0: 0}
        for new_idx, old_idx in enumerate(used_ids, start=1): id_map[old_idx] = new_idx
        remapped_flat = [id_map.get(cid, 0) for cid in flat]
        palette_rgb = []
        for idx in used_ids:
            c = saved_colors[idx]
            palette_rgb.append([int(c[0]), int(c[1]), int(c[2])])
        flat = remapped_flat
        colors_rgb = palette_rgb
    code=_encode_runs(flat, colors_rgb)
    if for_box: dpg.set_value("code_box", code)
    pyperclip.copy(code)
    return code

def import_code(from_undo, raw_code):
    global saved_colors, saved_color_texts, saved_color_groups, saved_color_icons, selected_color, base_row_parity
    if not raw_code: return
    s=str(raw_code).strip()
    return_color = None if not from_undo else selected_color
    try:
        if _is_old_text_code(s):
            # --- OLD FORMAT ---
            code=s[1:-1].replace("'","").replace(" ",""); parts=code.split('][')
            if len(parts)!=3: return
            dims=parts[0].split(','); colors_hex=parts[1].split(','); layout_tokens=parts[2].split(',')
            if len(dims)!=2 or not dims[0].isdigit() or not dims[1].isdigit(): return
            cols=int(dims[0]); rws=int(dims[1])
            dpg.set_value("input_size",(cols,rws,0,0))
            # wipe palette
            for i in range(len(saved_colors)):
                gid=dpg.get_alias_id(f"color_group_{i}"); dpg.remove_alias(f"color_group_{i}"); dpg.delete_item(gid)
                tid=dpg.get_alias_id(f"texture_{i}"); dpg.remove_alias(f"texture_{i}"); dpg.delete_item(tid)
            saved_colors.clear(); saved_color_groups.clear(); saved_color_texts.clear(); saved_color_icons.clear(); selected_color=0
            add_color_group(True); create_scale_matrix(False)
            for hex6 in colors_hex:
                if len(hex6)!=6: add_color_group(True)
                else:
                    rgba=[int(hex6[i:i+2],16) for i in (0,2,4)]+[255]; add_color_group(False, rgba)
            grid.clear(); base_row_parity=0
            for _ in range(rows): grid.append([0 for _ in range(columns)])
            idx=0
            for token in layout_tokens:
                if token.isdigit(): length, cid=1, int(token)
                else:
                    p=token.split('-')
                    if len(p)!=2 or not p[0].isdigit() or not p[1].isdigit(): continue
                    length, cid=int(p[0]), int(p[1])
                for _ in range(length):
                    if idx>=rows*columns: break
                    r=idx//columns; c=idx%columns; grid[r][c]=cid; idx+=1
            create_scale_matrix(False); save_state(); update_color_counts()
            # convert to new schema and show it
            try:
                new_code=generate_code(False); dpg.set_value("code_box", new_code)
            except Exception: pass
        else:
            # --- NEW FORMAT (base64) ---
            cols, rws, palette_rgb, flat, bit = _decode_runs(s)
            if cols<=0 or rws<=0: return
            dpg.set_value("input_size",(cols,rws,0,0))
            # wipe palette
            for i in range(len(saved_colors)):
                gid=dpg.get_alias_id(f"color_group_{i}"); dpg.remove_alias(f"color_group_{i}"); dpg.delete_item(gid)
                tid=dpg.get_alias_id(f"texture_{i}"); dpg.remove_alias(f"texture_{i}"); dpg.delete_item(tid)
            saved_colors.clear(); saved_color_groups.clear(); saved_color_texts.clear(); saved_color_icons.clear(); selected_color=0
            add_color_group(True); create_scale_matrix(False)
            for rgb in palette_rgb: add_color_group(False, [rgb[0],rgb[1],rgb[2],255])
            # rebuild grid
            grid.clear()
            base_row_parity=bit
            for _ in range(rows): grid.append([0 for _ in range(columns)])
            total=rows*columns
            for i in range(min(total, len(flat))):
                r=i//columns; c=i%columns; grid[r][c]=_clamp(flat[i],0,len(saved_colors)-1)
            create_scale_matrix(False); save_state(); update_color_counts()
        if return_color is not None and selected_color < len(saved_colors):
            _selection(saved_color_texts[return_color])
    except Exception as e:
        print(f"Import failed: {e}")

# ---- hotkeys / history ----
def number_keybind(num, *unused):
    if num is None: return
    if 0 <= num < len(saved_color_texts): _selection(saved_color_texts[num])

def switch_color():
    global selected_color, prev_selected_color
    _selection(saved_color_texts[prev_selected_color] if prev_selected_color < len(saved_colors) else saved_color_texts[0])

def undo():
    global previous_states
    if dpg.is_key_down(dpg.mvKey_Control) and previous_states:
        previous_states.pop()
        if not previous_states: previous_states = ['[0,0][ffffff][0]']
        import_code(True, previous_states[-1])

def save_state():
    global previous_states
    code = generate_code(False)
    if not previous_states or previous_states[-1] != code: previous_states.append(code)

# ---- theming & UI ----
with dpg.theme() as canvas_theme, dpg.theme_component():
    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)

with dpg.window() as window:
    with dpg.handler_registry():
        for i, key in enumerate([dpg.mvKey_0, dpg.mvKey_1, dpg.mvKey_2, dpg.mvKey_3, dpg.mvKey_4, dpg.mvKey_5, dpg.mvKey_6, dpg.mvKey_7, dpg.mvKey_8, dpg.mvKey_9]): dpg.add_key_press_handler(key, callback=(lambda *_, i=i: number_keybind(i)))
        for i, key in enumerate([dpg.mvKey_NumPad0, dpg.mvKey_NumPad1, dpg.mvKey_NumPad2, dpg.mvKey_NumPad3, dpg.mvKey_NumPad4, dpg.mvKey_NumPad5, dpg.mvKey_NumPad6, dpg.mvKey_NumPad7, dpg.mvKey_NumPad8, dpg.mvKey_NumPad9]): dpg.add_key_press_handler(key, callback=(lambda *_, i=i: number_keybind(i)))
        dpg.add_key_press_handler(dpg.mvKey_Tilde, callback=lambda: number_keybind(0))
        dpg.add_key_press_handler(dpg.mvKey_Spacebar, callback=switch_color)
        dpg.add_key_press_handler(dpg.mvKey_Z, callback=undo)

    with dpg.group(horizontal=True):
        with dpg.child_window(width=canvas_x, height=canvas_y) as canvas:
            dpg.bind_item_theme(canvas, canvas_theme)
            drawlist = dpg.add_drawlist(width=canvas_x, height=canvas_y)
            with dpg.item_handler_registry() as registry:
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Left, callback=click_handler)
            dpg.bind_item_handler_registry(drawlist, registry)

        with dpg.child_window(border=False):
            dpg.add_button(label="New Color", width=color_bar_width, callback=lambda: add_color_group(False))
            color_selector = dpg.child_window(width=color_bar_width, height=250, label="Color Selector", tag="color_selector")
            with color_selector:
                def _selection(sender):
                    global selected_color, prev_selected_color
                    prev_selected_color = selected_color
                    selected_color = saved_color_texts.index(sender)
                    for item in saved_color_texts: dpg.set_value(item, item == sender)
                add_color_group(True)
                add_color_group()
            dpg.add_text("    Width | Height")
            dpg.add_input_intx(tag="input_size", width=color_bar_width, default_value=[15, 20], size=2, min_value=1, min_clamped=True)
            dpg.add_button(label="Make Scale Grid", width=color_bar_width, callback=make_new_grid)
            dpg.add_text("")
            dpg.add_button(label="Export", width=color_bar_width, callback=lambda: generate_code(True))
            dpg.add_input_text(tag="code_box", width=color_bar_width, hint="Code") 
            dpg.add_button(label="Import", width=color_bar_width, callback=import_code_button)
            dpg.add_text("")
            dpg.add_text("    Canvas Resize")
            dpg.add_button(label="Add Top Row", width=color_bar_width, callback=_add_row_top)
            dpg.add_button(label="Add Bottom Row", width=color_bar_width, callback=_add_row_bottom)
            dpg.add_button(label="Add Left Column", width=color_bar_width, callback=_add_col_left)
            dpg.add_button(label="Add Right Column", width=color_bar_width, callback=_add_col_right)
            dpg.add_button(label="Crop Canvas", width=color_bar_width, callback=_crop_canvas)
            dpg.add_text("")
            dpg.add_text("       Symmetry")
            _create_sym_themes()
            slider_w = max(0, color_bar_width - SYM_BTN_SIZE - 6)
            # X row
            with dpg.group(horizontal=True):
                dpg.add_button(tag="x_toggle_btn", label="X", width=SYM_BTN_SIZE, height=SYM_BTN_SIZE, callback=lambda: _toggle_sym("x"))
                dpg.add_slider_float(tag="x_mirror_slider", label="", width=slider_w, min_value=1.0, max_value=max(1, 2*(columns - 1)), default_value=int(x_mirror_pos), callback=_set_x_sym, format='%.0f')
            # Y row
            with dpg.group(horizontal=True):
                dpg.add_button(tag="y_toggle_btn", label="Y", width=SYM_BTN_SIZE, height=SYM_BTN_SIZE, callback=lambda: _toggle_sym("y"))
                dpg.add_slider_float(tag="y_mirror_slider", label="", width=slider_w, min_value=2.0, max_value=max(2, rows - 1), default_value=int(y_mirror_pos), callback=_set_y_sym, format='%.0f')
            # initial visuals
            _sync_sym_btn_visual("x_toggle_btn", x_mirror_enabled)
            _sync_sym_btn_visual("y_toggle_btn", y_mirror_enabled)
            dpg.add_text("")
            dpg.add_button(label="Toggle Coords", width=color_bar_width, callback=_toggle_coords)

dpg.set_primary_window(window, True)
dpg.create_viewport(width=window_width, height=window_height, title="Boris's Scalemail Planner", small_icon=resource_path("icon_small.png"), large_icon=resource_path("icon_big.png"))
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

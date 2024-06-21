import re
from xml.etree import ElementTree as ET
import math

def svg_to_obj(svg_file, obj_file):
    tree = ET.parse(svg_file)
    root = tree.getroot()

    vertices = []
    faces = []

    def add_rectangle(x, y, width, height, depth):
        idx = len(vertices) + 1
        vertices.extend([
            (x, y, 0),
            (x + width, y, 0),
            (x + width, y + height, 0),
            (x, y + height, 0),
            (x, y, depth),
            (x + width, y, depth),
            (x + width, y + height, depth),
            (x, y + height, depth)
        ])
        faces.extend([
            (idx, idx+1, idx+2, idx+3),
            (idx+4, idx+5, idx+6, idx+7),
            (idx, idx+1, idx+5, idx+4),
            (idx+1, idx+2, idx+6, idx+5),
            (idx+2, idx+3, idx+7, idx+6),
            (idx+3, idx, idx+4, idx+7)
        ])

    def add_line(x1, y1, x2, y2, width, depth):
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        idx = len(vertices) + 1
        vertices.extend([
            (x1 + nx * width / 2, y1 + ny * width / 2, 0),
            (x1 - nx * width / 2, y1 - ny * width / 2, 0),
            (x2 - nx * width / 2, y2 - ny * width / 2, 0),
            (x2 + nx * width / 2, y2 + ny * width / 2, 0),
            (x1 + nx * width / 2, y1 + ny * width / 2, depth),
            (x1 - nx * width / 2, y1 - ny * width / 2, depth),
            (x2 - nx * width / 2, y2 - ny * width / 2, depth),
            (x2 + nx * width / 2, y2 + ny * width / 2, depth)
        ])
        faces.extend([
            (idx, idx+1, idx+2, idx+3),
            (idx+4, idx+5, idx+6, idx+7),
            (idx, idx+1, idx+5, idx+4),
            (idx+1, idx+2, idx+6, idx+5),
            (idx+2, idx+3, idx+7, idx+6),
            (idx+3, idx, idx+4, idx+7)
        ])

    def add_arc(cx, cy, rx, ry, start_angle, end_angle, width, depth):
        segments = 20
        angle_diff = (end_angle - start_angle) / segments
        points = []
        for i in range(segments + 1):
            angle = start_angle + i * angle_diff
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            points.append((x, y))
        for i in range(len(points) - 1):
            add_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], width, depth)

    def svg_arc_to_center(x1, y1, rx, ry, phi, fA, fS, x2, y2):
        phi = math.radians(phi)
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)

        x1_prime = cos_phi * (x1 - x2) / 2.0 + sin_phi * (y1 - y2) / 2.0
        y1_prime = -sin_phi * (x1 - x2) / 2.0 + cos_phi * (y1 - y2) / 2.0

        rx_sq = rx * rx
        ry_sq = ry * ry
        x1_prime_sq = x1_prime * x1_prime
        y1_prime_sq = y1_prime * y1_prime

        radicant = (rx_sq * ry_sq - rx_sq * y1_prime_sq - ry_sq * x1_prime_sq) / (rx_sq * y1_prime_sq + ry_sq * x1_prime_sq)
        radicant = max(0, radicant)
        c_prime = math.sqrt(radicant) * (1 if fA != fS else -1)
        cx_prime = c_prime * rx * y1_prime / ry
        cy_prime = c_prime * -ry * x1_prime / rx

        cx = cos_phi * cx_prime - sin_phi * cy_prime + (x1 + x2) / 2
        cy = sin_phi * cx_prime + cos_phi * cy_prime + (y1 + y2) / 2

        start_angle = math.atan2((y1_prime - cy_prime) / ry, (x1_prime - cx_prime) / rx)
        end_angle = math.atan2((-y1_prime - cy_prime) / ry, (-x1_prime - cx_prime) / rx)
        if not fS and end_angle > start_angle:
            end_angle -= 2 * math.pi
        elif fS and end_angle < start_angle:
            end_angle += 2 * math.pi

        return cx, cy, start_angle, end_angle

    for element in root.iter():
        if element.tag.endswith('rect'):
            x = float(element.get('x', 0))
            y = float(element.get('y', 0))
            width = float(element.get('width', 0))
            height = float(element.get('height', 0))
            add_rectangle(x, y, width, height, 0)

        if element.tag.endswith('path'):
            d = element.get('d')
            print(d)
            path_commands = re.findall(r'([MLA])([^MLA]*)', d)
            print(path_commands)
            for command, params_str in path_commands:
                params = list(map(float, re.findall(r'-?\d*\.?\d+', params_str)))
                if command == 'M':
                    x, y = params
                elif command == 'L':
                    x1, y1, x2, y2 = x, y, params[0], params[1]
                    add_line(x1, y1, x2, y2, 0.02, 0)
                    x, y = x2, y2
                elif command == 'A':
                    rx, ry, phi, large_arc_flag, sweep_flag, x2, y2 = params
                    cx, cy, start_angle, end_angle = svg_arc_to_center(x, y, rx, ry, phi, large_arc_flag, sweep_flag, x2, y2)
                    add_arc(cx, cy, rx, ry, start_angle, end_angle, 0.02, 0)
                    x, y = x2, y2

    with open(obj_file, 'w') as f:
        for v in vertices:
            f.write(f'v {v[0]} {v[1]} {v[2]}\n')
        for face in faces:
            f.write(f'f {face[0]} {face[1]} {face[2]} {face[3]}\n')


svg_to_obj('resources/office_straighty.svg', 'resources/office_straighty.obj')
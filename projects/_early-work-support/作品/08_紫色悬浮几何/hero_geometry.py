"""Editable procedural hero surfaces; local XY is the view plane, +Z faces camera."""
import math
import bpy


class SurfaceGraph:
    def __init__(self, name):
        self.group = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        self.group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        self.nodes, self.links = self.group.nodes, self.group.links
        self.inp = self.nodes.new('NodeGroupInput')
        self.inp.location = (-1200, 400)
        self.out = self.nodes.new('NodeGroupOutput')
        self.out.location = (1500, 400)
        self.count = 0

    def socket(self, name, value, lo, hi, integer=False):
        sock = self.group.interface.new_socket(name=name, in_out='INPUT', socket_type='NodeSocketInt' if integer else 'NodeSocketFloat')
        sock.default_value, sock.min_value, sock.max_value = value, lo, hi
        return self.inp.outputs[name]

    def node(self, kind, label, loc):
        node = self.nodes.new(kind)
        node.label = node.name = label
        node.location = loc
        node.width = 175
        return node

    def wire(self, source, target):
        if isinstance(source, (int, float)):
            target.default_value = source
        else:
            self.links.new(source, target)

    def math(self, op, a, b=None, label=None):
        column, row = self.count // 8, self.count % 8
        node = self.node('ShaderNodeMath', label or op, (-920 + column * 215, 100 - row * 145))
        self.count += 1
        node.operation = op
        self.wire(a, node.inputs[0])
        if b is not None:
            self.wire(b, node.inputs[1])
        return node.outputs[0]

    def grid_coordinates(self, nx, ny):
        grid = self.node('GeometryNodeMeshGrid', '01 • Sampling grid / 参数采样网格', (-1200, 800))
        grid.inputs['Size X'].default_value = 1
        grid.inputs['Size Y'].default_value = 1
        grid.inputs['Vertices X'].default_value = nx
        grid.inputs['Vertices Y'].default_value = ny
        pos = self.node('GeometryNodeInputPosition', 'Normalized grid coordinates', (-1400, 0))
        sep = self.node('ShaderNodeSeparateXYZ', 'u, v coordinates', (-1200, 0))
        self.links.new(pos.outputs['Position'], sep.inputs[0])
        return grid, sep.outputs['X'], sep.outputs['Y']

    def finish(self, obj, grid, xyz, material, merge=False):
        combine = self.node('ShaderNodeCombineXYZ', '02 • Parametric surface / 参数曲面', (650, 700))
        for i, value in enumerate(xyz):
            self.wire(value, combine.inputs[i])
        position = self.node('GeometryNodeSetPosition', '03 • Build surface / 曲面成形', (850, 800))
        self.links.new(grid.outputs['Mesh'], position.inputs['Geometry'])
        self.links.new(combine.outputs[0], position.inputs['Position'])
        geom = position.outputs['Geometry']
        if merge:
            weld = self.node('GeometryNodeMergeByDistance', '04 • Close periodic seams / 闭合接缝', (1060, 800))
            weld.inputs['Distance'].default_value = .00001
            self.links.new(geom, weld.inputs['Geometry'])
            geom = weld.outputs['Geometry']
        smooth = self.node('GeometryNodeSetShadeSmooth', '05 • Smooth folded surface', (1060, 550))
        smooth.domain = 'FACE'
        self.links.new(geom, smooth.inputs['Geometry'])
        geom = smooth.outputs['Geometry']
        if material:
            obj.data.materials.append(material)
            mat = self.node('GeometryNodeSetMaterial', '06 • Hero material', (1270, 550))
            mat.inputs['Material'].default_value = material
            self.links.new(geom, mat.inputs['Geometry'])
            geom = mat.outputs['Geometry']
        self.links.new(geom, self.out.inputs['Geometry'])
        modifier = obj.modifiers.new('Live surface parameters / 实时曲面参数', 'NODES')
        modifier.node_group = self.group
        return obj


def empty_surface(name):
    mesh = bpy.data.meshes.new(name + ' • generated grid')
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build_pleated_orb(name, material, radius=1.08, ribs=64):
    """Small-opening, deep pleated horn torus with editable GN parameters.

    Outer radius is radius; the central aperture is only about 3% of it.
    Best seen with its +Z axis tipped slightly toward screen upper left.
    """
    obj = empty_surface(name)
    g = SurfaceGraph(name + ' • Pleated Orb / 密褶鼓球')
    rad = g.socket('Radius / 外半径', radius, .01, 20)
    folds = g.socket('Ribs / 经向褶数', ribs, 8, 128, integer=True)
    depth_ratio = g.socket('Fold depth / 褶深比例', .052, .001, .13)
    opening = g.socket('Opening / 凹心比例', .028, .008, .25)
    profile = g.socket('Body depth / 鼓身深度', .67, .25, 1.1)
    inner_lift = g.socket('Dimple lift / 凹心前移', .78, 0, 1.2)
    twist = g.socket('Pleat sweep / 褶线旋度', .115, -.7, .7)
    grid, u, v = g.grid_coordinates(769, 145)
    theta = g.math('MULTIPLY', g.math('ADD', u, .5, 'Longitude 0—1'), math.tau, 'Longitude angle')
    phi = g.math('MULTIPLY', g.math('ADD', v, .5, 'Profile 0—1'), math.tau, 'Profile angle')
    cp = g.math('COSINE', phi, label='Profile cosine')
    sp = g.math('SINE', phi, label='Profile sine')
    angle = g.math('ADD', theta, g.math('MULTIPLY', sp, twist, 'Soft pleat sweep'), 'Swept longitude')
    rib_cos = g.math('COSINE', g.math('MULTIPLY', theta, folds, 'Periodic rib angle'), label='Rounded pleat waveform')
    rib_wave = g.math('MULTIPLY', g.math('ADD', rib_cos, 1, 'Pleat 0—2'), .5, 'Pleat 0—1')
    hole_radius = g.math('MULTIPLY', rad, opening, 'Small dimple radius')
    major = g.math('MULTIPLY', g.math('ADD', rad, hole_radius, 'Outer + inner radius'), .5, 'Profile center radius')
    minor = g.math('MULTIPLY', g.math('SUBTRACT', rad, hole_radius, 'Outer − inner radius'), .5, 'Profile section radius')
    depth = g.math('MULTIPLY', rad, depth_ratio, 'Absolute groove depth')
    folded_minor = g.math('SUBTRACT', minor, g.math('MULTIPLY', rib_wave, depth, 'Recessed pleat valleys'), 'Folded profile radius')
    rho = g.math('ADD', major, g.math('MULTIPLY', folded_minor, cp, 'Radial profile'), 'Distance from axis')
    x = g.math('MULTIPLY', rho, g.math('COSINE', angle, label='Longitude cosine'), 'Surface X')
    y = g.math('MULTIPLY', rho, g.math('SINE', angle, label='Longitude sine'), 'Surface Y')
    flatten = g.math('DIVIDE', folded_minor, minor, 'Pleat normal-depth factor')
    axial = g.math('MULTIPLY', g.math('MULTIPLY', rad, profile, 'Axial body depth'), g.math('MULTIPLY', sp, flatten, 'Folded axial profile'), 'Folded axial depth')
    lift = g.math('MULTIPLY', g.math('MULTIPLY', rad, inner_lift, 'Inner rim forward distance'), g.math('MULTIPLY', g.math('SUBTRACT', 1, cp, 'Inner-side weight'), .5, 'Forward-rim weight'), 'Raised shallow dimple')
    z = g.math('ADD', axial, lift, 'Surface Z')
    obj['shape_note'] = 'True periodic Grid → Set Position surface; small closed inner rim, 64 continuous meridian pleats.'
    return g.finish(obj, grid, (x, y, z), material, merge=True)


def build_ripple_sheet(name, material, width=1.55, height=.62, depth=.15):
    """A bowed continuous corrugated ribbon with editable GN and thin-shell modifiers."""
    obj = empty_surface(name)
    g = SurfaceGraph(name + ' • Ripple Sheet / 波纹薄片')
    w = g.socket('Width / 宽度', width, .01, 20)
    h = g.socket('Height / 高度', height, .01, 20)
    amp = g.socket('Ripple depth / 波纹深度', depth, .001, 1)
    waves = g.socket('Ripple count / 波纹数量', 9, 2, 32, integer=True)
    curl = g.socket('Bow / 整体弯曲', .27, -1, 1)
    grid, u, v = g.grid_coordinates(217, 17)
    phase = g.math('MULTIPLY', g.math('MULTIPLY', g.math('ADD', u, .5, 'Horizontal 0—1'), waves, 'Wave periods'), math.tau, 'Wave phase')
    cosine = g.math('COSINE', phase, label='Continuous corrugation')
    square = g.math('MULTIPLY', u, u, 'Horizontal bow profile')
    x = g.math('MULTIPLY', u, w, 'Surface X')
    arch = g.math('MULTIPLY', g.math('SUBTRACT', 1, g.math('MULTIPLY', square, 4, 'Normalized bow'), 'Crown arch'), g.math('MULTIPLY', h, .20, 'Crown amount'), 'Soft upper arch')
    y = g.math('ADD', g.math('MULTIPLY', v, h, 'Ribbon span'), g.math('ADD', arch, g.math('MULTIPLY', cosine, .012, 'Soft scalloped edge'), 'Crown + scallop'), 'Surface Y')
    z = g.math('ADD', g.math('MULTIPLY', g.math('MULTIPLY', cosine, amp, 'Corrugation amplitude'), .5, 'Half ripple depth'), g.math('MULTIPLY', square, g.math('MULTIPLY', curl, 4, 'Bow coefficient'), 'Overall cupping'), 'Surface Z')
    g.finish(obj, grid, (x, y, z), material)
    solid = obj.modifiers.new('Thin physical shell / 实体薄壳', 'SOLIDIFY')
    solid.thickness = .028
    solid.offset = 0
    solid.use_even_offset = True
    bevel = obj.modifiers.new('Soft edge light / 边缘柔和高光', 'BEVEL')
    bevel.width, bevel.segments = .009, 3
    obj['shape_note'] = 'Live Grid → Set Position corrugation, crown and cupping; Solidify and Bevel remain editable.'
    return obj

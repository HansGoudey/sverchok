
import numpy as np
from math import pi

import bpy
from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.surface.sphere import SvLambertSphere, SvEquirectSphere, SvGallSphere, SvDefaultSphere
from sverchok.utils.surface.algorithms import build_nurbs_sphere

class SvSphereNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Sphere
    Tooltip: Generate spherical surface (different projections are available)
    """
    bl_idname = 'SvExSphereNode'
    bl_label = 'Sphere (Surface)'
    bl_icon = 'MESH_UVSPHERE'

    projections = [
        ('DEFAULT', "Default", "Based on spherical coordinates", 0),
        ('EQUIRECT', "Equirectangular", "Equirectangular (geographic) projection", 1),
        ('LAMBERT', "Lambert", "Lambert cylindrical equal-area projection", 2),
        ('GALL', "Gall Stereographic", "Gall stereographic projection", 3),
        ('NURBS', "NURBS Sphere", "NURBS Sphere", 4)
    ]

    def update_sockets(self, context):
        self.inputs['Theta1'].hide_safe = self.projection != 'EQUIRECT'
        updateNode(self, context)

    projection : EnumProperty(
        name = "Projection",
        items = projections,
        default = 'DEFAULT',
        update = update_sockets)

    radius : FloatProperty(
        name = "Radius",
        default = 1.0,
        update = updateNode)

    theta1 : FloatProperty(
        name = "Theta1",
        description = "standard parallels (north and south of the equator) where the scale of the projection is true",
        default = pi/4,
        min = 0, max = pi/2,
        update = updateNode)

    def sv_init(self, context):
        p = self.inputs.new('SvVerticesSocket', "Center")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvStringsSocket', "Theta1").prop_name = 'theta1'
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "projection")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        center_s = self.inputs['Center'].sv_get()
        center_s = ensure_nesting_level(center_s, 3)
        radius_s = self.inputs['Radius'].sv_get()
        radius_s = ensure_nesting_level(radius_s, 2)
        theta1_s = self.inputs['Theta1'].sv_get()
        theta1_s = ensure_nesting_level(theta1_s, 2)

        surfaces_out = []
        for centers, radiuses, theta1s in zip_long_repeat(center_s, radius_s, theta1_s):
            for center, radius, theta1 in zip_long_repeat(centers, radiuses, theta1s):
                if self.projection == 'DEFAULT':
                    surface = SvDefaultSphere(np.array(center), radius)
                elif self.projection == 'EQUIRECT':
                    surface = SvEquirectSphere(np.array(center), radius, theta1)
                elif self.projection == 'LAMBERT':
                    surface = SvLambertSphere(np.array(center), radius)
                elif self.projection == 'GALL':
                    surface = SvGallSphere(np.array(center), radius)
                elif self.projection == 'NURBS':
                    surface = build_nurbs_sphere(np.array(center), radius)
                else:
                    raise Exception("Unsupported projection type")
                surfaces_out.append(surface)
        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvSphereNode)

def unregister():
    bpy.utils.unregister_class(SvSphereNode)


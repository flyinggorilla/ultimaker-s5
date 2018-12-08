# Ultimaker S5 Materials Management Tool and FormFutura Materials

I am going to share my experiences with Ultimaker S5 here. My first "hack" is to add FormFutura filaments to the printers display menu, to properly support the load/unload capabilities. Similarily I will publish and update also Cura material profiles for selected FormFutura materials.

## Custom Material Upload Tool

Uploading filament profiles via REST API to printer to add custom print profiles. e.g. I wanted that ASA (FormFutura ApolloX) and high-temperature PVA (FormFuture Helios) is selectable in the touch display.

![display materialtype](display_materialtype.jpg)

Therefore use the python tool (tested with Python 3.7+) ums5material.py

## Installing ums5material

1. clone or copy from github


1. python -m pip install requests
1. python -m pip install untangle
1. python -m pip install pyyaml
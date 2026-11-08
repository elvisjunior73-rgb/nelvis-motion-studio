"""Natron render script, executed by NatronRenderer."""
import os

def createInstance(app, group):
    source = os.environ["NELVIS_NATRON_SOURCE"]
    output = os.environ["NELVIS_NATRON_OUTPUT"]
    reader = app.createReader(source)
    grade = app.createNode("net.sf.openfx.ColorCorrectPlugin")
    grade.connectInput(0, reader)
    writer = app.createWriter(output)
    writer.connectInput(0, grade)
    writer.setScriptName("WriteNelvis")

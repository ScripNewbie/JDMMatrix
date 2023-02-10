import os
import math
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color, Line
from kivy.utils import get_color_from_hex as GetColor
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.properties import NumericProperty
from plyer import filechooser

from src import CustomWidget

class Nodes(Widget):
    
    def __init__(self, pos, node, **kwargs):
        super().__init__(**kwargs)
        self.node = node
        self.position = pos
        self.size = (dp(15), dp(15))
        self.displayLabelPos()
    
    def displayLabelPos(self):
        self.label = Label(
            color=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_TEXT), text=str(self.position),
            pos=(self.x, self.y+dp(10)), size=self.size,
            font_name = "consolas"
        )
        self.bind(pos=self.changePos)
    
    def changePos(self, *_):
        self.label.pos = self.x, self.y-dp(20)
    
    def setPosition(self):
        parent = self.parent.parent.parent
        if parent:
            self.x = parent.cameraX+parent.pos_[0]+parent.width_/2 + (self.position[0]*parent.blockPadding) - self.width/2
            self.y = parent.cameraY+parent.pos_[1]+parent.height_/2 + (self.position[1]*parent.blockPadding) - self.height/2
            self.label.text = str(f"({round(round(self.position[0]*100, 2)/100, 1)}, {round(round(self.position[1]*100, 2)/100, 1)})")
            if self.parent.changeMode: self.parent.changeLine()
            if self.parent.changeMode: self.parent.changeAngleLabel()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):      
            if self.parent.parent.parent.grabbing is None:
                self.parent.parent.parent.grabbing = self
                self.old_X = self.position[0]
                self.old_Y = self.position[1]
                self.grabX = touch.x
                self.grabY = touch.y
                self.parent.parent.parent.de_Select_line()
                self.parent.parent.parent.setGridValue(self.parent)

                self.parent.arrow.img.color = GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_ACTIVE)
                self.parent.color.rgb = GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_ACTIVE)
                if self.parent.parent.parent.show_Coords is False:
                    self.parent.node1.add_widget(self.parent.node1.label)
                    self.parent.node2.add_widget(self.parent.node2.label)
                self.parent.parent.parent.line_selected = self.parent
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        parent = self.parent.parent.parent
        if parent.grabbing is self:
            self.position = ((self.old_X*parent.blockPadding + (touch.x - self.grabX)) / parent.blockPadding,
                             (self.old_Y*parent.blockPadding + (touch.y - self.grabY)) / parent.blockPadding)
            self.setPosition()
            self.parent.parent.parent.setGridValue(self.parent)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.parent.parent.parent.grabbing is self:
            self.parent.parent.parent.grabbing = None
            self.position = (round(round(self.position[0]*100, 2)/100, 1),
                             round(round(self.position[1]*100, 2)/100, 1))
            self.setPosition()
            self.parent.parent.parent.setGridValue(self.parent)
        return super().on_touch_up(touch)

class Arrow(Scatter):
    
    def __init__(self, pos, **kwargs):
        super().__init__(**kwargs)
        self.size = (1, 1)
        self.pos = pos
        self.disabled = True
        self.auto_bring_to_front = False
        self.img = Image(
            color=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_NACTIVE),
            size=(dp(25), dp(20)), pos=(dp(18)*-0.2, dp(10)*-0.2),
            source="asset/triangle.png", opacity=1
        )
        self.add_widget(self.img)

class NodeLine(Widget):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle : int = 0
        self.changeMode = True
        self.node1 = Nodes((1, 1), 1)
        self.node2 = Nodes((0, 0), 2)
        self.arrow = Arrow(self.node1.pos)
        self.add_widget(self.node1)
        self.add_widget(self.node2)
        self.add_widget(self.arrow)
        self.displayLineName()
        self.displayLine()
        self.changeLine()
    
    def displayLineName(self):
        self.name_Label = Label(
            font_size=dp(20),
            font_name="consolas", size=(dp(30), dp(30)),
            color=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_TEXT))
        self.add_widget(self.name_Label)

    def getSlope(self, x1, x2, y1, y2):
        dx = x2 - x1
        dy = y2 - y1
        theta = math.atan2(dy, dx)
        theta *= 180 / math.pi
        self.angle = theta + 180
        return theta - 29

    def update2Nodeposition(self):
        self.changeMode = False
        self.node1.setPosition()
        self.node2.setPosition()
        self.changeMode = True
        self.changeLine()

    def displayLine(self):
        with self.canvas:
            self.color = Color(rgb=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_NACTIVE), a=0.5)
            self.line = Line(width=dp(2))

    def changeLine(self):
        self.line.points=[self.node1.x+(self.node1.width/2), self.node1.y+(self.node1.height/2),
            self.node2.x+(self.node2.width/2), self.node2.y+(self.node2.height/2)]
        self.name_Label.pos = ((self.node1.x+self.node2.x)/2 - dp(15), (self.node1.y+self.node2.y)/2 - dp(15))
        self.arrow.pos = self.node1.x+(self.node1.width/2), self.node1.y+(self.node1.height/2)
    
    def changeAngleLabel(self):
        if self.parent: self.parent.parent.updateAllStats()
        self.arrow.rotation = self.getSlope(self.node1.x, self.node2.x, self.node1.y, self.node2.y)

class CustomTextInput(TextInput):
    
    def __init__(self, text_hint, index=0, **kwargs):
        super().__init__(**kwargs)
        col = App.get_running_app().CT.CurrentTheme
        self.foreground_color = GetColor(col.MATRIX_ENTRY_FG)
        self.hint_text_color = GetColor(col.MATRIX_ENTRY_FG)
        self.selection_color = GetColor(col.MATRIX_ENTRY_SELECTION)
        self.cursor_color = GetColor(col.MATRIX_ENTRY_CURSOR)
        self.background_color = GetColor(col.MATRIX_ENTRY_COLOR)
        self.index = index
        self.background_normal = ""
        self.background_active = ""
        self.hint_text = text_hint
        self.multiline = False
        self.write_tab = False
        self.font_name = "consolas"
        self.bind(text=self.changeNodePosition)

    def on_focus(self, _, focus):
        if focus: Clock.schedule_once(lambda _: self.select_all(), 0.2)

    def changeNodePosition(self, *_):
        widget = self.parent.parent.parent.line_selected
        if self.parent.parent.parent.stop_text is False and widget:
            for child in self.parent.children:
                try: num = float(child.text)
                except ValueError: num = 0
                if child.index == 0:
                    widget.node1.position = (num, widget.node1.position[1])
                    widget.node1.setPosition()
                elif child.index == 1:
                    widget.node1.position = (widget.node1.position[1], num)
                    widget.node1.setPosition()
                elif child.index == 2:
                    widget.node2.position = (num, widget.node2.position[1])
                    widget.node2.setPosition()
                elif child.index == 3:
                    widget.node2.position = (widget.node2.position[1], num)
                    widget.node2.setPosition()

class CustomButt(CustomWidget):
    
    def __init__(self, num: int, name: str, dir: str = 'u', **kwargs):
        pos = (Window.width / 8 * num + dp(10) + (dp(5) * num),
               ((Window.height-dp(30)) if dir == 'u' else dp(20)) - dp(10))
        size = (Window.width/8, dp(30))
        super().__init__(pos, size, name, True, **kwargs)

class CustomLab(Label):

    def __init__(self, num: str, **kwargs):
        super().__init__(**kwargs)
        self.font_name = "consolas"
        self.halign = 'left'
        self.valign = 'center'
        self.color = GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_STATS)
        self.bind(size=self.setter('text_size'))
        self.pos = (dp(10), (Window.height-dp(70) - dp(20)*num))
        self.size = (Window.width, dp(20))

class Graph(Widget):

    cols = NumericProperty(100)
    rows = NumericProperty(100)
    cameraX = NumericProperty(0)
    cameraY = NumericProperty(0)
    blockPadding = NumericProperty(dp(50))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allVariable()
        self.allList()
        self.displayButton()
        self.allStats()
        self.displayAll()

    def allVariable(self):
        self.grabbing : Widget = None
        self.line_selected : NodeLine = None
        self.stop_text : bool = False
        self.show_Coords : bool = False
        self.minimum_size : int = dp(10)
        self.maximum_size : int = dp(100)
        self.mainPath = App.get_running_app().Matrixconfig.get("GraphMainPath")

    def allList(self):
        self.all_Line_ver : list[Line] = list()
        self.all_Line_hor : list[Line] = list()
        self.all_nodes_line : list[NodeLine] = list()
        self.all_horizontal : Label = list()
        self.all_vertical : Label = list()

    def displayButton(self):
        self.allButton = Widget()
        self.allButton.add_widget(zoomIn:=CustomButt(0, "Zoom In"))
        self.allButton.add_widget(zoomOut:=CustomButt(1, "Zoom Out"))
        self.allButton.add_widget(AddLine:=CustomButt(2, "Add"))
        self.allButton.add_widget(deleteLine:=CustomButt(3, "Delete"))
        self.allButton.add_widget(saveGraph:=CustomButt(0, "Save", 'd'))
        self.allButton.add_widget(deselect:=CustomButt(1, "DeSel", 'd'))
        self.allButton.add_widget(clearLine:=CustomButt(2, "Clear", 'd'))
        self.allButton.add_widget(showCoords:=CustomButt(3, "Coords", 'd'))

        zoomIn.func_binder = lambda *_: self.zoom_in()
        zoomOut.func_binder = lambda *_: self.zoom_out()
        AddLine.func_binder = lambda *_: self.addNodeLine()
        deleteLine.func_binder = lambda *_: self.deleteNodeLine()
        saveGraph.func_binder = lambda *_ : self.saveGraphFunction()
        deselect.func_binder = lambda *_ : self.de_Select_line()
        clearLine.func_binder = lambda *_: self.removeAllNodes()
        showCoords.func_binder = lambda *_ : self.showAllCoords()

        self.grid = GridLayout(
            cols=2, rows=2, size=(Window.width/7*2, dp(50)),
            pos=(Window.width-(Window.width/7*2)-dp(10), Window.height-dp(50)-dp(10)),
            spacing=dp(1), padding=dp(1)
        )
        with self.grid.canvas.before:
            Color(rgb=GetColor(App.get_running_app().CT.CurrentTheme.RESULT_LINE))
            Rectangle(size=self.grid.size, pos=self.grid.pos)

        self.grid.add_widget(CustomTextInput("N1-X", 0))
        self.grid.add_widget(CustomTextInput("N1-Y", 1))
        self.grid.add_widget(CustomTextInput("N2-X", 2))
        self.grid.add_widget(CustomTextInput("N2-Y", 3))
        self.allButton.add_widget(self.grid)

    def setSaveWindowSize(self):
        self.saveWin = Widget()
        maxx = maxy = 5
        for node in self.all_nodes_line:
            if node.node1.position[0] > maxx:
                maxx = node.node1.position[0] + 1
            if node.node2.position[0] > maxx:
                maxx = node.node2.position[0] + 1
            if node.node1.position[1] > maxy:
                maxy = node.node1.position[1] + 1
            if node.node2.position[1] > maxy:
                maxy = node.node2.position[1] + 1
        self.pos = ((self.pos_[0]+(self.width_/2)) + self.cameraX - (maxx * self.blockPadding),
                    (self.pos_[1]+(self.height_/2)) + self.cameraY - (maxy * self.blockPadding))
        self.size = (((maxx * self.blockPadding) * 2), ((maxy * self.blockPadding) * 2))

    def saveGraphFunction(self):
        self.createDir()
        self.de_Select_line()
        self.remove_widget(self.allButton)
        self.remove_widget(self.allStatsLabel)

        self.width_ = self.blockPadding*(self.cols*2+1)
        self.height_ = self.blockPadding*(self.rows*2+1)
        self.pos_ = (Window.width/2-self.width_/2, Window.height/2-self.height_/2)
        self.setAllNodes()
        self.updateCanvas(allLine=True)
        Clock.schedule_once(lambda _: self.saveCanvas(), 0.05)
        Clock.schedule_once(lambda _: self.re_addAll(), 0.1)

    def saveCanvas(self):
        self.setSaveWindowSize()
        self.mainBgRect.size = self.size
        self.mainBgRect.pos = self.pos
        self.export_to_png(self.mainPath + f"/graph{App.get_running_app().graphSave}.png", 5)
        App.get_running_app().graphSave += 1

    def re_addAll(self):
        self.add_widget(self.allButton)
        self.add_widget(self.allStatsLabel)
        self.mainBgRect.size = Window.size
        self.mainBgRect.pos = (0, 0)

    def createDir(self):
        if self.mainPath is None or not os.path.exists(self.mainPath):
            self.mainPath = filechooser.choose_dir()[0]
        App.get_running_app().Matrixconfig["GraphMainPath"] = self.mainPath

    def de_Select_line(self):
        if self.line_selected:
            self.line_selected.arrow.img.color = GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_NACTIVE)
            self.line_selected.color.rgb = GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_ARROW_NACTIVE)
            if self.show_Coords is False:
                self.line_selected.node1.remove_widget(self.line_selected.node1.label)
                self.line_selected.node2.remove_widget(self.line_selected.node2.label)
        self.resetVariable()

    def showAllCoords(self):
        self.show_Coords = not self.show_Coords
        for node in self.all_nodes_line:
            if node is not self.line_selected:
                node.node1.remove_widget(node.node1.label)
                node.node2.remove_widget(node.node2.label)
                if self.show_Coords:
                    node.node1.add_widget(node.node1.label)
                    node.node2.add_widget(node.node2.label)
                    

    def setGridValue(self, widget=None):
        self.stop_text = True
        self.grid.children[0].text = "N2-Y" if widget is None else str(round(round(widget.node2.position[1]*100, 2)/100, 1))
        self.grid.children[1].text = "N2-X" if widget is None else str(round(round(widget.node2.position[0]*100, 2)/100, 1))
        self.grid.children[2].text = "N1-Y" if widget is None else str(round(round(widget.node1.position[1]*100, 2)/100, 1))
        self.grid.children[3].text = "N1-X" if widget is None else str(round(round(widget.node1.position[0]*100, 2)/100, 1))
        self.stop_text = False

    def allStats(self):
        self.allStatsLabel = Widget()
        self.magnitude = CustomLab(0, text="Magnitude: ")
        self.components = CustomLab(1, text="Components: ")
        self.angle = CustomLab(2, text="Direction Angle: ")

        self.allStatsLabel.add_widget(self.magnitude)
        self.allStatsLabel.add_widget(self.components)
        self.allStatsLabel.add_widget(self.angle)
    
    def updateAllStats(self):
        if self.line_selected:
            x1, y1 = self.line_selected.node1.position
            x2, y2 = self.line_selected.node2.position
            self.magnitude.text = "Magnitude: " + str(round(math.sqrt(((x1 - x2) * (x1 - x2)) + ((y1 - y2) * (y1 - y2))), 2)) 
            self.components.text = "Components: " + str([round(x1 - x2, 1), round(y1 - y2, 1)])
            self.angle.text = "Direction Angle: " + str(round((self.line_selected.angle), 1)) + '°'

    def deleteNodeLine(self):
        if self.line_selected:
            self.all_nodes_line.remove(self.line_selected)
            self.all_Nodes.remove_widget(self.line_selected)
            self.resetVariable()

        for i, node in enumerate(self.all_nodes_line):
            node.name_Label.text = chr(65 + i)

    def addNodeLine(self):
        self.all_nodes_line.append(NodeLine())
        self.all_Nodes.add_widget(self.all_nodes_line[-1])
        self.all_nodes_line[-1].node1.setPosition()
        self.all_nodes_line[-1].node2.setPosition()
        if self.show_Coords:
            self.all_nodes_line[-1].node1.add_widget(self.all_nodes_line[-1].node1.label)
            self.all_nodes_line[-1].node2.add_widget(self.all_nodes_line[-1].node2.label)
        
        for i, node in enumerate(self.all_nodes_line):
            node.name_Label.text = chr(65 + i)
    
    def resetVariable(self):
        self.magnitude.text = "Magnitude: "
        self.components.text = "Components: "
        self.angle.text = "Direction Angle: "
        self.line_selected = None
        self.setGridValue()

    def displayAll(self):
        self.displayLabel()
        self.all_Nodes = Widget()

        self.displayGraph()
        self.displayLine()
        self.add_widget(self.all_Label)
        self.add_widget(self.all_Nodes)
        self.add_widget(self.allButton)
        self.add_widget(self.allStatsLabel)

    def setAllCanvas(self, *_):
        self.width_ = self.blockPadding*(self.cols*2+1)
        self.height_ = self.blockPadding*(self.rows*2+1)
        self.pos_ = (Window.width/2-self.width_/2, Window.height/2-self.height_/2)
        self.setAllNodes()
        self.updateCanvas()

    def updateCanvas(self, remove=False, allLine=False):    
        startX = max(round(((self.pos_[0]+self.cameraX + self.blockPadding/2) / self.blockPadding) * -1), 1)
        startY = max(round(((self.pos_[1]+self.cameraY + self.blockPadding/2) / self.blockPadding) * -1), 1)

        for c in range(startX-1 if allLine is False else 0, self.cols*2+1):
            if remove:
                self.all_Line_ver[c].points = [0, 0, 0, 0]
                self.all_horizontal[c].pos = (0, -Window.height)
                continue

            x = (self.cameraX + self.pos_[0] + self.blockPadding/2 + (c*self.blockPadding))
            if (x > -Window.width*0.3 and x < Window.width*1.3) or allLine:
                self.all_Line_ver[c].points = [
                    x, 0 if allLine is False else (self.cameraY + self.pos_[1]),
                    x, Window.height if allLine is False else ((self.cameraY + self.pos_[1]) + self.height_)]
                if c != self.cols:
                    self.all_horizontal[c].size = (self.blockPadding, self.blockPadding)
                    self.all_horizontal[c].pos = (self.cameraX + self.pos_[0] + self.blockPadding/2 + ((c-0.5)*self.blockPadding),
                         self.cameraY + self.pos_[1] + self.blockPadding/2 + ((self.rows-(0 if c+1 > self.cols else 1))*self.blockPadding))
            elif x > Window.width: break 
        for r in range(startY-1 if allLine is False else 0, self.rows*2+1):
            if remove: break

            y = self.cameraY + self.pos_[1] + self.blockPadding/2 + (r*self.blockPadding)
            if (y > -Window.height*0.3 and y < Window.height*1.3) or allLine:
                self.all_Line_hor[r].points= [
                    0 if allLine is False else (self.cameraX + self.pos_[0]), y,
                    Window.width if allLine is False else ((self.cameraX + self.pos_[0]) + self.width_), y]
                if r != self.rows:
                    self.all_vertical[r].size = (self.blockPadding, self.blockPadding)
                    self.all_vertical[r].pos = (self.cameraX + self.pos_[0] + self.blockPadding/2 + ((self.cols-(1 if r+1 > self.rows else 0))*self.blockPadding),
                       self.cameraY + self.pos_[1] + self.blockPadding/2 + ((r-0.5)*self.blockPadding))
            elif y > Window.height: break

    def removeAll(self):
        self.updateCanvas(True)

    def removeAllNodes(self):
        self.all_nodes_line.clear()
        self.all_Nodes.clear_widgets()
        self.resetVariable()

    def zoom_out(self):
        if self.blockPadding * 0.9 > self.minimum_size:
            self.blockPadding *= 0.9
            self.cameraX *= 0.9
            self.cameraY *= 0.9
        self.setAllCanvas()

    def zoom_in(self):
        if self.blockPadding * 1.1 < self.maximum_size:
            self.blockPadding *= 1.1
            self.cameraX *= 1.1
            self.cameraY *= 1.1
        self.setAllCanvas()

    def displayGraph(self):
        with self.canvas:
            Color(rgb=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_BG))
            self.mainBgRect = Rectangle(size=Window.size)

    def displayLabel(self):
        self.all_Label = Widget()
        for c in range(self.cols*2+1):
            if c != self.cols:
                self.all_horizontal.append(Label(
                        opacity=0.8,
                        text=f"{c-self.cols}", font_size=dp(15),
                        color=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_NUM_VERT),
                        bold=True, pos=(-Window.width, -Window.height))
                    )
                self.all_Label.add_widget(self.all_horizontal[-1])
            else: self.all_horizontal.append(Label())
        for r in range(self.rows*2+1):
            if r != self.rows:
                self.all_vertical.append(Label(
                        opacity=0.8,
                        text=f"{r-self.rows}", font_size=dp(15),
                        color=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_NUM_HOR),
                        bold=True, pos=(-Window.width, -Window.height))
                    )
                self.all_Label.add_widget(self.all_vertical[-1])
            else: self.all_vertical.append(Label())

    def setAllNodes(self):
        for node in self.all_nodes_line: node.update2Nodeposition()

    def displayLine(self):
        with self.canvas:
            Color(rgb=GetColor(App.get_running_app().CT.CurrentTheme.GRAPH_LINE))
            for c in range(self.cols*2+1):
                self.all_Line_ver.append(Line(width=dp(2) if c == self.cols else dp(0.5)))
            for r in range(self.rows*2+1):
                self.all_Line_hor.append(Line(width=dp(2) if r == self.rows else dp(0.5)))

    def on_touch_down(self, touch):
        touched = False
        for node in self.all_nodes_line:
            if node.node1.collide_point(*touch.pos):
                node.node1.on_touch_down(touch)
                touched = True
            if node.node2.collide_point(*touch.pos):
                node.node2.on_touch_down(touch)
                touched = True
        
        for butt in self.allButton.children:
            if butt.collide_point(*touch.pos):
                touched = True

        if self.grabbing is None and touched is False:
            self.grabbing = self
            self.oldCameraX = self.cameraX
            self.oldCameraY = self.cameraY
            self.grabX = touch.x
            self.grabY = touch.y
        return super().on_touch_down(touch)
  
    def on_touch_move(self, touch):
        if self.grabbing is self:
            self.cameraX = self.oldCameraX + (touch.x - self.grabX)
            self.cameraY = self.oldCameraY + (touch.y - self.grabY)
            self.setAllCanvas()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.grabbing is self:
            self.grabbing = None
            self.oldCameraX = self.cameraX
            self.oldCameraY = self.cameraY
        return super().on_touch_up(touch)

from kivy.config import Config
from kivy.app import App
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.properties import BoundedNumericProperty
from kivy.properties import ListProperty
from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock


class hitBang(Widget):
    width_shot = NumericProperty()
    height_shot = NumericProperty()
    file_pin = StringProperty()

    def __init__(self, **kwargs):
        super(hitBang, self).__init__(**kwargs)
        self.animation = Clock.create_trigger(self.animateHit, 0.25)
        self.cur_pos = (0.0,0.0)
        self.ani = 0
        
            
        self._shot = ScatterLayout(
            size=(self.width_shot, self.height_shot),
            do_rotate=False, 
            do_scale=False, 
            do_translation=False
            )

        _img_shot = Image(source=self.file_pin, size=(self.width_shot, 
            self.height_shot), allow_stretch=True)


        self._shot.add_widget(_img_shot)   
        self.add_widget(self._shot)
        self.bind(pos=self._update)
        self.bind(size=self._update)
        
    def _update(self, *args):
        self._shot.pos = self.pos
        self.cur_pos = self._shot.pos
        self.animation()

    def animateHit(self, dt):
        if self.ani == 1:
            self._shot.size = (self.width_shot/4, self.height_shot/4)
            self._shot.pos = (self.cur_pos[0] + self.width_shot/2.75, self.cur_pos[1] + self.height_shot/2.75)
        if self.ani == 2:
            self._shot.size = (self.width_shot/2, self.height_shot/2)
            self._shot.pos = (self.cur_pos[0] + self.width_shot/4, self.cur_pos[1] + self.height_shot/4)
        if self.ani == 3:
            self._shot.size = (self.width_shot, self.height_shot)
            self._shot.pos = (self.cur_pos[0], self.cur_pos[1])
        if self.ani == 4:
            self.ani = 0
        self.ani += 1
        self.animation()


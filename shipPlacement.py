from kivy.config import Config
from kivy.app import App
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.properties import ListProperty
from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.label import Label


class ship(Widget):
    unit = NumericProperty(1)
    width_ship = NumericProperty()
    height_ship = NumericProperty()
    file_ship = StringProperty()
    value = NumericProperty()


    def __init__(self, **kwargs):
        super(ship, self).__init__(**kwargs)
        

        self._ship = ScatterLayout(
            size=(self.width_ship, self.height_ship),
            do_rotate=False,
            do_scale=False,
            do_translation=False
            )

        self._img_ship = Image(source=self.file_ship, size=(self.width_ship, self.height_ship), allow_stretch=True)

        self.add_widget(self._ship)
        self._ship.add_widget(self._img_ship)
        self.bind(pos=self._update)
        self.bind(size=self._update)
        self.bind(value=self._aniSweep)
        
    def _update(self, *args):
        #self._radar.pos = self.pos
        self._ship.pos = (self.x, self.y)
        self._ship.center = self._ship.center
        self._ship.size = (self.width_ship, self.height_ship)


    def _aniSweep(self, *args):
        self._ship.rotation = -float(self.value)*self.unit